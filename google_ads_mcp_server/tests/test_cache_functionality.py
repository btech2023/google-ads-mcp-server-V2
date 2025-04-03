#!/usr/bin/env python
"""
Cache Functionality Test Suite

This module contains tests for the SQLite caching implementation in the
Google Ads MCP Server, focusing on basic cache operations, expiration,
and cache invalidation.
"""

import os
import sys
import pytest
import time
import json
import sqlite3
import logging
from unittest import mock
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.manager import DatabaseManager
from google_ads.client_with_sqlite_cache import GoogleAdsServiceWithSQLiteCache
from google_ads.budgets import BudgetService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cache-test")

# Test configuration
TEST_DB_PATH = "test_cache.db"
TEST_CUSTOMER_ID = "1234567890"
SHORT_TTL = 1  # 1 second for expiration tests
STANDARD_TTL = 300  # 5 minutes for standard tests


class TestCacheFunctionality:
    """Test suite for cache functionality."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Remove test database if it exists
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        
        # Create the database manager with test path
        self.db_manager = DatabaseManager(db_path=TEST_DB_PATH)
        
        # Mock the Google Ads client for testing
        with mock.patch('google_ads.client_base.GoogleAdsClient.initialize'):
            # Create a Google Ads client with caching
            self.google_ads_client = GoogleAdsServiceWithSQLiteCache(
                cache_enabled=True,
                cache_ttl=STANDARD_TTL,
                db_path=TEST_DB_PATH
            )
            # Set client to be initialized to avoid re-initialization attempts
            self.google_ads_client._initialized = True
            
            # Set client properties
            self.google_ads_client.client_customer_id = TEST_CUSTOMER_ID
            
            # Create a budget service with the mocked client
            self.budget_service = BudgetService(self.google_ads_client)
            
            # Run the test
            yield
            
        # Clean up after test
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
    
    def test_database_initialization(self):
        """Test CF-01: Verify database initialization."""
        # Check that the database was created
        assert os.path.exists(TEST_DB_PATH)
        
        # Connect to the database and check tables
        conn = sqlite3.connect(TEST_DB_PATH)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        # Verify required tables exist
        required_tables = ['api_cache', 'account_kpi_cache', 'campaign_cache', 
                           'keyword_cache', 'search_term_cache', 'budget_cache']
        for table in required_tables:
            assert table in table_names
            
        conn.close()
    
    def test_api_cache_store_retrieve(self):
        """Test CF-01: Basic cache store and retrieve for API responses."""
        # Test data
        test_data = {
            "campaigns": [
                {"id": "1", "name": "Campaign 1", "status": "ENABLED"},
                {"id": "2", "name": "Campaign 2", "status": "PAUSED"}
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        # Cache parameters
        params = {
            'query': "SELECT campaign.id, campaign.name FROM campaign",
            'customer_id': TEST_CUSTOMER_ID,
            'test_param': 'test_value'
        }
        
        # Store data in cache
        cache_key = self.google_ads_client._generate_cache_key("get_campaigns", **params)
        self.google_ads_client._cache_data("get_campaigns", test_data, **params)
        
        # Retrieve data from cache
        cached_data = self.google_ads_client._get_cached_data("get_campaigns", **params)
        
        # Verify data was retrieved correctly
        assert cached_data is not None
        assert cached_data == test_data
        assert len(cached_data["campaigns"]) == 2
        assert cached_data["campaigns"][0]["name"] == "Campaign 1"
    
    def test_cache_key_consistency(self):
        """Test CF-05: Cache key generation consistency."""
        # Test parameters
        params1 = {
            'query': "SELECT campaign.id FROM campaign",
            'customer_id': "1234567890",
            'start_date': "2025-01-01",
            'end_date': "2025-01-31"
        }
        
        params2 = {
            'query': "SELECT campaign.id FROM campaign",
            'customer_id': "1234567890",
            'start_date': "2025-01-01",
            'end_date': "2025-01-31"
        }
        
        params3 = {
            'query': "SELECT campaign.id FROM campaign",
            'customer_id': "1234567890",
            'start_date': "2025-02-01",  # Different date
            'end_date': "2025-02-28"
        }
        
        # Generate keys
        key1 = self.google_ads_client._generate_cache_key("get_campaigns", **params1)
        key2 = self.google_ads_client._generate_cache_key("get_campaigns", **params2)
        key3 = self.google_ads_client._generate_cache_key("get_campaigns", **params3)
        
        # Same parameters should generate same key
        assert key1 == key2
        
        # Different parameters should generate different keys
        assert key1 != key3
    
    def test_cache_expiration(self):
        """Test CF-02: Cache expiration."""
        # Test data
        test_data = {"value": "should_expire"}
        
        # Cache parameters with short TTL
        params = {
            'query': "SELECT test FROM test",
            'customer_id': TEST_CUSTOMER_ID
        }
        
        # Store data in cache with 1 second TTL
        self.google_ads_client.cache_ttl = SHORT_TTL
        self.google_ads_client._cache_data("short_ttl_test", test_data, **params)
        
        # Should be available immediately
        immediate_result = self.google_ads_client._get_cached_data("short_ttl_test", **params)
        assert immediate_result is not None
        assert immediate_result == test_data
        
        # Wait for expiration
        time.sleep(SHORT_TTL + 1)
        
        # Should be expired now
        expired_result = self.google_ads_client._get_cached_data("short_ttl_test", **params)
        assert expired_result is None
        
        # Reset TTL for other tests
        self.google_ads_client.cache_ttl = STANDARD_TTL
    
    def test_customer_specific_caching(self):
        """Test CF-06: Cache with different customer IDs."""
        # Test data for different customers
        test_data_1 = {"value": "customer_1_data"}
        test_data_2 = {"value": "customer_2_data"}
        
        # Common parameters except customer ID
        common_params = {'query': "SELECT test FROM test"}
        
        # Store data for customer 1
        params_1 = {**common_params, 'customer_id': "1111111111"}
        self.google_ads_client._cache_data("customer_test", test_data_1, **params_1)
        
        # Store data for customer 2
        params_2 = {**common_params, 'customer_id': "2222222222"}
        self.google_ads_client._cache_data("customer_test", test_data_2, **params_2)
        
        # Retrieve data for customer 1
        cached_data_1 = self.google_ads_client._get_cached_data("customer_test", **params_1)
        
        # Retrieve data for customer 2
        cached_data_2 = self.google_ads_client._get_cached_data("customer_test", **params_2)
        
        # Verify correct data for each customer
        assert cached_data_1 == test_data_1
        assert cached_data_2 == test_data_2
        assert cached_data_1 != cached_data_2
    
    def test_cache_clearing(self):
        """Test CF-04: Selective and complete cache clearing."""
        # Store data for multiple entity types
        api_data = {"api_data": "test"}
        campaign_data = {"campaign_data": "test"}
        keyword_data = {"keyword_data": "test"}
        
        # Store API cache data
        self.google_ads_client._cache_data("api_test", api_data, query="test", customer_id=TEST_CUSTOMER_ID)
        
        # Store campaign data
        self.db_manager.store_campaign_data(
            customer_id=TEST_CUSTOMER_ID,
            campaign_id="12345",
            campaign_data=json.dumps(campaign_data),
            ttl_seconds=STANDARD_TTL
        )
        
        # Store keyword data
        self.db_manager.store_keyword_data(
            customer_id=TEST_CUSTOMER_ID,
            keyword_id="67890",
            keyword_data=json.dumps(keyword_data),
            ttl_seconds=STANDARD_TTL
        )
        
        # Verify all data is stored
        stats_before = self.db_manager.get_cache_statistics()
        assert stats_before['api_cache_count'] > 0
        assert stats_before['campaign_cache_count'] > 0
        assert stats_before['keyword_cache_count'] > 0
        
        # Clear only campaign cache
        self.db_manager.clear_cache('campaign')
        
        # Verify only campaign cache is cleared
        stats_after_selective = self.db_manager.get_cache_statistics()
        assert stats_after_selective['api_cache_count'] > 0
        assert stats_after_selective['campaign_cache_count'] == 0
        assert stats_after_selective['keyword_cache_count'] > 0
        
        # Clear all cache
        self.db_manager.clear_all_cache()
        
        # Verify all cache is cleared
        stats_after_full = self.db_manager.get_cache_statistics()
        assert stats_after_full['api_cache_count'] == 0
        assert stats_after_full['campaign_cache_count'] == 0
        assert stats_after_full['keyword_cache_count'] == 0
    
    @mock.patch('google_ads.client_with_sqlite_cache.GoogleAdsServiceWithSQLiteCache.get_campaigns')
    def test_cache_hit_integration(self, mock_get_campaigns):
        """Test CF-01 + CF-08: Cache hit integration and tracking."""
        # Mock response for the first call (cache miss)
        mock_campaigns = [
            {"id": "1", "name": "Campaign 1", "status": "ENABLED"},
            {"id": "2", "name": "Campaign 2", "status": "PAUSED"}
        ]
        mock_get_campaigns.return_value = mock_campaigns
        
        # Call the method first time (should be a cache miss)
        with mock.patch('utils.api_tracker.APICallTracker.track_call'):
            result1 = self.google_ads_client.get_campaigns(
                start_date="2025-01-01",
                end_date="2025-01-31",
                customer_id=TEST_CUSTOMER_ID
            )
        
        # Verify result
        assert result1 == mock_campaigns
        
        # Call the method second time (should be a cache hit)
        with mock.patch('utils.api_tracker.APICallTracker.track_call') as mock_tracker:
            mock_context = mock.MagicMock()
            mock_tracker.return_value.__enter__.return_value = mock_context
            
            result2 = self.google_ads_client.get_campaigns(
                start_date="2025-01-01",
                end_date="2025-01-31",
                customer_id=TEST_CUSTOMER_ID
            )
            
            # Verify cache hit was tracked
            mock_context.set_cache_status.assert_called_once_with("HIT")
        
        # Verify result
        assert result2 == mock_campaigns
        
        # Verify get_campaigns was only called once (first time)
        assert mock_get_campaigns.call_count == 1
    
    def test_large_data_caching(self):
        """Test CF-07: Large object caching."""
        # Generate large dataset (1000 items)
        large_data = {
            "items": [{"id": str(i), "value": f"test_{i}", "data": "x" * 100} for i in range(1000)]
        }
        
        # Cache parameters
        params = {
            'query': "SELECT large FROM test",
            'customer_id': TEST_CUSTOMER_ID
        }
        
        # Store large data in cache
        self.google_ads_client._cache_data("large_data_test", large_data, **params)
        
        # Retrieve data from cache
        cached_data = self.google_ads_client._get_cached_data("large_data_test", **params)
        
        # Verify data was retrieved correctly
        assert cached_data is not None
        assert len(cached_data["items"]) == 1000
        assert cached_data["items"][999]["id"] == "999"
    
    def test_cache_invalidation_on_update(self):
        """Test cache invalidation after updates."""
        # Mock budget data
        budget_id = "12345"
        budget_data = {
            "id": budget_id,
            "name": "Test Budget",
            "amount_micros": 1000000
        }
        
        # Store budget data in cache
        self.db_manager.store_budget_data(
            customer_id=TEST_CUSTOMER_ID,
            budget_id=budget_id,
            budget_data=json.dumps(budget_data),
            ttl_seconds=STANDARD_TTL
        )
        
        # Verify budget is in cache
        stats_before = self.db_manager.get_cache_statistics()
        assert stats_before['budget_cache_count'] > 0
        
        # Mock the update_campaign_budget method
        with mock.patch.object(self.google_ads_client, 'update_campaign_budget') as mock_update:
            mock_update.return_value = {"success": True}
            
            # Update the budget
            result = self.budget_service.update_budget(
                customer_id=TEST_CUSTOMER_ID,
                budget_id=budget_id,
                amount_micros=2000000
            )
            
            # Verify update was called
            mock_update.assert_called_once()
            
        # Verify cache was cleared for budgets
        stats_after = self.db_manager.get_cache_statistics()
        assert stats_after['budget_cache_count'] == 0


if __name__ == "__main__":
    pytest.main(["-v", __file__]) 