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
from ..db.factory import get_database_manager
from ..db.interface import DatabaseInterface

# Import utilities
from ..utils.logging import get_logger
from ..utils.validation import validate_positive_integer, validate_enum
from ..utils.error_handler import handle_exception, CATEGORY_CONFIG, SEVERITY_ERROR

logger = get_logger(__name__)

VALID_DB_TYPES = ["sqlite", "postgres"] # Define valid DB types

def get_google_ads_client(
    use_cache: bool = None, 
    cache_ttl: int = 3600,
    db_type: str = None,
    db_config: Optional[Dict[str, Any]] = None
) -> GoogleAdsClient:
    """
    Get a Google Ads client instance, optionally with caching.
    
    Raises:
        ValueError: If input parameters are invalid.
        RuntimeError: If client initialization fails.
        
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
    # Define base context for error handling
    context = {
        "use_cache": use_cache, 
        "cache_ttl": cache_ttl, 
        "db_type": db_type, 
        "method": "get_google_ads_client"
    }

    try:
        # --- Input Validation ---
        if not validate_positive_integer(cache_ttl):
             raise ValueError("cache_ttl must be a positive integer")
        context["cache_ttl"] = cache_ttl # Update context with validated/default value
        
        # Determine DB type, validate if provided
        if db_type is None:
            db_type_to_use = os.environ.get("DB_TYPE", "sqlite").lower()
        else:
            db_type_to_use = db_type.lower()
            if not validate_enum(db_type_to_use, VALID_DB_TYPES):
                 raise ValueError(f"Invalid db_type: {db_type}. Must be one of {VALID_DB_TYPES}")
        context["db_type"] = db_type_to_use # Update context

        # Determine whether to use caching
        if use_cache is None:
            use_cache_env = os.environ.get("USE_CACHE", "true").lower()
            use_cache_final = use_cache_env in ("true", "1", "yes")
        else:
            use_cache_final = use_cache
        context["use_cache"] = use_cache_final # Update context
        
        # --- Client Instantiation ---
        if use_cache_final:
            logger.info(f"Initializing Google Ads client with {db_type_to_use} caching (TTL: {cache_ttl}s)")
            
            # Create a database manager instance (can raise exceptions)
            db_manager = get_database_manager(db_type=db_type_to_use, db_config=db_config)
            
            # Create a cached client with the database manager (can raise exceptions)
            return GoogleAdsServiceWithSQLiteCache(
                cache_enabled=True, 
                cache_ttl=cache_ttl,
                db_manager=db_manager
            )
        else:
            logger.info("Initializing Google Ads client without caching")
            # Base client instantiation (can raise exceptions)
            return GoogleAdsClient()

    except ValueError as ve:
        # Handle known validation errors
        error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_CONFIG)
        logger.warning(f"Invalid configuration for Google Ads client: {error_details.message}")
        raise ve # Re-raise validation error
    except Exception as e:
        # Handle unexpected initialization errors (DB connection, client init, etc.)
        error_details = handle_exception(e, context=context, category=CATEGORY_CONFIG) # Default severity ERROR
        logger.error(f"Failed to initialize Google Ads client: {error_details.message}")
        raise RuntimeError(f"Google Ads client initialization failed: {error_details.message}") from e

# For backwards compatibility
GoogleAdsService = get_google_ads_client