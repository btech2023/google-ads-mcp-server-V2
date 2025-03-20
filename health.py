#!/usr/bin/env python
"""
Health check module for Google Ads MCP Server
"""

import logging
import os
import asyncio
from datetime import datetime

logger = logging.getLogger("health-check")

class HealthCheck:
    """Health check services for the Google Ads MCP Server."""
    
    def __init__(self):
        """Initialize the health check service."""
        self.app_start_time = datetime.now()
        self.status = "OK"
    
    async def get_health(self):
        """
        Get the health status of the server and its components.
        
        Returns:
            Dict containing health status information
        """
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
                "caching": os.environ.get("CACHE_ENABLED", "true").lower() == "true"
            }
        }
        
        # Check Google Ads API connectivity if needed
        # This could be expanded to actually test connectivity
        health_data["components"]["google_ads_api"] = "CONFIGURED" if os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN") else "NOT_CONFIGURED"
        
        return health_data
    
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