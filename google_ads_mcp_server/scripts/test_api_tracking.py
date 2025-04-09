#!/usr/bin/env python
"""
Test API Tracking

This script tests the API tracking functionality by making a few 
Google Ads API calls and then analyzing the call patterns.
"""

import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime, timedelta
import random
import time
from unittest.mock import MagicMock

# Use absolute imports
from google_ads_mcp_server.google_ads.client_with_sqlite_cache import GoogleAdsServiceWithSQLiteCache
from google_ads_mcp_server.utils.api_tracker import ApiCallTracker
from google_ads_mcp_server.db.factory import get_database_manager
from google_ads_mcp_server.utils.logging import configure_logging, get_logger
from scripts.analyze_api_usage import generate_report

# Configure logging
configure_logging(console_level=logging.INFO)
logger = get_logger(__name__)

async def run_test_calls(client, customer_id, days_back=30, cache_enabled=True):
    """Run a series of test API calls to generate tracking data."""
    # Calculate date range
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    logger.info(f"Making API calls for date range {start_date} to {end_date}")
    logger.info(f"Caching {'enabled' if cache_enabled else 'disabled'}")
    
    # Make a series of API calls
    calls = [
        # First call - should be a cache miss
        client.get_campaigns(start_date, end_date, customer_id),
        # Second call - should be a cache hit
        client.get_campaigns(start_date, end_date, customer_id),
        # Different API call - different method
        client.get_account_summary(start_date, end_date, customer_id),
        # Same API call again - should be cache hit
        client.get_account_summary(start_date, end_date, customer_id),
        # Slightly different date range - should be cache miss
        client.get_campaigns(
            (datetime.now() - timedelta(days=days_back+5)).strftime('%Y-%m-%d'),
            end_date,
            customer_id
        )
    ]
    
    # Execute all calls concurrently
    results = await asyncio.gather(*calls, return_exceptions=True)
    
    # Log results
    success_count = 0
    error_count = 0
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Call {i+1} failed: {type(result).__name__}: {str(result)}")
            error_count += 1
        else:
            logger.info(f"Call {i+1} succeeded")
            success_count += 1
    
    logger.info(f"Completed {len(calls)} API calls: {success_count} succeeded, {error_count} failed")
    return success_count, error_count

async def main(args):
    """Main function."""
    # Initialize the Google Ads client
    client = GoogleAdsServiceWithSQLiteCache(
        cache_enabled=args.use_cache,
        cache_ttl=args.cache_ttl
    )
    
    # Run the test calls
    success_count, error_count = await run_test_calls(
        client=client, 
        customer_id=args.customer_id,
        days_back=args.days_back,
        cache_enabled=args.use_cache
    )
    
    if success_count == 0:
        logger.error("All API calls failed. Check credentials and permissions.")
        return 1
    
    # Generate and display API usage report
    report = generate_report(
        hours=args.hours,
        format_type=args.format,
        db_path=None  # Use default path
    )
    
    print("\n" + "="*80)
    print("API USAGE REPORT")
    print("="*80)
    print(report)
    
    return 0

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Test API tracking functionality.')
    
    parser.add_argument('--customer-id', type=str, default=None,
                        help='Google Ads customer ID to use (default: use from environment variables)')
    parser.add_argument('--use-cache', action='store_true', default=True,
                        help='Enable caching (default: True)')
    parser.add_argument('--no-cache', dest='use_cache', action='store_false',
                        help='Disable caching')
    parser.add_argument('--cache-ttl', type=int, default=3600,
                        help='Cache time-to-live in seconds (default: 3600)')
    parser.add_argument('--days-back', type=int, default=30,
                        help='Number of days to look back for campaign data (default: 30)')
    parser.add_argument('--hours', type=int, default=1,
                        help='Number of hours to analyze in the report (default: 1)')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown',
                        help='Output format for the report (default: markdown)')
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    sys.exit(asyncio.run(main(args))) 