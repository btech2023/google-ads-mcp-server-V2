"""
Test the database abstraction layer.

This module tests the database abstraction layer to ensure it works as expected,
particularly focusing on the SQLite implementation and compatibility with the interface.
"""

import os
import tempfile
import unittest
import json
from datetime import datetime, timedelta

from db.interface import DatabaseInterface
from db.factory import get_database_manager
from db.sqlite_manager import SQLiteDatabaseManager


class TestDatabaseAbstraction(unittest.TestCase):
    """Test case for the database abstraction layer."""

    def setUp(self):
        """Set up a test database."""
        # Create a temporary database file
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db_file.close()
        
        # Get a database manager using the factory
        self.db_manager = get_database_manager(
            db_type="sqlite",
            db_config={"db_path": self.temp_db_file.name}
        )
        
    def tearDown(self):
        """Clean up after tests."""
        self.db_manager.close()
        
        # Remove the temporary database file
        if os.path.exists(self.temp_db_file.name):
            os.unlink(self.temp_db_file.name)
            
    def test_factory_returns_interface_implementation(self):
        """Test that the factory returns an implementation of DatabaseInterface."""
        self.assertIsInstance(self.db_manager, DatabaseInterface)
        self.assertIsInstance(self.db_manager, SQLiteDatabaseManager)
        
    def test_api_cache_operations(self):
        """Test API cache operations."""
        # Test data
        customer_id = "1234567890"
        query_type = "get_campaigns"
        query_params = {"start_date": "2025-01-01", "end_date": "2025-01-31"}
        response_data = {"campaigns": [{"id": "123", "name": "Test Campaign"}]}
        
        # Store data in cache
        cache_key = self.db_manager.store_api_response(
            customer_id=customer_id,
            query_type=query_type,
            query_params=query_params,
            response_data=response_data
        )
        
        # Retrieve data from cache
        retrieved_data = self.db_manager.get_api_response(
            customer_id=customer_id,
            query_type=query_type,
            query_params=query_params
        )
        
        # Verify the data matches
        self.assertEqual(retrieved_data, response_data)
        
        # Test cache expiration
        # 1. Store with short TTL
        self.db_manager.store_api_response(
            customer_id=customer_id,
            query_type=query_type,
            query_params=query_params,
            response_data=response_data,
            ttl_seconds=1  # Very short TTL
        )
        
        # 2. Wait for TTL to expire
        import time
        time.sleep(2)
        
        # 3. Try to retrieve (should return None)
        expired_data = self.db_manager.get_api_response(
            customer_id=customer_id,
            query_type=query_type,
            query_params=query_params
        )
        
        self.assertIsNone(expired_data)
        
    def test_entity_data_operations(self):
        """Test entity data cache operations."""
        # Test data
        customer_id = "1234567890"
        entity_type = "campaign"
        campaign_id = "123456"
        entity_data = {"id": campaign_id, "name": "Test Campaign", "status": "ENABLED"}
        
        # Store entity data
        cache_key = self.db_manager.store_entity_data(
            entity_type=entity_type,
            customer_id=customer_id,
            entity_data=entity_data,
            campaign_id=campaign_id
        )
        
        # Retrieve entity data
        retrieved_data = self.db_manager.get_entity_data(
            entity_type=entity_type,
            customer_id=customer_id,
            campaign_id=campaign_id
        )
        
        # Verify the data matches
        self.assertEqual(retrieved_data, entity_data)
        
        # Test with invalid entity type
        with self.assertRaises(ValueError):
            self.db_manager.store_entity_data(
                entity_type="invalid_type",
                customer_id=customer_id,
                entity_data=entity_data
            )
            
    def test_user_data_operations(self):
        """Test user data operations."""
        # Test data
        user_id = "test_user_1"
        user_data = {"name": "Test User", "email": "test@example.com"}
        
        # Store user data
        self.db_manager.store_user_data(
            user_id=user_id,
            user_data=user_data
        )
        
        # Retrieve user data
        retrieved_data = self.db_manager.get_user_data(user_id)
        
        # Verify the data matches
        self.assertEqual(retrieved_data, user_data)
        
        # Test non-existent user
        non_existent_data = self.db_manager.get_user_data("non_existent_user")
        self.assertIsNone(non_existent_data)
        
    def test_user_account_access(self):
        """Test user account access operations."""
        # Test data
        user_id = "test_user_1"
        customer_id = "1234567890"
        
        # Initially, user should not have access
        has_access = self.db_manager.check_user_account_access(user_id, customer_id)
        self.assertFalse(has_access)
        
        # Grant read access
        self.db_manager.store_user_account_access(user_id, customer_id, "read")
        
        # Now user should have access
        has_access = self.db_manager.check_user_account_access(user_id, customer_id)
        self.assertTrue(has_access)
        
        # Check specific access levels
        has_read = self.db_manager.check_user_account_access(user_id, customer_id, "read")
        self.assertTrue(has_read)
        
        has_write = self.db_manager.check_user_account_access(user_id, customer_id, "write")
        self.assertFalse(has_write)
        
        # Grant higher access
        self.db_manager.store_user_account_access(user_id, customer_id, "admin")
        
        # Check access levels again
        has_read = self.db_manager.check_user_account_access(user_id, customer_id, "read")
        self.assertTrue(has_read)
        
        has_write = self.db_manager.check_user_account_access(user_id, customer_id, "write")
        self.assertTrue(has_write)
        
        has_admin = self.db_manager.check_user_account_access(user_id, customer_id, "admin")
        self.assertTrue(has_admin)
        
    def test_configuration_operations(self):
        """Test configuration operations."""
        # Test data
        system_config_key = "api_rate_limit"
        system_config_data = {"limit": 100, "period": 60}
        
        user_id = "test_user_1"
        user_config_key = "dashboard_preferences"
        user_config_data = {"theme": "dark", "metrics": ["clicks", "impressions"]}
        
        # Store system configuration
        self.db_manager.store_config(
            config_key=system_config_key,
            config_data=system_config_data
        )
        
        # Retrieve system configuration
        system_config = self.db_manager.get_config(system_config_key)
        self.assertEqual(system_config, system_config_data)
        
        # Store user configuration
        self.db_manager.store_config(
            config_key=user_config_key,
            config_data=user_config_data,
            user_id=user_id
        )
        
        # Retrieve user configuration
        user_config = self.db_manager.get_config(user_config_key, user_id)
        self.assertEqual(user_config, user_config_data)
        
        # Test fallback to system config when user config not available
        # First, retrieve a system-level config with a user ID
        system_with_user = self.db_manager.get_config(system_config_key, user_id)
        self.assertEqual(system_with_user, system_config_data)
        
        # Then, try to get a non-existent user config
        non_existent = self.db_manager.get_config("non_existent_key", user_id)
        self.assertIsNone(non_existent)
        
    def test_cache_statistics(self):
        """Test cache statistics."""
        # Initially, all cache tables should be empty
        stats = self.db_manager.get_cache_stats()
        for count in stats.values():
            self.assertEqual(count, 0)
            
        # Add some cache entries
        self.db_manager.store_api_response(
            customer_id="1234567890",
            query_type="get_campaigns",
            query_params={"start_date": "2025-01-01"},
            response_data={"campaigns": []}
        )
        
        self.db_manager.store_entity_data(
            entity_type="campaign",
            customer_id="1234567890",
            entity_data={"id": "123", "name": "Test"}
        )
        
        # Check statistics again
        stats = self.db_manager.get_cache_stats()
        self.assertEqual(stats["api_cache"], 1)
        self.assertEqual(stats["campaign_cache"], 1)
        
        # Clear specific cache
        self.db_manager.clear_cache(entity_type="api")
        
        # Check statistics again
        stats = self.db_manager.get_cache_stats()
        self.assertEqual(stats["api_cache"], 0)
        self.assertEqual(stats["campaign_cache"], 1)
        
        # Clear all cache
        self.db_manager.clear_cache()
        
        # Check statistics again
        stats = self.db_manager.get_cache_stats()
        for count in stats.values():
            self.assertEqual(count, 0)
            
    def test_transaction_execution(self):
        """Test transaction execution."""
        # Prepare SQL statements
        sql_statements = [
            (
                "INSERT INTO system_config (config_key, config_data) VALUES (?, ?)",
                ["test_key_1", json.dumps({"value": 1})]
            ),
            (
                "INSERT INTO system_config (config_key, config_data) VALUES (?, ?)",
                ["test_key_2", json.dumps({"value": 2})]
            )
        ]
        
        # Execute transaction
        self.db_manager.execute_transaction(sql_statements)
        
        # Verify both inserts were successful
        config_1 = self.db_manager.get_config("test_key_1")
        config_2 = self.db_manager.get_config("test_key_2")
        
        self.assertEqual(config_1["value"], 1)
        self.assertEqual(config_2["value"], 2)
        
        # Test transaction rollback
        # Prepare SQL statements with an error in the second one
        sql_statements = [
            (
                "INSERT INTO system_config (config_key, config_data) VALUES (?, ?)",
                ["test_key_3", json.dumps({"value": 3})]
            ),
            (
                "INSERT INTO non_existent_table (column) VALUES (?)",
                ["value"]
            )
        ]
        
        # Execute transaction (should fail)
        with self.assertRaises(Exception):
            self.db_manager.execute_transaction(sql_statements)
        
        # Verify the first insert was rolled back
        config_3 = self.db_manager.get_config("test_key_3")
        self.assertIsNone(config_3)


if __name__ == "__main__":
    unittest.main() 