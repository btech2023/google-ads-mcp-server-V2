#!/usr/bin/env python
"""
Test script for Google Ads client with MCC and child account functionality.
This script validates caching, account hierarchy, and improved functionality.
"""

import os
import asyncio
import json
import time
import logging
from dotenv import load_dotenv
from google_ads_client import GoogleAdsService, GoogleAdsClientError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test-google-ads")

# Load environment variables from parent directory's .env file
parent_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(parent_env_path)

async def test_list_accounts():
    """Test listing accounts accessible from the MCC account."""
    try:
        service = GoogleAdsService()
        
        # First call - should hit API
        start_time = time.time()
        accounts = await service.list_accessible_accounts()
        first_call_time = time.time() - start_time
        
        print("\n=== ACCESSIBLE ACCOUNTS ===")
        print(f"Total accounts: {len(accounts)}\n")
        print(f"First call execution time: {first_call_time:.3f} seconds")
        
        for account in accounts:
            print(f"ID: {account['id']}, Name: {account['name']}")
        
        # Second call - should use cache
        start_time = time.time()
        accounts_cached = await service.list_accessible_accounts()
        second_call_time = time.time() - start_time
        
        print(f"\nSecond call execution time: {second_call_time:.3f} seconds")
        print(f"Cache performance improvement: {first_call_time / second_call_time:.1f}x faster")
            
        return accounts
    except GoogleAdsClientError as e:
        logger.error(f"Failed to list accounts: {str(e)}")
        return []

async def test_get_campaigns(customer_id=None):
    """Test getting campaigns for a specific customer ID."""
    try:
        service = GoogleAdsService()
        
        # Use a 30-day date range
        start_date = "2024-02-17"
        end_date = "2024-03-17"
        
        # First call - should hit API
        start_time = time.time()
        campaigns = await service.get_campaigns(start_date, end_date, customer_id)
        first_call_time = time.time() - start_time
        
        print(f"\n=== CAMPAIGNS FOR CUSTOMER {customer_id or 'default'} ===")
        print(f"Total campaigns: {len(campaigns)}")
        print(f"First call execution time: {first_call_time:.3f} seconds\n")
        
        for campaign in campaigns[:5]:  # Show first 5 campaigns
            print(f"ID: {campaign['id']}, Name: {campaign['name']}, Cost: ${campaign['cost']:.2f}")
        
        if len(campaigns) > 5:
            print(f"... and {len(campaigns) - 5} more campaigns")
        
        # Second call - should use cache
        start_time = time.time()
        campaigns_cached = await service.get_campaigns(start_date, end_date, customer_id)
        second_call_time = time.time() - start_time
        
        print(f"\nSecond call execution time: {second_call_time:.3f} seconds")
        print(f"Cache performance improvement: {first_call_time / second_call_time:.1f}x faster")
            
    except GoogleAdsClientError as e:
        logger.error(f"Failed to get campaigns: {str(e)}")

async def test_get_account_summary(customer_id=None):
    """Test getting account summary for a specific customer ID."""
    try:
        service = GoogleAdsService()
        
        # Use a 30-day date range
        start_date = "2024-02-17"
        end_date = "2024-03-17"
        
        # First call - should hit API
        start_time = time.time()
        summary = await service.get_account_summary(start_date, end_date, customer_id)
        first_call_time = time.time() - start_time
        
        print(f"\n=== ACCOUNT SUMMARY FOR CUSTOMER {customer_id or 'default'} ===")
        print(f"Date range: {summary['date_range']['start_date']} to {summary['date_range']['end_date']}")
        print(f"First call execution time: {first_call_time:.3f} seconds\n")
        
        print(f"Total impressions: {int(summary['total_impressions']):,d}")
        print(f"Total clicks: {int(summary['total_clicks']):,d}")
        print(f"Total cost: ${summary['total_cost']:,.2f}")
        print(f"CTR: {summary['ctr']:.2f}%")
        
        # Second call - should use cache
        start_time = time.time()
        summary_cached = await service.get_account_summary(start_date, end_date, customer_id)
        second_call_time = time.time() - start_time
        
        print(f"\nSecond call execution time: {second_call_time:.3f} seconds")
        print(f"Cache performance improvement: {first_call_time / second_call_time:.1f}x faster")
        
    except GoogleAdsClientError as e:
        logger.error(f"Failed to get account summary: {str(e)}")

async def test_get_account_hierarchy(customer_id=None):
    """Test getting account hierarchy for a specific customer ID."""
    try:
        service = GoogleAdsService()
        
        # First call - should hit API
        start_time = time.time()
        hierarchy = await service.get_account_hierarchy(customer_id)
        first_call_time = time.time() - start_time
        
        print(f"\n=== ACCOUNT HIERARCHY FOR CUSTOMER {customer_id or 'default'} ===")
        print(f"Root account: {hierarchy.get('name', 'Unknown')} ({hierarchy['id']})")
        print(f"First call execution time: {first_call_time:.3f} seconds\n")
        
        print(f"Child accounts: {len(hierarchy.get('children', []))}")
        
        # Second call - should use cache
        start_time = time.time()
        hierarchy_cached = await service.get_account_hierarchy(customer_id)
        second_call_time = time.time() - start_time
        
        print(f"\nSecond call execution time: {second_call_time:.3f} seconds")
        print(f"Cache performance improvement: {first_call_time / second_call_time:.1f}x faster")
        
        return hierarchy
        
    except GoogleAdsClientError as e:
        logger.error(f"Failed to get account hierarchy: {str(e)}")
        return None

async def test_cache_clearing():
    """Test cache clearing functionality."""
    try:
        service = GoogleAdsService()
        
        print("\n=== TESTING CACHE CLEARING ===")
        
        # First call to fill cache
        await service.list_accessible_accounts()
        
        # Check cache size
        cache_size_before = len(service.cache)
        print(f"Cache entries before clearing: {cache_size_before}")
        
        # Clear cache
        service._clear_cache()
        
        # Check cache size after clearing
        cache_size_after = len(service.cache)
        print(f"Cache entries after clearing: {cache_size_after}")
        
        # Verify cache was cleared
        if cache_size_after == 0:
            print("Cache clearing successful!")
        else:
            print("Cache clearing failed!")
            
    except Exception as e:
        logger.error(f"Failed to test cache clearing: {str(e)}")

async def main():
    """Run all tests."""
    try:
        print("\n*** GOOGLE ADS CLIENT TEST SCRIPT ***")
        print("This script validates caching, account hierarchy, and improved functionality.")
        
        # Test 1: List all accessible accounts
        accounts = await test_list_accounts()
        
        # Test 2: Get campaigns for the default account
        await test_get_campaigns()
        
        # Test 3: Get account summary for the default account
        await test_get_account_summary()
        
        # Test 4: Get account hierarchy
        hierarchy = await test_get_account_hierarchy()
        
        # Test 5: Test cache clearing
        await test_cache_clearing()
        
        # If we found accessible accounts and a hierarchy, test with a child account
        if accounts and hierarchy and hierarchy.get('children'):
            # Use the first child account
            child_account = hierarchy['children'][0]
            child_account_id = child_account['id']
            
            print(f"\n\n*** TESTING WITH CHILD ACCOUNT: {child_account.get('name', 'Unknown')} ({child_account_id}) ***")
            
            # Test campaigns for a child account
            await test_get_campaigns(child_account_id)
            
            # Test account summary for a child account
            await test_get_account_summary(child_account_id)
    
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
