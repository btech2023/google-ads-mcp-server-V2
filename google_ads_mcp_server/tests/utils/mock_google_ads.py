import logging
from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

DEFAULT_CUSTOMER_ID = "7788990011" # Shared default for mocks

class MockBatchManager(MagicMock):
    """Mock implementation of the BatchManager class for testing."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.execute_batch = AsyncMock()
        self.execute_batch.return_value = [
            {"status": "SUCCESS", "budget_id": "budget1", "applied_amount": 50.0},
            {"status": "SUCCESS", "budget_id": "budget2", "applied_amount": 100.0}
        ]
        self.add_budget_update = MagicMock()
        self.reset_batch = MagicMock()

def create_mock_google_ads_client(cache_enabled: bool = True, cache_ttl: int = 3600) -> MagicMock:
    """
    Create a reusable mock Google Ads client for testing without actual API access.
    
    Args:
        cache_enabled: Whether the mock client should simulate caching.
        cache_ttl: The TTL for the mock cache.
        
    Returns:
        Mock GoogleAdsClient instance
    """
    logger.info("Creating mock Google Ads client for testing...")
    
    # Create a mock client instance
    mock_client = MagicMock()
    mock_client.cache_enabled = cache_enabled
    mock_client.cache_ttl = cache_ttl
    mock_client.developer_token = "FAKE_TOKEN"
    mock_client.client_id = "FAKE_CLIENT_ID"
    mock_client.client_secret = "FAKE_CLIENT_SECRET"
    mock_client.refresh_token = "FAKE_REFRESH_TOKEN"
    mock_client.login_customer_id = "FAKE_LOGIN_ID"
    
    # Mock asynchronous methods
    mock_client.get_campaigns = AsyncMock()
    mock_client.get_account_summary = AsyncMock()
    mock_client.get_keywords = AsyncMock()
    mock_client.list_accessible_accounts = AsyncMock()
    mock_client.update_campaign_budget = AsyncMock()
    mock_client.update_campaign_budgets_batch = AsyncMock()
    mock_client.search = AsyncMock() # Generic search mock
    mock_client._execute_query = AsyncMock() # Internal query mock
    mock_client.get_campaign_budgets = AsyncMock() # Mock required by BudgetService
    
    # Setup some default mock return data (can be overridden in tests)
    mock_client.get_campaigns.return_value = [
        {"id": "1", "name": "Campaign 1", "status": "ENABLED", "channel_type": "SEARCH",
         "impressions": 30000, "clicks": 1500, "cost": 1500.0, "conversions": 75},
        {"id": "2", "name": "Campaign 2", "status": "ENABLED", "channel_type": "DISPLAY",
         "impressions": 25000, "clicks": 1250, "cost": 1250.0, "conversions": 60}
    ]
    
    mock_client.get_account_summary.return_value = {
        "customer_id": DEFAULT_CUSTOMER_ID,
        "date_range": {"start_date": "2025-05-01", "end_date": "2025-05-30"},
        "total_impressions": 100000, "total_clicks": 5000, "total_cost": 5000.0,
        "total_conversions": 250, "total_conversion_value": 12500.0,
        "ctr": 5.0, "cpc": 1.0, "conversion_rate": 5.0, "cost_per_conversion": 20.0
    }
    
    mock_client.get_keywords.return_value = [
        {"id": "101", "text": "test keyword 1", "match_type": "EXACT", "status": "ENABLED"},
        {"id": "102", "text": "test keyword 2", "match_type": "PHRASE", "status": "ENABLED"}
    ]
    
    mock_client.list_accessible_accounts.return_value = [
        {"customer_id": DEFAULT_CUSTOMER_ID, "descriptive_name": "Mock Account 1"},
        {"customer_id": "1122334455", "descriptive_name": "Mock Account 2"}
    ]

    mock_client.update_campaign_budget.return_value = {"success": True, "applied_amount": 50.0}
    
    # Fix: Return a list of dictionaries with status field for batch operations
    mock_client.update_campaign_budgets_batch.return_value = [
        {"status": "SUCCESS", "budget_id": "budget1", "applied_amount": 50.0},
        {"status": "SUCCESS", "budget_id": "budget2", "applied_amount": 100.0}
    ]
    
    mock_client.search.return_value = MagicMock() # Return a mock iterator
    mock_client._execute_query.return_value = MagicMock()
    mock_client.get_campaign_budgets.return_value = [ # Default return for get_campaign_budgets
        {"id": "budget1", "name": "Budget 1", "amount_micros": 50000000, "status": "ENABLED"},
        {"id": "budget2", "name": "Budget 2", "amount_micros": 100000000, "status": "ENABLED"}
    ]
    
    return mock_client 