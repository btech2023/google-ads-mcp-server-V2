"""
Cache Manager Module

This module provides functionality for caching API responses and other data.
"""

import logging
import json
import hashlib
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

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
    
    def get(self, cache_key: str) -> Optional[Any]:
        """
        Get data from cache if it exists and is not expired.
        
        Args:
            cache_key: The cache key to lookup
            
        Returns:
            The cached data or None if not found or expired
        """
        # First check memory cache
        entry = self.memory_cache.get(cache_key)
        if entry is not None:
            if not entry.is_expired():
                logger.debug(f"Memory cache hit for key: {cache_key}")
                return entry.data
            # Remove expired entry
            del self.memory_cache[cache_key]
        
        # Then check database cache
        try:
            data_json = self.db_manager.get_kpi_data(cache_key)
            if data_json:
                logger.debug(f"Database cache hit for key: {cache_key}")
                data = json.loads(data_json)
                
                # Store in memory cache for faster access next time
                expiry = time.time() + self.default_ttl
                self.memory_cache[cache_key] = CacheEntry(data, expiry)
                
                return data
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
        
        logger.debug(f"Cache miss for key: {cache_key}")
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
        if ttl is None:
            ttl = self.default_ttl
            
        try:
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
            logger.error(f"Error storing in cache: {e}")
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
            logger.error(f"Error clearing cache: {e}")
            return False
