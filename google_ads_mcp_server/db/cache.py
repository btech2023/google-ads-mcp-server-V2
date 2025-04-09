"""
Cache Manager Module

This module provides functionality for caching API responses and other data.
"""

import json
import hashlib
import time
from typing import Any, Optional, Dict

# Import utility modules
from google_ads_mcp_server.utils.error_handler import (
    handle_exception,
    SEVERITY_WARNING,
    CATEGORY_DATABASE
)
from google_ads_mcp_server.utils.validation import (
    validate_non_empty_string,
    validate_non_negative_number
)
from google_ads_mcp_server.utils.logging import get_logger

# Get logger
logger = get_logger(__name__)

class CacheEntry:
    """Class representing a cached response."""
    
    def __init__(self, data: Any, expiry: float):
        """
        Initialize a cache entry.
        
        Args:
            data: The data to cache
            expiry: The timestamp when this cache entry expires
        """
        self.data = data
        self.expiry = expiry
    
    def is_expired(self) -> bool:
        """
        Check if the cache entry has expired.
        
        Returns:
            True if expired, False otherwise
        """
        return time.time() > self.expiry


class CacheManager:
    """Manager for handling caching operations."""
    
    def __init__(self, db_manager, default_ttl: int = 3600):
        """
        Initialize the cache manager.
        
        Args:
            db_manager: Database manager instance
            default_ttl: Default cache time-to-live in seconds (default: 1 hour)
        """
        # Validate inputs
        validation_errors = []
        validate_non_negative_number(default_ttl, "default_ttl", validation_errors)
        
        if validation_errors:
            error_message = f"Validation errors in CacheManager initialization: {'; '.join(validation_errors)}"
            logger.error(error_message)
            raise ValueError(error_message)
            
        self.db_manager = db_manager
        self.default_ttl = default_ttl
        self.memory_cache = {}  # In-memory cache dictionary
        logger.info(f"CacheManager initialized with TTL: {default_ttl} seconds")
        
    def generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate a unique cache key for the given parameters.
        
        Args:
            prefix: A prefix for the cache key
            *args: Positional arguments to include in the key
            **kwargs: Keyword arguments to include in the key
            
        Returns:
            A unique string key for caching
        """
        try:
            # Validate inputs
            validation_errors = []
            validate_non_empty_string(prefix, "prefix", validation_errors)
            
            if validation_errors:
                error_message = f"Validation errors in generate_cache_key: {'; '.join(validation_errors)}"
                logger.warning(error_message)
                raise ValueError(error_message)
                
            # Create a representation of the parameters
            params_repr = {
                "args": args,
                "kwargs": kwargs
            }
            
            # Convert to a stable JSON string and hash it
            json_str = json.dumps(params_repr, sort_keys=True)
            params_hash = hashlib.md5(json_str.encode()).hexdigest()
            
            # Create the full cache key with prefix
            return f"{prefix}:{params_hash}"
        except Exception as e:
            # Handle exception with proper context
            error_details = handle_exception(
                e,
                context={"prefix": prefix, "args_count": len(args), "kwargs_count": len(kwargs)},
                severity=SEVERITY_WARNING,
                category=CATEGORY_DATABASE
            )
            logger.error(f"Error generating cache key: {error_details.message}")
            raise ValueError(f"Failed to generate cache key: {str(e)}")
    
    def get(self, cache_key: str) -> Optional[Any]:
        """
        Get data from cache if it exists and is not expired.
        
        Args:
            cache_key: The cache key to lookup
            
        Returns:
            The cached data or None if not found or expired
        """
        try:
            # Validate inputs
            validation_errors = []
            validate_non_empty_string(cache_key, "cache_key", validation_errors)
            
            if validation_errors:
                error_message = f"Validation errors in cache get: {'; '.join(validation_errors)}"
                logger.warning(error_message)
                return None
                
            # First check memory cache
            entry = self.memory_cache.get(cache_key)
            if entry is not None:
                if not entry.is_expired():
                    logger.debug(f"Memory cache hit for key: {cache_key}")
                    return entry.data
                # Remove expired entry
                del self.memory_cache[cache_key]
            
            # Then check database cache
            data_json = self.db_manager.get_kpi_data(cache_key)
            if data_json:
                logger.debug(f"Database cache hit for key: {cache_key}")
                data = json.loads(data_json)
                
                # Store in memory cache for faster access next time
                expiry = time.time() + self.default_ttl
                self.memory_cache[cache_key] = CacheEntry(data, expiry)
                
                return data
            
            logger.debug(f"Cache miss for key: {cache_key}")
            return None
        except Exception as e:
            # Handle exception with proper context
            error_details = handle_exception(
                e,
                context={"cache_key": cache_key},
                severity=SEVERITY_WARNING,
                category=CATEGORY_DATABASE
            )
            logger.error(f"Error retrieving from cache: {error_details.message}")
            return None
    
    def set(self, cache_key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """
        Store data in the cache.
        
        Args:
            cache_key: The cache key to store under
            data: The data to cache
            ttl: Optional time-to-live in seconds (defaults to self.default_ttl)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate inputs
            validation_errors = []
            validate_non_empty_string(cache_key, "cache_key", validation_errors)
            if ttl is not None:
                validate_non_negative_number(ttl, "ttl", validation_errors)
                
            if validation_errors:
                error_message = f"Validation errors in cache set: {'; '.join(validation_errors)}"
                logger.warning(error_message)
                return False
                
            if ttl is None:
                ttl = self.default_ttl
                
            # Store in memory cache
            expiry = time.time() + ttl
            self.memory_cache[cache_key] = CacheEntry(data, expiry)
            
            # Extract components for database storage
            parts = cache_key.split(':')
            if len(parts) >= 2:
                prefix = parts[0]
                
                # Store in database cache
                data_json = json.dumps(data)
                account_id = data.get('account_id', '0') if isinstance(data, dict) else '0'
                start_date = data.get('start_date', '2023-01-01') if isinstance(data, dict) else '2023-01-01'
                end_date = data.get('end_date', '2023-12-31') if isinstance(data, dict) else '2023-12-31'
                
                segmentation_json = json.dumps({
                    "prefix": prefix,
                    "ttl": ttl
                })
                
                self.db_manager.store_kpi_data(
                    cache_key, 
                    account_id, 
                    start_date, 
                    end_date, 
                    segmentation_json, 
                    data_json
                )
            
            logger.debug(f"Data cached with key: {cache_key}, TTL: {ttl}s")
            return True
        except Exception as e:
            # Handle exception with proper context
            error_details = handle_exception(
                e,
                context={"cache_key": cache_key, "ttl": ttl},
                severity=SEVERITY_WARNING,
                category=CATEGORY_DATABASE
            )
            logger.error(f"Error storing in cache: {error_details.message}")
            return False
    
    def clear(self, prefix: Optional[str] = None) -> bool:
        """
        Clear cache entries.
        
        Args:
            prefix: Optional prefix to clear only entries with that prefix
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate inputs if prefix is provided
            if prefix is not None:
                validation_errors = []
                validate_non_empty_string(prefix, "prefix", validation_errors)
                
                if validation_errors:
                    error_message = f"Validation errors in cache clear: {'; '.join(validation_errors)}"
                    logger.warning(error_message)
                    return False
            
            if prefix:
                # Clear memory cache entries with the prefix
                keys_to_remove = [k for k in self.memory_cache.keys() if k.startswith(f"{prefix}:")]
                for key in keys_to_remove:
                    del self.memory_cache[key]
                logger.info(f"Cleared {len(keys_to_remove)} memory cache entries with prefix '{prefix}'")
            else:
                # Clear all memory cache
                self.memory_cache.clear()
                
                # Clear database cache
                self.db_manager.clear_cache()
                logger.info("All cache entries cleared")
            
            return True
        except Exception as e:
            # Handle exception with proper context
            error_details = handle_exception(
                e,
                context={"prefix": prefix},
                severity=SEVERITY_WARNING,
                category=CATEGORY_DATABASE
            )
            logger.error(f"Error clearing cache: {error_details.message}")
            return False
