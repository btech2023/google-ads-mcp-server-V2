#!/usr/bin/env python
"""
Health check module for Google Ads MCP Server
"""

import logging
import os
import asyncio
from datetime import datetime
import time

try:
    # Import monitoring if available (will be added in a later step)
    from monitoring import update_health_status
    MONITORING_ENABLED = True
except ImportError:
    MONITORING_ENABLED = False

logger = logging.getLogger("health-check")

class HealthCheck:
    """Health check services for the Google Ads MCP Server."""
    
    def __init__(self):
        """Initialize the health check service."""
        self.app_start_time = datetime.now()
        self.status = "OK"
        self.last_check_time = time.time()
        self.check_interval_seconds = 60  # Check health metrics every 60 seconds
        self.health_metrics = {}  # Store historical health metrics
    
    async def get_health(self):
        """
        Get the health status of the server and its components.
        
        Returns:
            Dict containing health status information
        """
        current_time = time.time()
        
        # Only recompute metrics if check interval has passed
        if current_time - self.last_check_time > self.check_interval_seconds:
            await self._update_health_metrics()
            self.last_check_time = current_time
        
        uptime_seconds = (datetime.now() - self.app_start_time).total_seconds()
        
        health_data = {
            "status": self.status,
            "version": os.environ.get("APP_VERSION", "1.0.0"),
            "environment": os.environ.get("APP_ENV", "dev"),
            "uptime_seconds": uptime_seconds,
            "uptime_formatted": self._format_uptime(uptime_seconds),
            "timestamp": datetime.now().isoformat(),
            "components": {
                "server": "UP",
                "caching": os.environ.get("CACHE_ENABLED", "true").lower() == "true",
            }
        }
        
        # Check Google Ads API connectivity if needed
        # This could be expanded to actually test connectivity
        ads_api_status = "CONFIGURED" if os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN") else "NOT_CONFIGURED"
        health_data["components"]["google_ads_api"] = ads_api_status
        
        # Add metrics if available
        if self.health_metrics:
            health_data["metrics"] = self.health_metrics
        
        # Update monitoring metrics if enabled
        if MONITORING_ENABLED:
            update_health_status(health_data["status"] == "OK")
        
        return health_data
    
    async def _update_health_metrics(self):
        """
        Update health metrics by performing additional checks.
        This is called periodically to avoid expensive checks on every request.
        """
        # Start with empty metrics
        metrics = {}
        
        # Memory usage
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            metrics["memory"] = {
                "rss_bytes": memory_info.rss,
                "rss_mb": memory_info.rss / (1024 * 1024),
                "vms_bytes": memory_info.vms,
                "vms_mb": memory_info.vms / (1024 * 1024)
            }
        except (ImportError, Exception) as e:
            logger.warning(f"Unable to collect memory metrics: {str(e)}")
        
        # API response time check (simulated)
        # In a production environment, you might want to actually test API response time
        metrics["api_response_time_ms"] = 50  # Example placeholder value
        
        # Update stored metrics
        self.health_metrics = metrics
    
    def _format_uptime(self, seconds):
        """Format uptime in seconds to a human-readable string."""
        days, remainder = divmod(int(seconds), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or hours > 0 or days > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        
        return " ".join(parts)

# Singleton instance
health_check = HealthCheck() 