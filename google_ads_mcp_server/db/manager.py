"""
Database Manager Module

This module provides the DatabaseManager class which handles all database operations,
including cache management for the Google Ads MCP Server.
"""

import os
import sqlite3
import json
import hashlib
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union

from .schema import (
    ALL_TABLES,
    ALL_INDEXES,
    CLEAN_EXPIRED_CACHE,
    GET_CACHE_STATS,
    CACHE_TABLES
)

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages database operations for the Google Ads MCP Server.
    
    This class handles database initialization, caching operations,
    and other persistent storage needs.
    """
    
    def __init__(self, db_path: str = None, auto_clean_interval: int = 3600):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses a default path.
            auto_clean_interval: Interval in seconds between automatic cache cleanups.
                                Set to 0 to disable auto-cleaning.
        """
        if db_path is None:
            # Default to a database file in the same directory as this module
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, 'google_ads_mcp.db')
            
        self.db_path = db_path
        self.auto_clean_interval = auto_clean_interval
        self.last_clean_time = 0
        
        # Initialize database
        self._init_db()
        
    def _init_db(self):
        """Initialize the database schema if it doesn't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Create tables
            for create_table_sql in ALL_TABLES:
                cursor.execute(create_table_sql)
                
            # Create indexes
            for create_index_sql in ALL_INDEXES:
                cursor.execute(create_index_sql)
                
            conn.commit()
            logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
            
    def _get_connection(self) -> sqlite3.Connection:
        """Get a connection to the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
        
    def _maybe_clean_cache(self):
        """
        Clean expired cache entries if the auto-clean interval has elapsed.
        """
        if self.auto_clean_interval <= 0:
            return
            
        current_time = time.time()
        if current_time - self.last_clean_time >= self.auto_clean_interval:
            self.clean_cache()
            self.last_clean_time = current_time
            
    def _generate_cache_key(self, entity_type: str, customer_id: str, query_params: Dict[str, Any]) -> str:
        """
        Generate a unique cache key based on entity type, customer ID, and query parameters.
        
        Args:
            entity_type: Type of entity being cached (e.g., 'api', 'campaign', 'keyword')
            customer_id: Google Ads customer ID
            query_params: Dictionary of query parameters
            
        Returns:
            A unique hash string to use as cache key
        """
        # Convert query_params to a consistent string representation
        params_str = json.dumps(query_params, sort_keys=True)
        
        # Generate a hash of the combined parameters
        key_components = f"{entity_type}:{customer_id}:{params_str}"
        cache_key = hashlib.md5(key_components.encode()).hexdigest()
        
        return cache_key
        
    def store_api_response(
        self,
        customer_id: str,
        query_type: str,
        query_params: Dict[str, Any],
        response_data: Union[Dict[str, Any], List[Dict[str, Any]]],
        ttl_seconds: int = 900,  # 15 minutes default
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store an API response in the cache.
        
        Args:
            customer_id: Google Ads customer ID
            query_type: Type of query (e.g., 'get_campaigns', 'get_keywords')
            query_params: Dictionary of query parameters
            response_data: The API response data to cache
            ttl_seconds: Time-to-live in seconds for this cache entry
            metadata: Optional metadata to store with the cache entry
            
        Returns:
            The cache key used to store the entry
        """
        self._maybe_clean_cache()
        
        # Generate cache key
        query_hash = hashlib.md5(json.dumps(query_params, sort_keys=True).encode()).hexdigest()
        cache_key = self._generate_cache_key('api', customer_id, query_params)
        
        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds + 2)  # Add 2 seconds grace period
        
        # Serialize data to JSON
        response_json = json.dumps(response_data)
        metadata_json = json.dumps(metadata) if metadata else None
        
        # Debug information
        logger.debug(f"Storing API response with key: {cache_key}")
        logger.debug(f"Customer ID: {customer_id}, Query type: {query_type}")
        logger.debug(f"TTL: {ttl_seconds} seconds, Expires at: {expires_at.isoformat()}")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Insert or replace existing cache entry
            query = """
            INSERT OR REPLACE INTO api_cache
            (cache_key, customer_id, query_type, query_hash, response_data, expires_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            values = (
                cache_key,
                customer_id,
                query_type,
                query_hash,
                response_json,
                expires_at.isoformat(),
                metadata_json
            )
            
            cursor.execute(query, values)
            
            # Verify that the data was stored
            cursor.execute("SELECT COUNT(*) as count FROM api_cache WHERE cache_key = ?", (cache_key,))
            count_row = cursor.fetchone()
            if count_row and count_row['count'] > 0:
                logger.debug(f"Successfully stored data for key {cache_key}")
            else:
                logger.debug(f"Failed to store data for key {cache_key}")
            
            conn.commit()
            
            return cache_key
            
        except sqlite3.Error as e:
            logger.error(f"Error storing API response in cache: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
            
    def get_api_response(
        self,
        customer_id: str,
        query_type: str,
        query_params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve an API response from the cache if available and not expired.
        
        Args:
            customer_id: Google Ads customer ID
            query_type: Type of query (e.g., 'get_campaigns', 'get_keywords')
            query_params: Dictionary of query parameters
            
        Returns:
            The cached response data, or None if not found or expired
        """
        self._maybe_clean_cache()
        
        # Generate cache key
        cache_key = self._generate_cache_key('api', customer_id, query_params)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Query for cache entry with properly formatted datetime comparison
            query = """
            SELECT response_data, metadata
            FROM api_cache
            WHERE cache_key = ? AND expires_at > datetime('now', 'utc')
            """
            
            logger.debug(f"Executing query for cache key: {cache_key}")
            logger.debug(f"Query: {query}")
            
            cursor.execute(query, (cache_key,))
            
            row = cursor.fetchone()
            if row is None:
                # For debugging, check if the key exists at all, regardless of expiration
                cursor.execute("SELECT expires_at FROM api_cache WHERE cache_key = ?", (cache_key,))
                any_row = cursor.fetchone()
                if any_row:
                    logger.debug(f"Entry found but expired. Expiry was: {any_row['expires_at']}")
                    
                # Also check if there are any rows in the table
                cursor.execute("SELECT COUNT(*) as count FROM api_cache")
                count_row = cursor.fetchone()
                logger.debug(f"Total entries in api_cache: {count_row['count']}")
                
                return None
                
            # Parse response data from JSON
            try:
                response_data = json.loads(row['response_data'])
                metadata = json.loads(row['metadata']) if row['metadata'] else None
                
                logger.debug(f"Cache hit for key {cache_key}")
                
                # If metadata is needed, return both
                if metadata:
                    return {
                        'data': response_data,
                        'metadata': metadata
                    }
                    
                return response_data
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                logger.debug(f"Response data: {row['response_data'][:100]}...")  # Show first 100 chars
                return None
            
        except sqlite3.Error as e:
            logger.error(f"Error retrieving API response from cache: {e}")
            return None
        finally:
            conn.close()
            
    def store_entity_data(
        self,
        entity_type: str,
        customer_id: str,
        entity_data: Union[Dict[str, Any], List[Dict[str, Any]]],
        ttl_seconds: int = 900,  # 15 minutes default
        **params
    ) -> str:
        """
        Store entity data in the appropriate cache table.
        
        Args:
            entity_type: Type of entity ('campaign', 'keyword', 'search_term', 'budget')
            customer_id: Google Ads customer ID
            entity_data: The entity data to cache
            ttl_seconds: Time-to-live in seconds for this cache entry
            **params: Additional parameters for the entity (e.g., campaign_id, start_date)
            
        Returns:
            The cache key used to store the entry
        """
        self._maybe_clean_cache()
        
        if entity_type not in CACHE_TABLES:
            raise ValueError(f"Unknown entity type: {entity_type}")
            
        table_name = CACHE_TABLES[entity_type]
        
        # Generate cache key using all parameters
        cache_key = self._generate_cache_key(entity_type, customer_id, params)
        
        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds + 2)  # Add 2 seconds grace period
        
        # Serialize data to JSON
        entity_data_json = json.dumps(entity_data)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Prepare column names and placeholders for dynamic SQL
            columns = ['cache_key', 'customer_id', f'{entity_type}_data', 'expires_at']
            values = [cache_key, customer_id, entity_data_json, expires_at.isoformat()]
            
            # Add additional parameters
            for key, value in params.items():
                if value is not None:
                    columns.append(key)
                    values.append(value)
                    
            # Construct SQL query
            placeholders = ', '.join(['?'] * len(values))
            columns_str = ', '.join(columns)
            
            query = f"""
            INSERT OR REPLACE INTO {table_name}
            ({columns_str})
            VALUES ({placeholders})
            """
            
            cursor.execute(query, values)
            conn.commit()
            
            logger.debug(f"Stored {entity_type} data in cache with key {cache_key}")
            return cache_key
            
        except sqlite3.Error as e:
            logger.error(f"Error storing {entity_type} data in cache: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
            
    def get_entity_data(
        self,
        entity_type: str,
        customer_id: str,
        **params
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve entity data from the appropriate cache table if available and not expired.
        
        Args:
            entity_type: Type of entity ('campaign', 'keyword', 'search_term', 'budget')
            customer_id: Google Ads customer ID
            **params: Additional parameters for the entity (e.g., campaign_id, start_date)
            
        Returns:
            The cached entity data, or None if not found or expired
        """
        self._maybe_clean_cache()
        
        if entity_type not in CACHE_TABLES:
            raise ValueError(f"Unknown entity type: {entity_type}")
            
        table_name = CACHE_TABLES[entity_type]
        
        # Generate cache key using all parameters
        cache_key = self._generate_cache_key(entity_type, customer_id, params)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Query for cache entry with properly formatted datetime comparison
            cursor.execute(
                f"""
                SELECT {entity_type}_data
                FROM {table_name}
                WHERE cache_key = ? AND expires_at > datetime('now', 'utc')
                """,
                (cache_key,)
            )
            
            row = cursor.fetchone()
            if row is None:
                logger.debug(f"Cache miss for {entity_type} with key {cache_key}")
                
                # For debugging, check if the key exists at all
                cursor.execute(f"SELECT expires_at FROM {table_name} WHERE cache_key = ?", (cache_key,))
                any_row = cursor.fetchone()
                if any_row:
                    logger.debug(f"Entry found but expired. Expiry was: {any_row[0]}")
                
                return None
                
            # Parse entity data from JSON
            try:
                entity_data = json.loads(row[f'{entity_type}_data'])
                logger.debug(f"Cache hit for {entity_type} with key {cache_key}")
                return entity_data
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return None
            
        except sqlite3.Error as e:
            logger.error(f"Error retrieving {entity_type} data from cache: {e}")
            return None
        finally:
            conn.close()
            
    def store_account_kpi_data(
        self,
        account_id: str,
        start_date: str,
        end_date: str,
        kpi_data: Dict[str, Any],
        segmentation: Optional[Dict[str, Any]] = None,
        ttl_seconds: int = 900  # 15 minutes default
    ) -> str:
        """
        Store account KPI data in the cache.
        
        Args:
            account_id: Google Ads account ID
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            kpi_data: The KPI data to cache
            segmentation: Optional segmentation parameters
            ttl_seconds: Time-to-live in seconds for this cache entry
            
        Returns:
            The cache key used to store the entry
        """
        self._maybe_clean_cache()
        
        # Generate cache key
        params = {
            'start_date': start_date,
            'end_date': end_date,
            'segmentation': segmentation
        }
        cache_key = self._generate_cache_key('account_kpi', account_id, params)
        
        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds + 2)  # Add 2 seconds grace period
        
        # Serialize data to JSON
        kpi_data_json = json.dumps(kpi_data)
        segmentation_json = json.dumps(segmentation) if segmentation else None
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Insert or replace existing cache entry
            cursor.execute(
                """
                INSERT OR REPLACE INTO account_kpi_cache
                (cache_key, account_id, start_date, end_date, segmentation, kpi_data, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cache_key,
                    account_id,
                    start_date,
                    end_date,
                    segmentation_json,
                    kpi_data_json,
                    expires_at.isoformat()
                )
            )
            
            conn.commit()
            logger.debug(f"Stored account KPI data in cache with key {cache_key}")
            return cache_key
            
        except sqlite3.Error as e:
            logger.error(f"Error storing account KPI data in cache: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
            
    def get_account_kpi_data(
        self,
        account_id: str,
        start_date: str,
        end_date: str,
        segmentation: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve account KPI data from the cache if available and not expired.
        
        Args:
            account_id: Google Ads account ID
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            segmentation: Optional segmentation parameters
            
        Returns:
            The cached KPI data, or None if not found or expired
        """
        self._maybe_clean_cache()
        
        # Generate cache key
        params = {
            'start_date': start_date,
            'end_date': end_date,
            'segmentation': segmentation
        }
        cache_key = self._generate_cache_key('account_kpi', account_id, params)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Query for cache entry with properly formatted datetime comparison
            cursor.execute(
                """
                SELECT kpi_data
                FROM account_kpi_cache
                WHERE cache_key = ? AND expires_at > datetime('now', 'utc')
                """,
                (cache_key,)
            )
            
            row = cursor.fetchone()
            if row is None:
                # For debugging, check if the key exists at all
                cursor.execute("SELECT expires_at FROM account_kpi_cache WHERE cache_key = ?", (cache_key,))
                any_row = cursor.fetchone()
                if any_row:
                    logger.debug(f"Entry found but expired. Expiry was: {any_row[0]}")
                else:
                    logger.debug(f"No entry found for key: {cache_key}")
                    
                return None
                
            # Parse KPI data from JSON
            try:
                kpi_data = json.loads(row['kpi_data'])
                logger.debug(f"Cache hit for key {cache_key}")
                return kpi_data
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return None
            
        except sqlite3.Error as e:
            logger.error(f"Error retrieving account KPI data from cache: {e}")
            return None
        finally:
            conn.close()
            
    def clean_cache(self):
        """Remove all expired cache entries from all cache tables."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Clean each cache table
            for table in CACHE_TABLES.values():
                cursor.execute(CLEAN_EXPIRED_CACHE.format(table=table))
                
            conn.commit()
            logger.info("Cleaned expired cache entries")
        except sqlite3.Error as e:
            logger.error(f"Error cleaning cache: {e}")
            conn.rollback()
        finally:
            conn.close()
            
    def clear_cache(self, entity_type: Optional[str] = None, customer_id: Optional[str] = None):
        """
        Clear cache entries, optionally filtered by entity type and/or customer ID.
        
        Args:
            entity_type: Optional entity type to clear ('api', 'campaign', etc.)
            customer_id: Optional customer ID to clear
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if entity_type and entity_type not in CACHE_TABLES:
                raise ValueError(f"Unknown entity type: {entity_type}")
                
            # Determine which tables to clear
            tables_to_clear = [CACHE_TABLES[entity_type]] if entity_type else CACHE_TABLES.values()
            
            # Clear each table
            for table in tables_to_clear:
                if customer_id:
                    cursor.execute(f"DELETE FROM {table} WHERE customer_id = ?", (customer_id,))
                else:
                    cursor.execute(f"DELETE FROM {table}")
                    
            conn.commit()
            
            if entity_type and customer_id:
                logger.info(f"Cleared {entity_type} cache for customer {customer_id}")
            elif entity_type:
                logger.info(f"Cleared all {entity_type} cache entries")
            elif customer_id:
                logger.info(f"Cleared all cache entries for customer {customer_id}")
            else:
                logger.info("Cleared all cache entries")
                
        except sqlite3.Error as e:
            logger.error(f"Error clearing cache: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
            
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with counts of entries in each cache table
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(GET_CACHE_STATS)
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            else:
                return {f"{table}_count": 0 for table in CACHE_TABLES.keys()}
                
        except sqlite3.Error as e:
            logger.error(f"Error getting cache statistics: {e}")
            return {f"{table}_count": -1 for table in CACHE_TABLES.keys()}
        finally:
            conn.close()
