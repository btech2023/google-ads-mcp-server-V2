"""
API Call Tracking Utility

This module provides functions for tracking, logging, and analyzing Google Ads API calls
to optimize API usage and identify potential performance improvements.
"""

import json
import logging
import time
import os
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from functools import wraps
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)

class APICallTracker:
    """
    Tracks Google Ads API calls for analysis and optimization.
    
    This class provides methods to log API calls, record their parameters,
    execution time, and result status. It also provides tools to analyze
    call patterns and generate optimization recommendations.
    """
    
    def __init__(self, db_path: Optional[str] = None, enabled: bool = True):
        """
        Initialize the API call tracker.
        
        Args:
            db_path: Path to the SQLite database file for storing call logs.
                If None, uses a default path in the same directory.
            enabled: Whether tracking is enabled (default: True)
        """
        self.enabled = enabled
        if not enabled:
            return
            
        # Set up database path
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, 'api_call_logs.db')
            
        self.db_path = db_path
        self._init_db()
        logger.info(f"API call tracking enabled, logging to {db_path}")
        
    def _init_db(self):
        """Initialize the database schema if it doesn't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Create API call logs table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_call_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                method_name TEXT NOT NULL,
                customer_id TEXT,
                cache_status TEXT NOT NULL,
                execution_time_ms REAL NOT NULL,
                query_hash TEXT,
                query_size INTEGER,
                response_size INTEGER,
                success INTEGER NOT NULL,
                error_message TEXT,
                parameters TEXT
            )
            """)
            
            # Create indexes
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_call_logs_method ON api_call_logs(method_name)
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_call_logs_customer ON api_call_logs(customer_id)
            """)
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_call_logs_timestamp ON api_call_logs(timestamp)
            """)
            
            conn.commit()
            logger.debug("API call tracking database initialized")
        except sqlite3.Error as e:
            logger.error(f"Error initializing API call tracking database: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a connection to the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    
    @contextmanager
    def track_call(self, method_name: str, customer_id: Optional[str] = None, 
                  parameters: Optional[Dict[str, Any]] = None, 
                  query_hash: Optional[str] = None):
        """
        Context manager for tracking an API call.
        
        Usage:
            with api_tracker.track_call(method_name='get_campaigns', customer_id='1234567890'):
                result = api_client.get_campaigns(...)
                
        Args:
            method_name: Name of the API method being called
            customer_id: Optional Google Ads customer ID
            parameters: Optional dictionary of call parameters
            query_hash: Optional hash identifying the specific query
        """
        if not self.enabled:
            yield
            return
            
        start_time = time.time()
        error_message = None
        success = True
        cache_status = "UNKNOWN"
        response_size = 0
        
        try:
            # Set placeholder for cache status that will be updated by the caller
            self._current_cache_status = "MISS"  # Default to MISS unless set to HIT
            yield self
            
            # Get cache status
            cache_status = self._current_cache_status
            
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Store the log
            self.log_call(
                method_name=method_name,
                customer_id=customer_id,
                cache_status=cache_status,
                execution_time_ms=execution_time_ms,
                query_hash=query_hash,
                query_size=len(json.dumps(parameters)) if parameters else 0,
                response_size=response_size,
                success=success,
                error_message=error_message,
                parameters=parameters
            )
    
    def set_cache_status(self, status: str):
        """Set the cache status for the current API call being tracked."""
        if self.enabled:
            self._current_cache_status = status
            
    def set_response_size(self, size: int):
        """Set the response size for the current API call being tracked."""
        if self.enabled:
            self._current_response_size = size
    
    def log_call(self, method_name: str, customer_id: Optional[str] = None,
                cache_status: str = "MISS", execution_time_ms: float = 0,
                query_hash: Optional[str] = None, query_size: int = 0,
                response_size: int = 0, success: bool = True,
                error_message: Optional[str] = None,
                parameters: Optional[Dict[str, Any]] = None):
        """
        Log an API call to the database.
        
        Args:
            method_name: Name of the API method being called
            customer_id: Optional Google Ads customer ID
            cache_status: Cache status ("HIT", "MISS", "N/A", etc.)
            execution_time_ms: Execution time in milliseconds
            query_hash: Optional hash identifying the specific query
            query_size: Size of the query parameters in bytes
            response_size: Size of the response in bytes
            success: Whether the call was successful
            error_message: Error message if the call failed
            parameters: Optional dictionary of call parameters
        """
        if not self.enabled:
            return
            
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Convert parameters to JSON if provided
            params_json = json.dumps(parameters) if parameters else None
            
            # Insert log entry
            cursor.execute("""
            INSERT INTO api_call_logs (
                timestamp, method_name, customer_id, cache_status, 
                execution_time_ms, query_hash, query_size, response_size,
                success, error_message, parameters
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                method_name,
                customer_id,
                cache_status,
                execution_time_ms,
                query_hash,
                query_size,
                response_size,
                1 if success else 0,
                error_message,
                params_json
            ))
            
            conn.commit()
            logger.debug(f"Logged API call: {method_name} ({cache_status}) in {execution_time_ms:.2f}ms")
        except sqlite3.Error as e:
            logger.error(f"Error logging API call: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_recent_calls(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get API calls from the recent period.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of API call log entries
        """
        if not self.enabled:
            return []
            
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Calculate time threshold
            threshold = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            # Query recent calls
            cursor.execute("""
            SELECT * FROM api_call_logs 
            WHERE timestamp > ? 
            ORDER BY timestamp DESC
            """, (threshold,))
            
            rows = cursor.fetchall()
            result = []
            
            for row in rows:
                entry = dict(row)
                # Convert parameters from JSON if present
                if entry['parameters']:
                    try:
                        entry['parameters'] = json.loads(entry['parameters'])
                    except json.JSONDecodeError:
                        entry['parameters'] = {}
                result.append(entry)
                
            return result
            
        except sqlite3.Error as e:
            logger.error(f"Error retrieving recent API calls: {e}")
            return []
        finally:
            conn.close()
    
    def analyze_call_patterns(self, hours: int = 24) -> Dict[str, Any]:
        """
        Analyze API call patterns for the recent period.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dictionary with analysis results
        """
        if not self.enabled:
            return {"enabled": False}
            
        calls = self.get_recent_calls(hours)
        
        if not calls:
            return {
                "enabled": True,
                "calls_analyzed": 0,
                "message": "No API calls found in the specified period."
            }
            
        # Initialize analysis
        analysis = {
            "enabled": True,
            "calls_analyzed": len(calls),
            "period_hours": hours,
            "methods": {},
            "customers": {},
            "cache_hits": 0,
            "cache_misses": 0,
            "failures": 0,
            "total_execution_time_ms": 0,
            "avg_execution_time_ms": 0,
            "potential_optimizations": []
        }
        
        # Analyze method and customer patterns
        for call in calls:
            method = call['method_name']
            customer_id = call['customer_id'] or "unknown"
            
            # Method stats
            if method not in analysis["methods"]:
                analysis["methods"][method] = {
                    "count": 0,
                    "cache_hits": 0,
                    "cache_misses": 0,
                    "failures": 0,
                    "total_execution_time_ms": 0,
                    "avg_execution_time_ms": 0
                }
                
            analysis["methods"][method]["count"] += 1
            if call['cache_status'] == 'HIT':
                analysis["methods"][method]["cache_hits"] += 1
                analysis["cache_hits"] += 1
            elif call['cache_status'] == 'MISS':
                analysis["methods"][method]["cache_misses"] += 1
                analysis["cache_misses"] += 1
                
            if not call['success']:
                analysis["methods"][method]["failures"] += 1
                analysis["failures"] += 1
                
            analysis["methods"][method]["total_execution_time_ms"] += call['execution_time_ms']
            
            # Customer stats
            if customer_id not in analysis["customers"]:
                analysis["customers"][customer_id] = {
                    "count": 0,
                    "methods": set()
                }
                
            analysis["customers"][customer_id]["count"] += 1
            analysis["customers"][customer_id]["methods"].add(method)
            
            # Total stats
            analysis["total_execution_time_ms"] += call['execution_time_ms']
        
        # Calculate averages and finalize stats
        analysis["avg_execution_time_ms"] = analysis["total_execution_time_ms"] / len(calls)
        
        for method, stats in analysis["methods"].items():
            stats["avg_execution_time_ms"] = stats["total_execution_time_ms"] / stats["count"]
            # Convert method sets to lists for JSON serialization
            
        for customer_id, stats in analysis["customers"].items():
            stats["methods"] = list(stats["methods"])
            
        # Identify potential optimizations
        
        # 1. Methods with low cache hit rate
        for method, stats in analysis["methods"].items():
            if stats["count"] > 5:  # Only consider methods with sufficient call volume
                hit_rate = stats["cache_hits"] / stats["count"] if stats["count"] > 0 else 0
                if hit_rate < 0.3:  # Less than 30% cache hit rate
                    analysis["potential_optimizations"].append({
                        "type": "low_cache_hit_rate",
                        "method": method,
                        "hit_rate": hit_rate,
                        "recommendation": "Review caching strategy for this method. Consider increasing TTL or caching more aggressively."
                    })
        
        # 2. Repeated calls to the same method
        method_counts = {method: stats["count"] for method, stats in analysis["methods"].items()}
        high_frequency_methods = {method: count for method, count in method_counts.items() if count > 10}
        
        if high_frequency_methods:
            for method, count in sorted(high_frequency_methods.items(), key=lambda x: x[1], reverse=True)[:5]:
                analysis["potential_optimizations"].append({
                    "type": "high_frequency_method",
                    "method": method,
                    "count": count,
                    "recommendation": "Consider batching requests or consolidating multiple calls."
                })
        
        # 3. Slow methods
        slow_methods = {
            method: stats 
            for method, stats in analysis["methods"].items() 
            if stats["avg_execution_time_ms"] > 1000 and stats["count"] > 3  # Slower than 1 second and called at least 3 times
        }
        
        if slow_methods:
            for method, stats in sorted(slow_methods.items(), key=lambda x: x[1]["avg_execution_time_ms"], reverse=True)[:5]:
                analysis["potential_optimizations"].append({
                    "type": "slow_method",
                    "method": method,
                    "avg_execution_time_ms": stats["avg_execution_time_ms"],
                    "recommendation": "Review method implementation for optimization opportunities. Check if all requested fields are necessary."
                })
                
        return analysis
    
    def generate_optimization_report(self, hours: int = 24) -> str:
        """
        Generate a human-readable optimization report.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Markdown-formatted report
        """
        analysis = self.analyze_call_patterns(hours)
        
        if not analysis["enabled"]:
            return "API call tracking is disabled."
            
        if analysis["calls_analyzed"] == 0:
            return f"No API calls found in the last {hours} hours."
            
        # Build report
        report = [
            f"# Google Ads API Call Optimization Report",
            f"Period: Last {hours} hours",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"## Summary",
            f"",
            f"* Total calls analyzed: {analysis['calls_analyzed']}",
            f"* Cache hit rate: {(analysis['cache_hits'] / analysis['calls_analyzed'] * 100):.1f}%",
            f"* Average execution time: {analysis['avg_execution_time_ms']:.2f}ms",
            f"* Failed calls: {analysis['failures']} ({(analysis['failures'] / analysis['calls_analyzed'] * 100):.1f}%)",
            f"",
            f"## Method Usage",
            f"",
            f"| Method | Count | Cache Hit Rate | Avg Time (ms) |",
            f"|--------|-------|---------------|---------------|"
        ]
        
        # Sort methods by call count
        sorted_methods = sorted(
            analysis["methods"].items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        
        for method, stats in sorted_methods:
            hit_rate = (stats["cache_hits"] / stats["count"] * 100) if stats["count"] > 0 else 0
            report.append(
                f"| {method} | {stats['count']} | {hit_rate:.1f}% | {stats['avg_execution_time_ms']:.2f} |"
            )
            
        # Add optimization recommendations if any
        if analysis["potential_optimizations"]:
            report.extend([
                f"",
                f"## Optimization Recommendations",
                f""
            ])
            
            for i, opt in enumerate(analysis["potential_optimizations"], 1):
                report.extend([
                    f"### {i}. {opt['type']} - {opt['method']}",
                    f"",
                    f"{opt['recommendation']}",
                    f""
                ])
                
                if opt['type'] == "low_cache_hit_rate":
                    report.append(f"Current hit rate: {opt['hit_rate'] * 100:.1f}%")
                elif opt['type'] == "high_frequency_method":
                    report.append(f"Called {opt['count']} times in the period")
                elif opt['type'] == "slow_method":
                    report.append(f"Average execution time: {opt['avg_execution_time_ms']:.2f}ms")
                    
                report.append(f"")
        
        return "\n".join(report)
    
    def clear_logs(self, hours: Optional[int] = None):
        """
        Clear API call logs.
        
        Args:
            hours: If provided, only clears logs older than this many hours.
                  If None, clears all logs.
        """
        if not self.enabled:
            return
            
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if hours is not None:
                # Calculate time threshold
                threshold = (datetime.now() - timedelta(hours=hours)).isoformat()
                
                # Delete logs older than threshold
                cursor.execute("DELETE FROM api_call_logs WHERE timestamp < ?", (threshold,))
                deleted_count = cursor.rowcount
                logger.info(f"Cleared {deleted_count} API call logs older than {hours} hours")
            else:
                # Delete all logs
                cursor.execute("DELETE FROM api_call_logs")
                deleted_count = cursor.rowcount
                logger.info(f"Cleared all {deleted_count} API call logs")
                
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error clearing API call logs: {e}")
            conn.rollback()
        finally:
            conn.close()


# Function decorators for tracking
def track_api_call(tracker: APICallTracker):
    """
    Decorator for tracking API calls.
    
    Args:
        tracker: The APICallTracker instance to use
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapped(*args, **kwargs):
            # Determine method name
            method_name = func.__name__
            
            # Try to extract customer_id from arguments
            customer_id = None
            if 'customer_id' in kwargs:
                customer_id = kwargs['customer_id']
            elif len(args) > 0 and hasattr(args[0], 'client_customer_id'):
                # Assuming first arg is self with client_customer_id attribute
                customer_id = args[0].client_customer_id
                
            # Create parameters dict
            parameters = {}
            for i, arg in enumerate(args[1:], 1):  # Skip self
                parameters[f"arg{i}"] = str(arg)
            parameters.update({k: str(v) for k, v in kwargs.items()})
            
            # Generate query hash if possible
            query_hash = None
            if hasattr(args[0], '_generate_cache_key'):
                try:
                    query_hash = args[0]._generate_cache_key(method_name, *args[1:], **kwargs)
                except:
                    pass
            
            # Track the call
            with tracker.track_call(
                method_name=method_name,
                customer_id=customer_id,
                parameters=parameters,
                query_hash=query_hash
            ) as call_tracker:
                result = await func(*args, **kwargs)
                
                # Estimate response size
                try:
                    response_size = len(json.dumps(result)) if result else 0
                    call_tracker.set_response_size(response_size)
                except:
                    pass
                    
                return result
                
        return wrapped
    
    return decorator 