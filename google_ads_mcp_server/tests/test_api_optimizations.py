#!/usr/bin/env python
"""
API Optimizations Test Suite

This module contains tests for the API optimizations in the Google Ads MCP Server,
focusing on GAQL query optimization, pagination, and batch processing.
"""

import os
import sys
import pytest
import time
import json
import logging
from unittest import mock
from typing import List, Dict, Any
import asyncio

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_ads_mcp_server.google_ads.client_with_sqlite_cache import GoogleAdsServiceWithSQLiteCache
from google_ads_mcp_server.google_ads.batch_operations import BatchManager, OperationType
from google_ads_mcp_server.google_ads.campaigns import CampaignService
from utils.performance_profiler import PerformanceProfiler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api-optimizations-test")

# Test configuration
TEST_CUSTOMER_ID = "1234567890"


class TestApiOptimizations:
    """Test suite for API optimization functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test."""
        # Mock the Google Ads client for testing
        with mock.patch('google_ads.client_base.GoogleAdsClient.initialize'):
            # Create a Google Ads client
            self.google_ads_client = GoogleAdsServiceWithSQLiteCache(cache_enabled=False)
            # Set client to be initialized
            self.google_ads_client._initialized = True
            # Set client properties
            self.google_ads_client.client_customer_id = TEST_CUSTOMER_ID
            
            # Setup mock for the _execute_query method
            self.execute_query_patch = mock.patch.object(
                self.google_ads_client, 
                '_execute_query', 
                side_effect=self._mock_execute_query
            )
            self.mock_execute_query = self.execute_query_patch.start()
            
            # Setup mock for GoogleAdsClient.client
            self.client_patch = mock.patch.object(
                self.google_ads_client,
                'client',
                return_value=mock.MagicMock()
            )
            self.mock_client = self.client_patch.start()
            
            yield
            
            # Cleanup
            self.execute_query_patch.stop()
            self.client_patch.stop()
    
    def _mock_execute_query(self, method_name, query, customer_id, **kwargs):
        """Mock implementation of _execute_query that records the query."""
        # Store the query for inspection
        self.last_query = query
        self.last_kwargs = kwargs
        
        # Extract the FROM clause to determine what kind of data to return
        from_resource = query.split("FROM")[1].strip().split()[0]
        
        # Return mocked data based on the resource type
        if from_resource == "campaign":
            return self._generate_mock_campaigns(10)
        elif from_resource == "ad_group":
            return self._generate_mock_ad_groups(10)
        elif from_resource == "keyword_view":
            return self._generate_mock_keywords(10)
        else:
            return []
    
    def _generate_mock_campaigns(self, count: int) -> List[Dict[str, Any]]:
        """Generate mock campaign data."""
        return [
            {
                "id": str(i),
                "name": f"Campaign {i}",
                "status": "ENABLED" if i % 2 == 0 else "PAUSED",
                "channel_type": "SEARCH",
                "impressions": 1000 * i,
                "clicks": 100 * i,
                "cost": 50.0 * i,
                "conversions": 10 * i,
                "conversion_value": 500.0 * i
            }
            for i in range(1, count + 1)
        ]
    
    def _generate_mock_ad_groups(self, count: int) -> List[Dict[str, Any]]:
        """Generate mock ad group data."""
        return [
            {
                "id": str(i),
                "name": f"Ad Group {i}",
                "status": "ENABLED" if i % 2 == 0 else "PAUSED",
                "campaign_id": str(i % 3 + 1),
                "impressions": 500 * i,
                "clicks": 50 * i,
                "cost": 25.0 * i,
                "conversions": 5 * i,
                "conversion_value": 250.0 * i
            }
            for i in range(1, count + 1)
        ]
    
    def _generate_mock_keywords(self, count: int) -> List[Dict[str, Any]]:
        """Generate mock keyword data."""
        return [
            {
                "id": str(i),
                "text": f"keyword {i}",
                "match_type": "EXACT" if i % 3 == 0 else "PHRASE" if i % 3 == 1 else "BROAD",
                "status": "ENABLED" if i % 2 == 0 else "PAUSED",
                "ad_group": {
                    "id": str(i % 5 + 1),
                    "name": f"Ad Group {i % 5 + 1}"
                },
                "campaign": {
                    "id": str(i % 3 + 1),
                    "name": f"Campaign {i % 3 + 1}"
                },
                "metrics": {
                    "impressions": 100 * i,
                    "clicks": 10 * i,
                    "cost": 5.0 * i,
                    "conversions": 1 * i,
                    "conversion_value": 50.0 * i,
                    "average_cpc": 0.5 * i
                }
            }
            for i in range(1, count + 1)
        ]
    
    def test_gaql_field_selection_optimization(self):
        """Test AO-01: GAQL field selection optimization."""
        # Call the optimized get_campaigns method
        self.google_ads_client.get_campaigns(
            start_date="2025-01-01",
            end_date="2025-01-31",
            customer_id=TEST_CUSTOMER_ID
        )
        
        # Get the executed query
        query = self.last_query
        
        # Verify field selection optimization
        assert "SELECT" in query
        assert "campaign.id" in query
        assert "campaign.name" in query
        assert "campaign.status" in query
        assert "campaign.advertising_channel_type" in query
        assert "metrics.impressions" in query
        assert "metrics.clicks" in query
        assert "metrics.cost_micros" in query
        
        # Verify only necessary fields are selected
        # These fields shouldn't be in the query unless they're actually used
        assert "campaign.app_campaign_setting" not in query
        assert "campaign.bidding_strategy" not in query
        assert "metrics.active_view_cpm" not in query
    
    def test_gaql_filter_optimization(self):
        """Test AO-02: GAQL filtering optimization."""
        # Call the optimized get_campaigns method
        self.google_ads_client.get_campaigns(
            start_date="2025-01-01",
            end_date="2025-01-31",
            customer_id=TEST_CUSTOMER_ID
        )
        
        # Get the executed query
        query = self.last_query
        
        # Verify filter optimization
        assert "WHERE" in query
        assert "segments.date BETWEEN" in query
        assert "campaign.status != 'REMOVED'" in query
        assert "metrics.impressions > 0" in query
    
    @mock.patch('google_ads.client_with_sqlite_cache.GoogleAdsServiceWithSQLiteCache._execute_query')
    def test_pagination_implementation(self, mock_execute_query):
        """Test AO-03: Pagination for large datasets."""
        # Setup mock to return a large dataset
        large_keywords = self._generate_mock_keywords(100)
        mock_execute_query.return_value = large_keywords
        
        # Call the get_keywords method with pagination
        keywords = self.google_ads_client.get_keywords(
            start_date="2025-01-01",
            end_date="2025-01-31",
            customer_id=TEST_CUSTOMER_ID
        )
        
        # Verify pagination was used
        kwargs = mock_execute_query.call_args[1]
        assert kwargs.get('use_paging') is True
        assert kwargs.get('page_size') == 5000  # Default page size for keywords
        
        # Verify all data was retrieved
        assert len(keywords) == len(large_keywords)
    
    @mock.patch('google_ads.batch_operations.BatchManager.execute_batch')
    def test_batch_budget_updates(self, mock_execute_batch):
        """Test AO-04: Batch budget updates."""
        # Setup mock to return success for all operations
        mock_execute_batch.return_value = [
            {"operation_id": f"budget_update_{i}", "status": "SUCCESS"}
            for i in range(1, 6)
        ]
        
        # Create batch with multiple budget updates
        updates = [
            {"budget_id": str(i), "amount_micros": 1000000 * i}
            for i in range(1, 6)
        ]
        
        # Execute batch update
        results = self.google_ads_client.update_campaign_budgets_batch(
            updates=updates,
            customer_id=TEST_CUSTOMER_ID
        )
        
        # Verify batch execution was called
        mock_execute_batch.assert_called_once()
        
        # Verify all operations succeeded
        assert len(results) == 5
        for result in results:
            assert result["status"] == "SUCCESS"
    
    def test_batch_operation_creation(self):
        """Test AO-05: Batch operation creation and grouping."""
        # Create a batch manager
        batch = self.google_ads_client.create_batch()
        
        # Add different types of operations
        batch.add_campaign_budget_update(
            budget_id="12345",
            amount_micros=1000000,
            customer_id=TEST_CUSTOMER_ID
        )
        
        batch.add_ad_group_update(
            ad_group_id="67890",
            updates={"status": "PAUSED"},
            customer_id=TEST_CUSTOMER_ID
        )
        
        batch.add_keyword_update(
            keyword_id="98765",
            updates={"status": "ENABLED"},
            customer_id=TEST_CUSTOMER_ID
        )
        
        # Verify operations were added correctly
        assert len(batch.operations) == 3
        
        # Check operation types
        operation_types = [op.operation_type for op in batch.operations]
        assert OperationType.CAMPAIGN_BUDGET in operation_types
        assert OperationType.AD_GROUP in operation_types
        assert OperationType.KEYWORD in operation_types
        
        # Check operation data
        budget_op = next(op for op in batch.operations if op.operation_type == OperationType.CAMPAIGN_BUDGET)
        assert budget_op.operation_data["budget_id"] == "12345"
        assert budget_op.operation_data["amount_micros"] == 1000000
        
        ad_group_op = next(op for op in batch.operations if op.operation_type == OperationType.AD_GROUP)
        assert ad_group_op.operation_data["ad_group_id"] == "67890"
        assert ad_group_op.operation_data["updates"]["status"] == "PAUSED"
        
        keyword_op = next(op for op in batch.operations if op.operation_type == OperationType.KEYWORD)
        assert keyword_op.operation_data["keyword_id"] == "98765"
        assert keyword_op.operation_data["updates"]["status"] == "ENABLED"
    
    @mock.patch('google_ads.client_with_sqlite_cache.GoogleAdsServiceWithSQLiteCache.update_campaign_budget')
    def test_batch_vs_individual_performance(self, mock_update_budget):
        """Test AO-03: Batch vs. individual operations performance."""
        # Mock the update_campaign_budget method
        mock_update_budget.return_value = {"success": True}
        
        # Setup test data - 10 budget updates
        budget_updates = [
            {"budget_id": str(i), "amount_micros": 1000000 * i}
            for i in range(1, 11)
        ]
        
        # Measure individual updates
        with PerformanceProfiler() as profiler:
            for update in budget_updates:
                self.google_ads_client.update_campaign_budget(
                    budget_id=update["budget_id"],
                    amount_micros=update["amount_micros"],
                    customer_id=TEST_CUSTOMER_ID
                )
        individual_time = profiler.execution_time
        
        # Reset mock
        mock_update_budget.reset_mock()
        
        # Mock batch execution to simulate success
        with mock.patch.object(
            BatchManager, 
            'execute_batch', 
            return_value=[{"status": "SUCCESS"} for _ in range(10)]
        ):
            # Measure batch update
            with PerformanceProfiler() as profiler:
                self.google_ads_client.update_campaign_budgets_batch(
                    updates=budget_updates,
                    customer_id=TEST_CUSTOMER_ID
                )
            batch_time = profiler.execution_time
        
        # Verify batch performance is better (should be at least 2x faster)
        assert batch_time < individual_time / 2
        
        # Log performance improvement
        improvement = ((individual_time - batch_time) / individual_time) * 100
        logger.info(f"Batch processing is {improvement:.2f}% faster than individual operations")
    
    def test_optimized_get_keywords(self):
        """Test AO-08: Optimized get_keywords implementation."""
        # Call the optimized get_keywords method
        keywords = self.google_ads_client.get_keywords(
            campaign_id="12345",
            start_date="2025-01-01",
            end_date="2025-01-31",
            customer_id=TEST_CUSTOMER_ID
        )
        
        # Get the executed query
        query = self.last_query
        
        # Verify query optimization
        assert "SELECT" in query
        assert "ad_group_criterion.criterion_id" in query
        assert "ad_group_criterion.keyword.text" in query
        assert "ad_group_criterion.keyword.match_type" in query
        assert "ad_group_criterion.status" in query
        assert "ad_group.id" in query
        assert "ad_group.name" in query
        assert "campaign.id" in query
        assert "campaign.name" in query
        assert "metrics.impressions" in query
        assert "metrics.clicks" in query
        assert "metrics.cost_micros" in query
        
        # Verify filtering
        assert "WHERE" in query
        assert "segments.date BETWEEN" in query
        assert "ad_group.campaign = '12345'" in query
        assert "ad_group_criterion.status != 'REMOVED'" in query
        
        # Verify ordering
        assert "ORDER BY metrics.impressions DESC" in query
        
        # Verify pagination
        assert self.last_kwargs.get('use_paging') is True
        assert self.last_kwargs.get('page_size') is not None
        
        # Verify returned data structure
        assert isinstance(keywords, list)
        if keywords:
            keyword = keywords[0]
            assert "id" in keyword
            assert "text" in keyword
            assert "match_type" in keyword
            assert "status" in keyword
            assert "ad_group" in keyword
            assert "campaign" in keyword
            assert "metrics" in keyword


if __name__ == "__main__":
    pytest.main(["-v", __file__]) 