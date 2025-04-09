"""
Unit tests for database caching functionality.

This module tests the caching functionality of the database abstraction layer,
focusing on cache hits, misses, and expiration.
"""

import unittest
import asyncio
import time
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import logging

from google_ads_mcp_server.db.interface import DatabaseInterface
from google_ads_mcp_server.db.factory import get_database_manager
from google_ads_mcp_server.db.models import CacheEntry
from google_ads.client_with_sqlite_cache import GoogleAdsServiceWithSQLiteCache


class TestCacheFunctionality(unittest.TestCase):
    """
    Test cases for caching functionality through the database abstraction layer.
    """
    
    @patch('google_ads.client_base.GoogleAdsClient.__init__', return_value=None)  # Patch base init
    def setUp(self, mock_base_init):
        """Set up test dependencies and fixtures."""
        # Create a mock database manager
        self.db_manager = MagicMock(spec=DatabaseInterface)
        
        # Configure mock behavior
        self.db_manager.get_api_response.return_value = None  # Default to cache miss
        self.db_manager.store_api_response.return_value = "mock-cache-key"
        
        # Create a service with our mock db manager
        # The base __init__ is patched, so no real auth happens here
        self.service = GoogleAdsServiceWithSQLiteCache(
            cache_enabled=True,
            cache_ttl=3600,  # 1 hour TTL
            db_manager=self.db_manager
        )
        
        # Manually create logger if needed (base init would normally do this)
        if not hasattr(self.service, 'logger'):
             self.service.logger = logging.getLogger(self.service.__class__.__name__)
        
        # Mock the _execute_query method to avoid actual API calls
        self.mock_execute = patch.object(
            self.service, 
            '_execute_query', 
            new_callable=AsyncMock
        ).start()
        self.addCleanup(patch.stopall) # Ensure patch stops after test
        
        # Set up mock data for testing
        self.mock_campaign_data = [
            {"id": "1", "name": "Campaign 1", "status": "ENABLED"},
            {"id": "2", "name": "Campaign 2", "status": "PAUSED"}
        ]
        self.mock_execute.return_value = self.mock_campaign_data
        
        # Standard test parameters
        self.customer_id = "1234567890"
        self.method_name = "get_campaigns"
        
    def tearDown(self):
        """Clean up after tests."""
        # self.addCleanup handles patch.stopall now
        pass
    
    async def test_cache_miss_calls_api(self):
        """Test that a cache miss results in an API call."""
        # Configure the mock to return None (cache miss)
        self.db_manager.get_api_response.return_value = None
        
        # Call method that should check cache
        result = await self.service._execute_query(
            method_name=self.method_name,
            query="SELECT * FROM campaign",
            customer_id=self.customer_id
        )
        
        # Verify cache was checked
        self.db_manager.get_api_response.assert_called_once()
        
        # Verify API call was made
        self.mock_execute.assert_called_once()
        
        # Verify result matches mock API response
        self.assertEqual(result, self.mock_campaign_data)
        
        # Verify result was stored in cache
        self.db_manager.store_api_response.assert_called_once()
    
    async def test_cache_hit_avoids_api_call(self):
        """Test that a cache hit avoids making an API call."""
        # Configure the mock to return cached data
        self.db_manager.get_api_response.return_value = self.mock_campaign_data
        
        # Call method that should check cache
        result = await self.service._execute_query(
            method_name=self.method_name,
            query="SELECT * FROM campaign",
            customer_id=self.customer_id
        )
        
        # Verify cache was checked
        self.db_manager.get_api_response.assert_called_once()
        
        # Verify no API call was made
        self.mock_execute.assert_not_called()
        
        # Verify result matches cached data
        self.assertEqual(result, self.mock_campaign_data)
        
        # Verify no cache storage call was made
        self.db_manager.store_api_response.assert_not_called()
    
    async def test_cache_disabled_bypasses_cache(self):
        """Test that disabling the cache bypasses all cache operations."""
        # Create a service with caching disabled
        service_no_cache = GoogleAdsServiceWithSQLiteCache(
            cache_enabled=False,
            db_manager=self.db_manager
        )
        
        # Mock the _execute_query method
        with patch.object(service_no_cache, '_execute_query', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = self.mock_campaign_data
            
            # Call method that would normally check cache
            result = await service_no_cache._execute_query(
                method_name=self.method_name,
                query="SELECT * FROM campaign",
                customer_id=self.customer_id
            )
            
            # Verify cache was NOT checked
            self.db_manager.get_api_response.assert_not_called()
            
            # Verify API call was made directly
            mock_exec.assert_called_once()
            
            # Verify result matches mock API response
            self.assertEqual(result, self.mock_campaign_data)
            
            # Verify result was NOT stored in cache
            self.db_manager.store_api_response.assert_not_called()
    
    async def test_different_params_use_different_cache_keys(self):
        """Test that different parameters result in different cache keys."""
        # Make two calls with different parameters
        await self.service._execute_query(
            method_name=self.method_name,
            query="SELECT * FROM campaign WHERE status = 'ENABLED'",
            customer_id=self.customer_id
        )
        
        await self.service._execute_query(
            method_name=self.method_name,
            query="SELECT * FROM campaign WHERE status = 'PAUSED'",
            customer_id=self.customer_id
        )
        
        # Get the cache key generation parameters from both calls
        call_args_list = self.db_manager.get_api_response.call_args_list
        
        # Extract the query_params argument from each call
        first_call_params = call_args_list[0][1]['query_params']
        second_call_params = call_args_list[1][1]['query_params']
        
        # Verify that the query parameters are different
        self.assertNotEqual(
            first_call_params,
            second_call_params,
            "Different queries should result in different cache parameters"
        )
    
    async def test_customer_id_included_in_cache_key(self):
        """Test that the customer ID is included in the cache key."""
        # Make two calls with different customer IDs
        await self.service._execute_query(
            method_name=self.method_name,
            query="SELECT * FROM campaign",
            customer_id="1111111111"
        )
        
        await self.service._execute_query(
            method_name=self.method_name,
            query="SELECT * FROM campaign",
            customer_id="2222222222"
        )
        
        # Get the cache key parameters from both calls
        call_args_list = self.db_manager.get_api_response.call_args_list
        
        # Verify the customer_id parameter from each call
        first_call_customer_id = call_args_list[0][1]['customer_id']
        second_call_customer_id = call_args_list[1][1]['customer_id']
        
        # Verify that different customer IDs are used
        self.assertNotEqual(
            first_call_customer_id,
            second_call_customer_id,
            "Different customer IDs should be used in cache keys"
        )


class TestCacheTTLExpiration(unittest.TestCase):
    """
    Test cases for cache TTL (Time-To-Live) expiration functionality.
    """
    
    @patch('google_ads.client_base.GoogleAdsClient.__init__', return_value=None)  # Patch base init
    def setUp(self, mock_base_init):
        """Set up test dependencies and fixtures."""
        # Create a real SQLite database manager for TTL testing
        self.db_manager = get_database_manager(db_type="sqlite", db_config={"db_path": ":memory:"})
        
        # Create a service with a very short TTL
        # The base __init__ is patched, so no real auth happens here
        self.service = GoogleAdsServiceWithSQLiteCache(
            cache_enabled=True,
            cache_ttl=1,  # 1 second TTL for testing expiration
            db_manager=self.db_manager
        )
        
        # Manually create logger if needed
        if not hasattr(self.service, 'logger'):
             self.service.logger = logging.getLogger(self.service.__class__.__name__)
        
        # Mock the _execute_query method to avoid actual API calls
        self.mock_execute = patch.object(
            self.service, 
            '_execute_query', 
            new_callable=AsyncMock
        ).start()
        self.addCleanup(patch.stopall) # Ensure patch stops after test
        
        # Set up mock data for testing
        self.mock_campaign_data = [
            {"id": "1", "name": "Campaign 1", "status": "ENABLED"},
            {"id": "2", "name": "Campaign 2", "status": "PAUSED"}
        ]
        self.mock_execute.return_value = self.mock_campaign_data
        
        # Standard test parameters
        self.customer_id = "1234567890"
        self.method_name = "get_campaigns"
        self.query = "SELECT * FROM campaign"
        
    def tearDown(self):
        """Clean up after tests."""
        # self.addCleanup handles patch.stopall now
        if hasattr(self, 'db_manager') and hasattr(self.db_manager, 'close'):
            self.db_manager.close()
    
    async def test_cache_expires_after_ttl(self):
        """Test that cached data expires after the TTL period."""
        # First call - should be a cache miss
        result1 = await self.service._execute_query(
            method_name=self.method_name,
            query=self.query,
            customer_id=self.customer_id
        )
        
        # Verify API call was made
        self.assertEqual(self.mock_execute.call_count, 1)
        
        # Second call immediately after - should be a cache hit
        result2 = await self.service._execute_query(
            method_name=self.method_name,
            query=self.query,
            customer_id=self.customer_id
        )
        
        # Verify no additional API call was made
        self.assertEqual(self.mock_execute.call_count, 1)
        
        # Wait for TTL to expire
        await asyncio.sleep(1.5)  # Wait longer than the TTL
        
        # Third call after TTL expiration - should be a cache miss
        result3 = await self.service._execute_query(
            method_name=self.method_name,
            query=self.query,
            customer_id=self.customer_id
        )
        
        # Verify another API call was made
        self.assertEqual(self.mock_execute.call_count, 2)
        
        # Verify all results match
        self.assertEqual(result1, self.mock_campaign_data)
        self.assertEqual(result2, self.mock_campaign_data)
        self.assertEqual(result3, self.mock_campaign_data)


def run_tests():
    """Run the tests using asyncio."""
    # Create a test loader
    loader = unittest.TestLoader()
    
    # Create test suites
    functionality_suite = loader.loadTestsFromTestCase(TestCacheFunctionality)
    ttl_suite = loader.loadTestsFromTestCase(TestCacheTTLExpiration)
    
    # Create a test runner
    runner = unittest.TextTestRunner()
    
    # Run the async tests
    for test in functionality_suite:
        asyncio.run(test)
    
    for test in ttl_suite:
        asyncio.run(test)


if __name__ == "__main__":
    run_tests() 