"""
Database Interface Module

This module defines the abstract interface for database operations in the Google Ads MCP Server.
It provides a common interface that can be implemented by different database backends,
such as SQLite (currently) and PostgreSQL (future).
"""

import abc
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime


class DatabaseInterface(abc.ABC):
    """
    Abstract interface for database operations.
    
    This interface defines the contract that all database implementations must fulfill,
    ensuring that different backends (SQLite, PostgreSQL) can be used interchangeably.
    """
    
    @abc.abstractmethod
    def initialize(self) -> None:
        """
        Initialize the database, creating tables and indexes if they don't exist.
        
        This method should be idempotent and safe to call multiple times.
        """
        pass
    
    @abc.abstractmethod
    def close(self) -> None:
        """
        Close any open database connections.
        
        This method should be called when shutting down the application to ensure
        proper resource cleanup.
        """
        pass
    
    @abc.abstractmethod
    def execute_transaction(self, sql_statements: List[Tuple[str, List[Any]]]) -> None:
        """
        Execute multiple SQL statements as a single transaction.
        
        Args:
            sql_statements: List of tuples containing (sql_query, parameters)
        
        Raises:
            DatabaseError: If the transaction fails
        """
        pass
    
    # Cache operations
    
    @abc.abstractmethod
    def store_api_response(
        self,
        customer_id: str,
        query_type: str,
        query_params: Dict[str, Any],
        response_data: Union[Dict[str, Any], List[Dict[str, Any]]],
        ttl_seconds: int = 900,
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
        
        Raises:
            DatabaseError: If storing fails
        """
        pass
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
    def store_entity_data(
        self,
        entity_type: str,
        customer_id: str,
        entity_data: Union[Dict[str, Any], List[Dict[str, Any]]],
        ttl_seconds: int = 900,
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
        
        Raises:
            DatabaseError: If storing fails
            ValueError: If entity_type is unknown
        """
        pass
    
    @abc.abstractmethod
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
        
        Raises:
            ValueError: If entity_type is unknown
        """
        pass
    
    @abc.abstractmethod
    def store_account_kpi_data(
        self,
        account_id: str,
        start_date: str,
        end_date: str,
        kpi_data: Dict[str, Any],
        segmentation: Optional[Dict[str, Any]] = None,
        ttl_seconds: int = 900
    ) -> str:
        """
        Store account KPI data in the cache.
        
        Args:
            account_id: Google Ads account ID
            start_date: Start date for the data (YYYY-MM-DD)
            end_date: End date for the data (YYYY-MM-DD)
            kpi_data: The KPI data to cache
            segmentation: Optional segmentation parameters
            ttl_seconds: Time-to-live in seconds for this cache entry
            
        Returns:
            The cache key used to store the entry
        
        Raises:
            DatabaseError: If storing fails
        """
        pass
    
    @abc.abstractmethod
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
            start_date: Start date for the data (YYYY-MM-DD)
            end_date: End date for the data (YYYY-MM-DD)
            segmentation: Optional segmentation parameters
            
        Returns:
            The cached KPI data, or None if not found or expired
        """
        pass
    
    @abc.abstractmethod
    def clean_cache(self) -> None:
        """
        Clean expired cache entries from all cache tables.
        
        This method should be called periodically to remove expired entries.
        """
        pass
    
    @abc.abstractmethod
    def clear_cache(self, entity_type: Optional[str] = None, customer_id: Optional[str] = None) -> None:
        """
        Clear cache entries, optionally filtered by entity type and/or customer ID.
        
        Args:
            entity_type: Optional entity type to clear ('api', 'campaign', etc.)
            customer_id: Optional customer ID to clear cache for
        """
        pass
    
    @abc.abstractmethod
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with cache table names as keys and item counts as values
        """
        pass
    
    # User data operations - For multi-user support
    
    @abc.abstractmethod
    def store_user_data(
        self,
        user_id: str,
        user_data: Dict[str, Any]
    ) -> None:
        """
        Store user data in the database.
        
        Args:
            user_id: Unique identifier for the user
            user_data: User data to store
        
        Raises:
            DatabaseError: If storing fails
        """
        pass
    
    @abc.abstractmethod
    def get_user_data(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve user data from the database.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            The user data, or None if not found
        """
        pass
    
    @abc.abstractmethod
    def store_user_account_access(
        self,
        user_id: str,
        customer_id: str,
        access_level: str
    ) -> None:
        """
        Grant a user access to a specific customer account.
        
        Args:
            user_id: Unique identifier for the user
            customer_id: Google Ads customer ID
            access_level: Access level (e.g., 'read', 'write', 'admin')
        
        Raises:
            DatabaseError: If storing fails
        """
        pass
    
    @abc.abstractmethod
    def get_user_accounts(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all accounts a user has access to.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            List of dictionaries with customer_id and access_level
        """
        pass
    
    @abc.abstractmethod
    def check_user_account_access(
        self,
        user_id: str,
        customer_id: str,
        required_access_level: Optional[str] = None
    ) -> bool:
        """
        Check if a user has access to a specific customer account.
        
        Args:
            user_id: Unique identifier for the user
            customer_id: Google Ads customer ID
            required_access_level: Optional access level to check for
            
        Returns:
            True if the user has access, False otherwise
        """
        pass
    
    # Configuration operations
    
    @abc.abstractmethod
    def store_config(
        self,
        config_key: str,
        config_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> None:
        """
        Store configuration data in the database.
        
        Args:
            config_key: Unique identifier for the configuration
            config_data: Configuration data to store
            user_id: Optional user ID for user-specific configurations
        
        Raises:
            DatabaseError: If storing fails
        """
        pass
    
    @abc.abstractmethod
    def get_config(
        self,
        config_key: str,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve configuration data from the database.
        
        Args:
            config_key: Unique identifier for the configuration
            user_id: Optional user ID for user-specific configurations
            
        Returns:
            The configuration data, or None if not found
        """
        pass

    # --- User/Token Methods (Phase 3) ---

    @abc.abstractmethod
    async def get_token_data_by_hash(self, token_hash: str) -> Optional[Dict]:
        """Retrieve token data and associated user_id based on the token's hash."""
        pass

    @abc.abstractmethod
    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Retrieve user details based on user_id."""
        pass
        
    @abc.abstractmethod
    async def create_user(self, username: str, email: Optional[str] = None, status: str = 'active') -> int:
        """Create a new user and return their user_id."""
        pass

    @abc.abstractmethod
    async def add_user_token(self, user_id: int, token_hash: str, description: Optional[str] = None, expires_at: Optional[datetime] = None, status: str = 'active') -> int:
        """Add a new token (hashed) for a user and return the token_id."""
        pass

    @abc.abstractmethod
    async def update_token_last_used(self, token_id: int):
        """Update the last_used timestamp for a specific token."""
        pass

    @abc.abstractmethod
    async def delete_token(self, token_id: int):
        """Delete/invalidate a specific token (by ID or hash)."""
        # Consider whether this should truly delete or just set status to 'revoked'.
        pass
        
    # --- User Account Access Methods (Phase 3 / Future) ---
    
    @abc.abstractmethod
    async def add_account_access(self, user_id: int, customer_id: str, access_level: str = 'read', granted_by: Optional[int] = None):
        """Grant a user access to a specific Google Ads customer ID."""
        pass
        
    @abc.abstractmethod
    async def get_user_accessible_accounts(self, user_id: int) -> List[Dict]:
        """Get a list of Google Ads customer IDs accessible by a user."""
        pass

    @abc.abstractmethod
    async def check_account_access(self, user_id: int, customer_id: str, required_level: str = 'read') -> bool:
        """Check if a user has the required access level for a specific customer ID."""
        pass


class DatabaseError(Exception):
    """Exception raised for database errors."""
    pass 