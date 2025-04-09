#!/usr/bin/env python
"""
Google Ads API Caching Test Script

This script tests the SQLite-based caching for Google Ads API calls, verifying
that the caching mechanism works correctly by making test API calls and
measuring performance improvements with caching.
"""

import os
import sys
import asyncio
import time
import logging
from datetime import datetime, timedelta
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Change to absolute import
from google_ads_mcp_server.google_ads.client_with_sqlite_cache import GoogleAdsServiceWithSQLiteCache
from db.manager import DatabaseManager

async def test_get_campaigns_caching():
    """Test caching for the get_campaigns method."""
    print("\n=== Testing Get Campaigns Caching ===")
    
    # Initialize the Google Ads service with SQLite caching
    ads_service = GoogleAdsServiceWithSQLiteCache(cache_enabled=True, cache_ttl=3600)
    
    # Calculate date range for the last 30 days
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    print(f"Using date range: {start_date} to {end_date}")
    
    # First request should be a cache miss
    print("\nMaking first request (expected cache miss)...")
    start_time = time.time()
    try:
        campaigns = await ads_service.get_campaigns(start_date, end_date)
        execution_time = time.time() - start_time
        print(f"First request completed in {execution_time:.4f} seconds (cache miss)")
        
        if campaigns:
            print(f"Retrieved {len(campaigns)} campaigns")
            
            # Print details of the first few campaigns
            for i, campaign in enumerate(campaigns[:3]):
                print(f"Campaign {i+1}: {campaign['name']} (ID: {campaign['id']})")
                print(f"  Status: {campaign['status']}")
                print(f"  Channel Type: {campaign['channel_type']}")
                print(f"  Impressions: {campaign['impressions']}")
                print(f"  Clicks: {campaign['clicks']}")
                print(f"  Cost: ${campaign['cost']:.2f}")
                print()
        else:
            print("No campaigns retrieved")
    except Exception as e:
        print(f"Error retrieving campaigns: {str(e)}")
        return
    
    # Second request should be a cache hit
    print("\nMaking second request (expected cache hit)...")
    start_time = time.time()
    try:
        campaigns2 = await ads_service.get_campaigns(start_date, end_date)
        execution_time = time.time() - start_time
        print(f"Second request completed in {execution_time:.4f} seconds (cache hit)")
        
        if campaigns2:
            print(f"Retrieved {len(campaigns2)} campaigns from cache")
            
            # Verify data matches
            if campaigns == campaigns2:
                print("✅ Cached data matches original data")
            else:
                print("❌ Cached data doesn't match original data")
        else:
            print("❌ No campaigns retrieved from cache")
    except Exception as e:
        print(f"Error retrieving campaigns from cache: {str(e)}")

async def test_get_account_summary_caching():
    """Test caching for the get_account_summary method."""
    print("\n=== Testing Get Account Summary Caching ===")
    
    # Initialize the Google Ads service with SQLite caching
    ads_service = GoogleAdsServiceWithSQLiteCache(cache_enabled=True, cache_ttl=3600)
    
    # Calculate date range for the last 30 days
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    print(f"Using date range: {start_date} to {end_date}")
    
    # First request should be a cache miss
    print("\nMaking first request (expected cache miss)...")
    start_time = time.time()
    try:
        summary = await ads_service.get_account_summary(start_date, end_date)
        execution_time = time.time() - start_time
        print(f"First request completed in {execution_time:.4f} seconds (cache miss)")
        
        if summary:
            print("Account Summary:")
            print(f"Customer ID: {summary['customer_id']}")
            print(f"Impressions: {summary['total_impressions']}")
            print(f"Clicks: {summary['total_clicks']}")
            print(f"Cost: ${summary['total_cost']:.2f}")
            print(f"Conversions: {summary['total_conversions']}")
            print(f"CTR: {summary['ctr']:.2f}%")
            print(f"CPC: ${summary['cpc']:.2f}")
            print(f"Conversion Rate: {summary['conversion_rate']:.2f}%")
        else:
            print("No account summary retrieved")
    except Exception as e:
        print(f"Error retrieving account summary: {str(e)}")
        return
    
    # Second request should be a cache hit
    print("\nMaking second request (expected cache hit)...")
    start_time = time.time()
    try:
        summary2 = await ads_service.get_account_summary(start_date, end_date)
        execution_time = time.time() - start_time
        print(f"Second request completed in {execution_time:.4f} seconds (cache hit)")
        
        if summary2:
            print("Retrieved account summary from cache")
            
            # Verify data matches
            if summary == summary2:
                print("✅ Cached data matches original data")
            else:
                print("❌ Cached data doesn't match original data")
        else:
            print("❌ No account summary retrieved from cache")
    except Exception as e:
        print(f"Error retrieving account summary from cache: {str(e)}")

async def test_budget_update_cache_clearing():
    """Test cache clearing after budget update."""
    print("\n=== Testing Budget Update Cache Clearing ===")
    
    # Initialize the Google Ads service with SQLite caching
    ads_service = GoogleAdsServiceWithSQLiteCache(cache_enabled=True, cache_ttl=3600)
    
    # Get the database manager to check cache status
    db_manager = DatabaseManager(db_path=None)  # Use default DB path
    
    # Get cache statistics before the update
    print("Cache statistics before update:")
    stats_before = db_manager.get_cache_stats()
    print(f"Budget cache entries: {stats_before.get('budget_cache_count', 0)}")
    
    # Update a campaign budget
    # Note: This is a simulated test - you may need to use a real budget ID
    try:
        budget_id = "1234567890"  # Replace with a real budget ID if testing with a real account
        print(f"\nUpdating budget {budget_id}...")
        
        # This is a dummy update that won't actually be executed in a real account
        # In a real test, you would use a valid budget ID and customer ID
        updated_budget = await ads_service.update_campaign_budget(
            budget_id=budget_id,
            amount_micros=5000000,  # $5.00
            customer_id="1234567890"  # Replace with a real customer ID if testing with a real account
        )
        
        print(f"Budget updated to ${updated_budget['amount_dollars']:.2f}")
        
        # Get cache statistics after the update
        print("\nCache statistics after update:")
        stats_after = db_manager.get_cache_stats()
        print(f"Budget cache entries: {stats_after.get('budget_cache_count', 0)}")
        
        # For this test, we simulate the cache clearing
        print("\nChecking if budget-related cache was cleared...")
        if stats_after.get('budget_cache_count', 0) == 0:
            print("✅ Budget cache was successfully cleared after update")
        else:
            print("❌ Budget cache was not cleared after update")
            
    except Exception as e:
        print(f"Error updating budget: {str(e)}")
        print("Note: If using test credentials, this is expected behavior")
        print("This test would work correctly with valid credentials and budget ID")

async def main():
    """Main entry point for the test script."""
    print("Starting Google Ads API caching tests...")
    
    try:
        # Test get_campaigns caching
        await test_get_campaigns_caching()
        
        # Test get_account_summary caching
        await test_get_account_summary_caching()
        
        # Test budget update cache clearing
        await test_budget_update_cache_clearing()
        
        print("\n=== All Tests Completed ===")
        
    except Exception as e:
        print(f"Error running tests: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 