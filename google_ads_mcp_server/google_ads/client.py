"""
Google Ads Client Module

This module provides a client for interacting with the Google Ads API.
"""

import os
import logging
from typing import Optional, Dict, Any

# Import both client implementations
from .client_base import GoogleAdsClient
from .client_with_sqlite_cache import GoogleAdsServiceWithSQLiteCache
from db.factory import get_database_manager
from db.interface import DatabaseInterface

logger = logging.getLogger(__name__)

def get_google_ads_client(
    use_cache: bool = None, 
    cache_ttl: int = 3600,
    db_type: str = None,
    db_config: Optional[Dict[str, Any]] = None
) -> GoogleAdsClient:
    """
    Get a Google Ads client instance, optionally with caching.
    
    Args:
        use_cache: Whether to use caching. If None, determined by environment variable.
        cache_ttl: Cache TTL in seconds (default: 1 hour)
        db_type: Database type ('sqlite' or 'postgres'). If None, determined by environment variable.
        db_config: Optional database configuration dictionary
            For SQLite: {'db_path': '/path/to/db.sqlite', 'auto_clean_interval': 3600}
            For PostgreSQL: {'host': 'localhost', 'port': 5432, 'database': 'db_name', ...}
        
    Returns:
        A Google Ads client instance
    """
    # Determine whether to use caching from environment variable if not specified
    if use_cache is None:
        use_cache_env = os.environ.get("USE_CACHE", "true").lower()
        use_cache = use_cache_env in ("true", "1", "yes")
    
    # Get database type from environment if not specified
    if db_type is None:
        db_type = os.environ.get("DB_TYPE", "sqlite")
    
    # Create appropriate client type
    if use_cache:
        logger.info(f"Initializing Google Ads client with {db_type} caching")
        
        # Create a database manager instance
        db_manager = get_database_manager(db_type=db_type, db_config=db_config)
        
        # Create a cached client with the database manager
        return GoogleAdsServiceWithSQLiteCache(
            cache_enabled=True, 
            cache_ttl=cache_ttl,
            db_manager=db_manager
        )
    else:
        logger.info("Initializing Google Ads client without caching")
        return GoogleAdsClient()

# For backwards compatibility
GoogleAdsService = get_google_ads_client