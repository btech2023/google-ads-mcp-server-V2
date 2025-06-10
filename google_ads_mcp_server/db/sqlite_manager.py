# flake8: noqa
"""
SQLite Database Manager Module

This module provides the SQLiteDatabaseManager class which implements the DatabaseInterface
for SQLite databases. It handles all database operations, including cache management
for the Google Ads MCP Server.
"""

import hashlib
import json
import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
import aiosqlite

from .interface import DatabaseError, DatabaseInterface
from .schema import (
    ALL_INDEXES,
    ALL_TABLES,
    CACHE_TABLES,
    CLEAN_EXPIRED_CACHE,
    CREATE_CONFIG_TABLES_SQL,
    CREATE_USER_TABLES_SQL,
    GET_CACHE_STATS,
)

logger = logging.getLogger(__name__)


class SQLiteDatabaseManager(DatabaseInterface):
    """
    SQLite implementation of the DatabaseInterface.

    This class handles database initialization, caching operations,
    and other persistent storage needs using SQLite.
    """

    def __init__(self, db_path: str = None, auto_clean_interval: int = 3600):
        """
        Initialize the SQLite database manager.

        Args:
            db_path: Path to the SQLite database file. If None, uses a default path.
            auto_clean_interval: Interval in seconds between automatic cache cleanups.
                                Set to 0 to disable auto-cleaning.
        """
        if db_path is None:
            # Default to a database file in the same directory as this module
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, "google_ads_mcp.db")

        self.db_path = db_path
        self.auto_clean_interval = auto_clean_interval
        self.last_clean_time = 0

        # Initialize database
        self.initialize()

    def initialize(self) -> None:
        """Initialize the database schema if it doesn't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Create tables
            for create_table_sql in ALL_TABLES:
                cursor.execute(create_table_sql)

            # Create user and config tables
            for create_user_table_sql in CREATE_USER_TABLES_SQL:
                cursor.execute(create_user_table_sql)

            for create_config_table_sql in CREATE_CONFIG_TABLES_SQL:
                cursor.execute(create_config_table_sql)

            # Create indexes
            for create_index_sql in ALL_INDEXES:
                cursor.execute(create_index_sql)

            conn.commit()
            logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            conn.rollback()
            raise DatabaseError(f"Failed to initialize database: {e}")
        finally:
            conn.close()

    def close(self) -> None:
        """Close any open database connections."""
        # SQLite connections are created and closed for each operation
        # so there's nothing to do here
        pass

    def execute_transaction(self, sql_statements: List[Tuple[str, List[Any]]]) -> None:
        """
        Execute multiple SQL statements as a single transaction.

        Args:
            sql_statements: List of tuples containing (sql_query, parameters)

        Raises:
            DatabaseError: If the transaction fails
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            for query, params in sql_statements:
                cursor.execute(query, params)

            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error executing transaction: {e}")
            conn.rollback()
            raise DatabaseError(f"Failed to execute transaction: {e}")
        finally:
            conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a connection to the SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            return conn
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise DatabaseError(f"Failed to connect to database: {e}")

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

    def _generate_cache_key(
        self, entity_type: str, customer_id: str, query_params: Dict[str, Any]
    ) -> str:
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
        metadata: Optional[Dict[str, Any]] = None,
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
        query_hash = hashlib.md5(
            json.dumps(query_params, sort_keys=True).encode()
        ).hexdigest()
        cache_key = self._generate_cache_key("api", customer_id, query_params)

        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(
            seconds=ttl_seconds + 2
        )  # Add 2 seconds grace period

        # Serialize data to JSON
        response_json = json.dumps(response_data)
        metadata_json = json.dumps(metadata) if metadata else None

        # Debug information
        logger.debug(f"Storing API response with key: {cache_key}")
        logger.debug(f"Customer ID: {customer_id}, Query type: {query_type}")
        logger.debug(
            f"TTL: {ttl_seconds} seconds, Expires at: {expires_at.isoformat()}"
        )

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
                metadata_json,
            )

            cursor.execute(query, values)

            # Verify that the data was stored
            cursor.execute(
                "SELECT COUNT(*) as count FROM api_cache WHERE cache_key = ?",
                (cache_key,),
            )
            count_row = cursor.fetchone()
            if count_row and count_row["count"] > 0:
                logger.debug(f"Successfully stored data for key {cache_key}")
            else:
                logger.debug(f"Failed to store data for key {cache_key}")

            conn.commit()

            return cache_key

        except sqlite3.Error as e:
            logger.error(f"Error storing API response in cache: {e}")
            conn.rollback()
            raise DatabaseError(f"Failed to store API response in cache: {e}")
        finally:
            conn.close()

    def get_api_response(
        self, customer_id: str, query_type: str, query_params: Dict[str, Any]
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
        cache_key = self._generate_cache_key("api", customer_id, query_params)

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
                cursor.execute(
                    "SELECT expires_at FROM api_cache WHERE cache_key = ?", (cache_key,)
                )
                any_row = cursor.fetchone()
                if any_row:
                    logger.debug(
                        f"Entry found but expired. Expiry was: {any_row['expires_at']}"
                    )

                # Also check if there are any rows in the table
                cursor.execute("SELECT COUNT(*) as count FROM api_cache")
                count_row = cursor.fetchone()
                logger.debug(f"Total entries in api_cache: {count_row['count']}")

                return None

            # Parse response data from JSON
            try:
                response_data = json.loads(row["response_data"])
                metadata = json.loads(row["metadata"]) if row["metadata"] else None

                logger.debug(f"Cache hit for key {cache_key}")

                # If metadata is needed, return both
                if metadata:
                    return {"data": response_data, "metadata": metadata}

                return response_data
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                logger.debug(
                    f"Response data: {row['response_data'][:100]}..."
                )  # Show first 100 chars
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
        **params,
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
        expires_at = datetime.utcnow() + timedelta(
            seconds=ttl_seconds + 2
        )  # Add 2 seconds grace period

        # Serialize data to JSON
        entity_data_json = json.dumps(entity_data)

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Prepare column names and placeholders for dynamic SQL
            columns = ["cache_key", "customer_id", f"{entity_type}_data", "expires_at"]
            values = [cache_key, customer_id, entity_data_json, expires_at.isoformat()]

            # Add additional parameters
            for key, value in params.items():
                if value is not None:
                    columns.append(key)
                    values.append(value)

            # Construct SQL query
            placeholders = ", ".join(["?"] * len(values))
            columns_str = ", ".join(columns)

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
            raise DatabaseError(f"Failed to store {entity_type} data in cache: {e}")
        finally:
            conn.close()

    def get_entity_data(
        self, entity_type: str, customer_id: str, **params
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
                (cache_key,),
            )

            row = cursor.fetchone()
            if row is None:
                logger.debug(f"Cache miss for {entity_type} with key {cache_key}")
                return None

            # Parse data from JSON
            try:
                entity_data = json.loads(row[f"{entity_type}_data"])
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
        ttl_seconds: int = 900,  # 15 minutes default
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
        """
        self._maybe_clean_cache()

        # Generate cache key
        cache_params = {
            "start_date": start_date,
            "end_date": end_date,
            "segmentation": segmentation,
        }
        cache_key = self._generate_cache_key("account_kpi", account_id, cache_params)

        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(
            seconds=ttl_seconds + 2
        )  # Add 2 seconds grace period

        # Serialize data to JSON
        kpi_data_json = json.dumps(kpi_data)
        segmentation_json = json.dumps(segmentation) if segmentation else None

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Insert or replace existing cache entry
            query = """
            INSERT OR REPLACE INTO account_kpi_cache
            (cache_key, account_id, start_date, end_date, segmentation, kpi_data, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """

            values = (
                cache_key,
                account_id,
                start_date,
                end_date,
                segmentation_json,
                kpi_data_json,
                expires_at.isoformat(),
            )

            cursor.execute(query, values)
            conn.commit()

            logger.debug(f"Stored account KPI data in cache with key {cache_key}")
            return cache_key

        except sqlite3.Error as e:
            logger.error(f"Error storing account KPI data in cache: {e}")
            conn.rollback()
            raise DatabaseError(f"Failed to store account KPI data in cache: {e}")
        finally:
            conn.close()

    def get_account_kpi_data(
        self,
        account_id: str,
        start_date: str,
        end_date: str,
        segmentation: Optional[Dict[str, Any]] = None,
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
        self._maybe_clean_cache()

        # Generate cache key
        cache_params = {
            "start_date": start_date,
            "end_date": end_date,
            "segmentation": segmentation,
        }
        cache_key = self._generate_cache_key("account_kpi", account_id, cache_params)

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
                (cache_key,),
            )

            row = cursor.fetchone()
            if row is None:
                logger.debug(f"Cache miss for account KPI data with key {cache_key}")
                return None

            # Parse data from JSON
            try:
                kpi_data = json.loads(row["kpi_data"])
                logger.debug(f"Cache hit for account KPI data with key {cache_key}")
                return kpi_data
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return None

        except sqlite3.Error as e:
            logger.error(f"Error retrieving account KPI data from cache: {e}")
            return None
        finally:
            conn.close()

    def clean_cache(self) -> None:
        """
        Clean expired cache entries from all cache tables.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            for table_name in CACHE_TABLES.values():
                # Delete expired entries
                cursor.execute(CLEAN_EXPIRED_CACHE.format(table=table_name))

            conn.commit()
            logger.info("Cache cleaned")
        except sqlite3.Error as e:
            logger.error(f"Error cleaning cache: {e}")
            conn.rollback()
            raise DatabaseError(f"Failed to clean cache: {e}")
        finally:
            conn.close()

    def clear_cache(
        self, entity_type: Optional[str] = None, customer_id: Optional[str] = None
    ) -> None:
        """
        Clear cache entries, optionally filtered by entity type and/or customer ID.

        Args:
            entity_type: Optional entity type to clear ('api', 'campaign', etc.)
            customer_id: Optional customer ID to clear cache for
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if entity_type and customer_id:
                # Clear specific entity type for specific customer
                if entity_type not in CACHE_TABLES:
                    raise ValueError(f"Unknown entity type: {entity_type}")

                table_name = CACHE_TABLES[entity_type]
                cursor.execute(
                    f"DELETE FROM {table_name} WHERE customer_id = ?", (customer_id,)
                )
                logger.info(f"Cleared {entity_type} cache for customer {customer_id}")

            elif entity_type:
                # Clear all entries of specific entity type
                if entity_type not in CACHE_TABLES:
                    raise ValueError(f"Unknown entity type: {entity_type}")

                table_name = CACHE_TABLES[entity_type]
                cursor.execute(f"DELETE FROM {table_name}")
                logger.info(f"Cleared all {entity_type} cache entries")

            elif customer_id:
                # Clear all entries for specific customer across all tables
                for entity_type, table_name in CACHE_TABLES.items():
                    if entity_type == "account_kpi":
                        cursor.execute(
                            f"DELETE FROM {table_name} WHERE account_id = ?",
                            (customer_id,),
                        )
                    else:
                        cursor.execute(
                            f"DELETE FROM {table_name} WHERE customer_id = ?",
                            (customer_id,),
                        )

                logger.info(f"Cleared all cache entries for customer {customer_id}")

            else:
                # Clear all cache entries
                for table_name in CACHE_TABLES.values():
                    cursor.execute(f"DELETE FROM {table_name}")

                logger.info("Cleared all cache entries")

            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error clearing cache: {e}")
            conn.rollback()
            raise DatabaseError(f"Failed to clear cache: {e}")
        finally:
            conn.close()

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get statistics about the cache.

        Returns:
            Dictionary with cache table names as keys and item counts as values
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(GET_CACHE_STATS)
            row = cursor.fetchone()
            if row:
                return {
                    "api_cache": row["api_cache_count"],
                    "account_kpi_cache": row["account_kpi_cache_count"],
                    "campaign_cache": row["campaign_cache_count"],
                    "keyword_cache": row["keyword_cache_count"],
                    "search_term_cache": row["search_term_cache_count"],
                    "budget_cache": row["budget_cache_count"],
                }
            else:
                return {name: 0 for name in CACHE_TABLES.keys()}

        except sqlite3.Error as e:
            logger.error(f"Error getting cache stats: {e}")
            return {name: 0 for name in CACHE_TABLES.keys()}
        finally:
            conn.close()

    # User data operations - For multi-user support

    def store_user_data(self, user_id: str, user_data: Dict[str, Any]) -> None:
        """
        Store user data in the database.

        Args:
            user_id: Unique identifier for the user
            user_data: User data to store

        Raises:
            DatabaseError: If storing fails
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Serialize user data to JSON
            user_data_json = json.dumps(user_data)

            # Insert or replace existing user
            query = """
            INSERT OR REPLACE INTO users
            (user_id, user_data, created_at, updated_at)
            VALUES (?, ?, COALESCE((SELECT created_at FROM users WHERE user_id = ?), CURRENT_TIMESTAMP), CURRENT_TIMESTAMP)
            """

            cursor.execute(query, (user_id, user_data_json, user_id))
            conn.commit()

            logger.info(f"Stored data for user {user_id}")
        except sqlite3.Error as e:
            logger.error(f"Error storing user data: {e}")
            conn.rollback()
            raise DatabaseError(f"Failed to store user data: {e}")
        finally:
            conn.close()

    def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user data from the database.

        Args:
            user_id: Unique identifier for the user

        Returns:
            The user data, or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT user_data FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()

            if not row:
                return None

            # Parse user data from JSON
            try:
                return json.loads(row["user_data"])
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for user {user_id}: {e}")
                return None

        except sqlite3.Error as e:
            logger.error(f"Error retrieving user data: {e}")
            return None
        finally:
            conn.close()

    def store_user_account_access(
        self, user_id: str, customer_id: str, access_level: str
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
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Insert or replace existing access
            query = """
            INSERT OR REPLACE INTO user_account_access
            (user_id, customer_id, access_level, created_at, updated_at)
            VALUES (?, ?, ?, COALESCE((SELECT created_at FROM user_account_access 
                                       WHERE user_id = ? AND customer_id = ?), 
                                     CURRENT_TIMESTAMP), CURRENT_TIMESTAMP)
            """

            cursor.execute(
                query, (user_id, customer_id, access_level, user_id, customer_id)
            )
            conn.commit()

            logger.info(
                f"Granted {access_level} access to account {customer_id} for user {user_id}"
            )
        except sqlite3.Error as e:
            logger.error(f"Error granting account access: {e}")
            conn.rollback()
            raise DatabaseError(f"Failed to grant account access: {e}")
        finally:
            conn.close()

    def get_user_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all accounts a user has access to.

        Args:
            user_id: Unique identifier for the user

        Returns:
            List of dictionaries with customer_id and access_level
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT customer_id, access_level 
                FROM user_account_access 
                WHERE user_id = ?
                """,
                (user_id,),
            )

            return [
                {"customer_id": row["customer_id"], "access_level": row["access_level"]}
                for row in cursor.fetchall()
            ]

        except sqlite3.Error as e:
            logger.error(f"Error retrieving user accounts: {e}")
            return []
        finally:
            conn.close()

    def check_user_account_access(
        self,
        user_id: str,
        customer_id: str,
        required_access_level: Optional[str] = None,
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
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if required_access_level:
                # Check for specific access level
                # This simplified implementation assumes 'admin' > 'write' > 'read'
                access_levels = {"read": 1, "write": 2, "admin": 3}
                required_level_value = access_levels.get(
                    required_access_level.lower(), 0
                )

                if required_level_value == 0:
                    logger.warning(f"Unknown access level: {required_access_level}")
                    return False

                cursor.execute(
                    """
                    SELECT access_level 
                    FROM user_account_access 
                    WHERE user_id = ? AND customer_id = ?
                    """,
                    (user_id, customer_id),
                )

                row = cursor.fetchone()
                if not row:
                    return False

                user_level_value = access_levels.get(row["access_level"].lower(), 0)
                return user_level_value >= required_level_value
            else:
                # Check for any access
                cursor.execute(
                    """
                    SELECT COUNT(*) as count 
                    FROM user_account_access 
                    WHERE user_id = ? AND customer_id = ?
                    """,
                    (user_id, customer_id),
                )

                row = cursor.fetchone()
                return row["count"] > 0

        except sqlite3.Error as e:
            logger.error(f"Error checking user account access: {e}")
            return False
        finally:
            conn.close()

    # Configuration operations

    def store_config(
        self,
        config_key: str,
        config_data: Dict[str, Any],
        user_id: Optional[str] = None,
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
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Serialize config data to JSON
            config_data_json = json.dumps(config_data)

            # Insert or replace existing configuration
            if user_id:
                # User-specific configuration
                query = """
                INSERT OR REPLACE INTO user_config
                (user_id, config_key, config_data, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """
                cursor.execute(query, (user_id, config_key, config_data_json))
            else:
                # Global configuration
                query = """
                INSERT OR REPLACE INTO system_config
                (config_key, config_data, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """
                cursor.execute(query, (config_key, config_data_json))

            conn.commit()

            if user_id:
                logger.info(f"Stored configuration {config_key} for user {user_id}")
            else:
                logger.info(f"Stored global configuration {config_key}")

        except sqlite3.Error as e:
            logger.error(f"Error storing configuration: {e}")
            conn.rollback()
            raise DatabaseError(f"Failed to store configuration: {e}")
        finally:
            conn.close()

    def get_config(
        self, config_key: str, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve configuration data from the database.

        Args:
            config_key: Unique identifier for the configuration
            user_id: Optional user ID for user-specific configurations

        Returns:
            The configuration data, or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if user_id:
                # Try to get user-specific configuration
                cursor.execute(
                    """
                    SELECT config_data 
                    FROM user_config 
                    WHERE user_id = ? AND config_key = ?
                    """,
                    (user_id, config_key),
                )

                row = cursor.fetchone()
                if row:
                    # User-specific configuration found
                    return json.loads(row["config_data"])

            # If no user-specific configuration found or no user_id provided,
            # try to get global configuration
            cursor.execute(
                """
                SELECT config_data 
                FROM system_config 
                WHERE config_key = ?
                """,
                (config_key,),
            )

            row = cursor.fetchone()
            if row:
                return json.loads(row["config_data"])

            # No configuration found
            return None

        except (sqlite3.Error, json.JSONDecodeError) as e:
            logger.error(f"Error retrieving configuration: {e}")
            return None
        finally:
            conn.close()

    # --- User/Token Methods ---

    async def get_token_data_by_hash(self, token_hash: str) -> Optional[Dict]:
        """Retrieve token data and associated user_id based on the token's hash."""
        sql = """
        SELECT token_id, user_id, description, created_at, expires_at, last_used, status
        FROM user_tokens
        WHERE token_hash = ?
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(sql, (token_hash,)) as cursor:
                    row = await cursor.fetchone()
            if row:
                logger.debug(f"Found token data for hash: {token_hash[:4]}...{token_hash[-4:]}")
                return dict(row)
            logger.debug(
                f"No token found for hash: {token_hash[:4]}...{token_hash[-4:]}"
            )
            return None
        except Exception as e:
            logger.error(f"Error retrieving token data by hash: {e}")
            return None

    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Retrieve user details based on user_id."""
        sql = """
        SELECT user_id, username, email, created_at, last_active, status
        FROM users
        WHERE user_id = ?
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(sql, (user_id,)) as cursor:
                    row = await cursor.fetchone()
            if row:
                logger.debug(f"Found user data for user_id: {user_id}")
                return dict(row)
            logger.debug(f"No user found for user_id: {user_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving user data by id {user_id}: {e}")
            return None

    async def create_user(
        self, username: str, email: Optional[str] = None, status: str = "active"
    ) -> int:
        """Create a new user and return their user_id."""
        sql = """
        INSERT INTO users (username, email, status, created_at)
        VALUES (?, ?, ?, datetime('now'))
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(sql, (username, email, status))
                await db.commit()
                user_id = cursor.lastrowid
                logger.info(f"Created user '{username}' with user_id: {user_id}")
                return user_id
        except aiosqlite.IntegrityError as e:
            logger.error(
                f"Failed to create user '{username}'. Username or email might already exist. Error: {e}"
            )
            return -1
        except Exception as e:
            logger.error(f"Error creating user '{username}': {e}")
            return -1

    async def add_user_token(
        self,
        user_id: int,
        token_hash: str,
        description: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        status: str = "active",
    ) -> int:
        """Add a new token (hashed) for a user and return the token_id."""
        sql = """
        INSERT INTO user_tokens (user_id, token_hash, description, expires_at, status, created_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        """
        expires_at_str = expires_at.isoformat() if expires_at else None
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    sql, (user_id, token_hash, description, expires_at_str, status)
                )
                await db.commit()
                token_id = cursor.lastrowid
                logger.info(f"Added token (ID: {token_id}) for user_id: {user_id}")
                return token_id
        except aiosqlite.IntegrityError as e:
            logger.error(
                f"Failed to add token for user {user_id}. Hash might already exist. Error: {e}"
            )
            return -1
        except Exception as e:
            logger.error(f"Error adding token for user {user_id}: {e}")
            return -1

    async def update_token_last_used(self, token_id: int):
        """Update the last_used timestamp for a specific token."""
        sql = "UPDATE user_tokens SET last_used = datetime('now') WHERE token_id = ?"
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(sql, (token_id,))
                await db.commit()
            logger.debug(f"Updated last_used for token_id: {token_id}")
        except Exception as e:
            logger.error(f"Error updating last_used for token {token_id}: {e}")

    async def delete_token(self, token_id: int):
        """Revoke a specific token by setting its status to 'revoked'."""
        sql = (
            "UPDATE user_tokens SET status = 'revoked', expires_at = datetime('now') "
            "WHERE token_id = ? AND status = 'active'"
        )
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(sql, (token_id,))
                await db.commit()
                if cursor.rowcount > 0:
                    logger.info(f"Revoked token_id: {token_id}")
                else:
                    logger.warning(
                        f"Attempted to revoke token_id: {token_id}, but it was not found or already revoked."
                    )
        except Exception as e:
            logger.error(f"Error revoking token {token_id}: {e}")

    async def add_account_access(
        self,
        user_id: int,
        customer_id: str,
        access_level: str = "read",
        granted_by: Optional[int] = None,
    ):
        logger.warning("add_account_access not implemented")

    async def get_user_accessible_accounts(self, user_id: int) -> List[Dict]:
        logger.warning("get_user_accessible_accounts not implemented")
        return []

    async def check_account_access(
        self, user_id: int, customer_id: str, required_level: str = "read"
    ) -> bool:
        logger.warning("check_account_access not implemented")
        return False
