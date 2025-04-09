"""
Test the Google Ads client with database abstraction layer.

This module tests the integration of GoogleAdsServiceWithSQLiteCache with the 
database abstraction layer, ensuring it works correctly with different database types.
"""

import os
import unittest
import tempfile
from unittest import mock
import asyncio
from unittest.mock import patch, MagicMock

from google_ads_mcp_server.google_ads.client import get_google_ads_client
from google_ads_mcp_server.client_with_sqlite_cache import GoogleAdsServiceWithSQLiteCache
from google_ads_mcp_server.db.interface import DatabaseInterface
from google_ads_mcp_server.db.sqlite_manager import SQLiteDatabaseManager
from google_ads_mcp_server.db.factory import get_database_manager


class MockDatabaseManager(DatabaseInterface):
    """Mock database manager for testing."""
    
    def __init__(self):
        self.cache = {}
        self.initialize_called = False
        self.close_called = False
        self.store_api_response_calls = []
        self.get_api_response_calls = []
        
    def initialize(self) -> None:
        self.initialize_called = True
        
    def close(self) -> None:
        self.close_called = True
        
    def execute_transaction(self, sql_statements):
        pass
        
    def store_api_response(self, customer_id, query_type, query_params, response_data, **kwargs):
        self.store_api_response_calls.append({
            "customer_id": customer_id,
            "query_type": query_type,
            "query_params": query_params,
            "response_data": response_data,
            "kwargs": kwargs
        })
        key = f"{customer_id}:{query_type}:{hash(str(query_params))}"
        self.cache[key] = response_data
        return key
        
    def get_api_response(self, customer_id, query_type, query_params):
        self.get_api_response_calls.append({
            "customer_id": customer_id,
            "query_type": query_type,
            "query_params": query_params
        })
        key = f"{customer_id}:{query_type}:{hash(str(query_params))}"
        return self.cache.get(key)
    
    # Implement all other required methods with minimal functionality
    def store_entity_data(self, entity_type, customer_id, entity_data, **kwargs):
        return "mock_key"
        
    def get_entity_data(self, entity_type, customer_id, **kwargs):
        return None
        
    def store_account_kpi_data(self, account_id, start_date, end_date, kpi_data, **kwargs):
        return "mock_key"
        
    def get_account_kpi_data(self, account_id, start_date, end_date, **kwargs):
        return None
        
    def clean_cache(self):
        self.cache = {}
        
    def clear_cache(self, entity_type=None, customer_id=None):
        self.cache = {}
        
    def get_cache_stats(self):
        return {"mock_stats": len(self.cache)}
        
    def store_user_data(self, user_id, user_data):
        pass
        
    def get_user_data(self, user_id):
        return None
        
    def store_user_account_access(self, user_id, customer_id, access_level):
        pass
        
    def get_user_accounts(self, user_id):
        return []
        
    def check_user_account_access(self, user_id, customer_id, required_access_level=None):
        return False
        
    def store_config(self, config_key, config_data, user_id=None):
        pass
        
    def get_config(self, config_key, user_id=None):
        return None


class TestClientWithDatabaseAbstraction(unittest.TestCase):
    """Test case for the Google Ads client with database abstraction layer."""
    
    def test_client_with_mock_db_manager(self):
        """Test client with a mock database manager."""
        # Create a mock database manager
        mock_db_manager = MockDatabaseManager()
        
        # Create a client with the mock database manager
        client = GoogleAdsServiceWithSQLiteCache(
            cache_enabled=True,
            db_manager=mock_db_manager
        )
        
        # Verify the client is using our mock database manager
        self.assertEqual(client.db_manager, mock_db_manager)
        
        # Mock the _execute_query method to avoid actual API calls
        with mock.patch.object(client, '_execute_query') as mock_execute:
            # Set up the mock to return some test data
            mock_execute.return_value = {"campaigns": [{"id": "123", "name": "Test Campaign"}]}
            
            # Call a method that would use caching
            method_name = "get_campaigns"
            customer_id = "1234567890"
            
            # First call should result in a cache miss and store in cache
            result = client._get_cached_data(method_name, customer_id=customer_id)
            self.assertIsNone(result)  # No cache hit
            
            # Execute the mock query
            query_result = {"campaigns": [{"id": "123", "name": "Test Campaign"}]}
            client._cache_data(method_name, query_result, customer_id=customer_id)
            
            # Verify the store_api_response was called
            self.assertEqual(len(mock_db_manager.store_api_response_calls), 1)
            self.assertEqual(mock_db_manager.store_api_response_calls[0]["customer_id"], customer_id)
            self.assertEqual(mock_db_manager.store_api_response_calls[0]["query_type"], method_name)
            
            # Second call should result in a cache hit
            result = client._get_cached_data(method_name, customer_id=customer_id)
            self.assertIsNotNone(result)  # Cache hit
            self.assertEqual(result, query_result)
            
            # Verify the get_api_response was called
            self.assertEqual(len(mock_db_manager.get_api_response_calls), 2)  # Called twice
    
    def test_client_factory_with_sqlite(self):
        """Test client factory with SQLite database."""
        # Create a temporary SQLite database file
        with tempfile.NamedTemporaryFile(delete=False) as temp_db:
            temp_db.close()
            
            try:
                # Create a client with SQLite configuration
                with mock.patch('google_ads_mcp_server.google_ads.client.get_database_manager') as mock_get_db:
                    # Set up the mock to return a SQLiteDatabaseManager
                    sqlite_manager = SQLiteDatabaseManager(db_path=temp_db.name)
                    mock_get_db.return_value = sqlite_manager
                    
                    # Create a client
                    client = get_google_ads_client(
                        use_cache=True,
                        db_type="sqlite",
                        db_config={"db_path": temp_db.name}
                    )
                    
                    # Verify the client is a GoogleAdsServiceWithSQLiteCache
                    self.assertIsInstance(client, GoogleAdsServiceWithSQLiteCache)
                    
                    # Verify get_database_manager was called correctly
                    mock_get_db.assert_called_once_with(
                        db_type="sqlite",
                        db_config={"db_path": temp_db.name}
                    )
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_db.name):
                    os.unlink(temp_db.name)
    
    def test_client_with_environment_variables(self):
        """Test client initialization using environment variables."""
        # Save the original environment values
        original_use_cache = os.environ.get("USE_CACHE")
        original_db_type = os.environ.get("DB_TYPE")
        original_db_path = os.environ.get("DB_PATH")
        
        try:
            # Set up environment variables
            os.environ["USE_CACHE"] = "true"
            os.environ["DB_TYPE"] = "sqlite"
            
            # Create a temporary database file
            with tempfile.NamedTemporaryFile(delete=False) as temp_db:
                temp_db.close()
                os.environ["DB_PATH"] = temp_db.name
                
                try:
                    # Mock the database manager factory
                    with mock.patch('google_ads_mcp_server.client_with_sqlite_cache.get_database_manager') as mock_get_db:
                        # Set up the mock to return a SQLiteDatabaseManager
                        sqlite_manager = SQLiteDatabaseManager(db_path=temp_db.name)
                        mock_get_db.return_value = sqlite_manager
                        
                        # Create a client
                        client = GoogleAdsServiceWithSQLiteCache(cache_enabled=True)
                        
                        # Verify get_database_manager was called correctly
                        mock_get_db.assert_called_once()
                        call_args = mock_get_db.call_args[1]
                        self.assertEqual(call_args["db_type"], "sqlite")
                        self.assertTrue("db_config" in call_args)
                finally:
                    # Clean up the temporary file
                    if os.path.exists(temp_db.name):
                        os.unlink(temp_db.name)
        finally:
            # Restore original environment variables
            if original_use_cache is not None:
                os.environ["USE_CACHE"] = original_use_cache
            else:
                os.environ.pop("USE_CACHE", None)
                
            if original_db_type is not None:
                os.environ["DB_TYPE"] = original_db_type
            else:
                os.environ.pop("DB_TYPE", None)
                
            if original_db_path is not None:
                os.environ["DB_PATH"] = original_db_path
            else:
                os.environ.pop("DB_PATH", None)
    
    def test_client_with_postgres_config(self):
        """Test client initialization with PostgreSQL configuration."""
        # Mock the database manager factory
        with mock.patch('google_ads_mcp_server.client_with_sqlite_cache.get_database_manager') as mock_get_db:
            # Set up mock to return our mock database manager
            mock_db_manager = MockDatabaseManager()
            mock_get_db.return_value = mock_db_manager
            
            # Create a client with PostgreSQL configuration
            client = GoogleAdsServiceWithSQLiteCache(
                cache_enabled=True,
                db_config={
                    "host": "localhost",
                    "port": 5432,
                    "database": "google_ads_mcp",
                    "user": "postgres",
                    "password": "password",
                    "ssl_mode": "require"
                }
            )
            
            # Verify the client is using our mock database manager
            self.assertEqual(client.db_manager, mock_db_manager)
            
            # Verify that get_database_manager was called with the correct configuration
            call_kwargs = mock_get_db.call_args[1]
            
            # Default is sqlite if not specified
            self.assertEqual(call_kwargs["db_type"], "sqlite")
            self.assertEqual(call_kwargs["db_config"]["host"], "localhost")
            self.assertEqual(call_kwargs["db_config"]["port"], 5432)
            self.assertEqual(call_kwargs["db_config"]["database"], "google_ads_mcp")


if __name__ == "__main__":
    unittest.main() 