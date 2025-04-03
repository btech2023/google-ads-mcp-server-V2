#!/usr/bin/env python

import os
import sys
import logging
from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class AdGroupService:
    """Service for managing Google Ads ad groups."""
    
    def __init__(self, google_ads_service):
        """
        Initialize the Ad Group service.
        
        Args:
            google_ads_service: The Google Ads service instance
        """
        self.google_ads_service = google_ads_service
        self.ga_service = google_ads_service.client.get_service("GoogleAdsService")
        logger.info("AdGroupService initialized")
    
    async def get_ad_groups(self, customer_id: str, campaign_id: Optional[str] = None, 
                           status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get ad groups for a customer, optionally filtered by campaign_id and status.
        
        Args:
            customer_id: Google Ads customer ID
            campaign_id: Optional campaign ID to filter by
            status_filter: Optional filter for ad group status (ENABLED, PAUSED, REMOVED)
            
        Returns:
            List of ad group data with metrics
        """
        logger.info(f"Getting ad groups for customer ID {customer_id}")
        
        # Calculate default date range (last 30 days)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Get data from the Google Ads service
        ad_groups = await self.google_ads_service.get_ad_groups(
            start_date=start_date,
            end_date=end_date,
            campaign_id=campaign_id,
            customer_id=customer_id
        )
        
        # Apply status filter if provided
        if status_filter:
            ad_groups = [ad_group for ad_group in ad_groups if ad_group['status'] == status_filter]
            
        logger.info(f"Retrieved {len(ad_groups)} ad groups")
        return ad_groups
    
    async def get_ad_group_performance(self, customer_id: str, ad_group_id: str, 
                                      start_date: Optional[str] = None, 
                                      end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance metrics for a specific ad group.
        
        Args:
            customer_id: Google Ads customer ID
            ad_group_id: Ad group ID
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Dictionary with ad group performance data
        """
        logger.info(f"Getting performance data for ad group {ad_group_id}")
        
        # Calculate default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Get daily stats for the ad group
        stats = await self.google_ads_service.get_ad_group_daily_stats(
            ad_group_id=ad_group_id,
            start_date=start_date,
            end_date=end_date,
            customer_id=customer_id
        )
        
        # Calculate totals for the period
        performance = {
            "ad_group_id": ad_group_id,
            "start_date": start_date,
            "end_date": end_date,
            "impressions": sum(day['impressions'] for day in stats),
            "clicks": sum(day['clicks'] for day in stats),
            "cost": sum(day['cost'] for day in stats),
            "conversions": sum(day['conversions'] for day in stats),
            "conversion_value": sum(day['conversion_value'] for day in stats),
            "daily_stats": stats
        }
        
        # Calculate derived metrics
        if performance['impressions'] > 0:
            performance['ctr'] = (performance['clicks'] / performance['impressions']) * 100
        else:
            performance['ctr'] = 0
            
        if performance['clicks'] > 0:
            performance['cpc'] = performance['cost'] / performance['clicks']
        else:
            performance['cpc'] = 0
            
        if performance['cost'] > 0:
            performance['roas'] = performance['conversion_value'] / performance['cost']
        else:
            performance['roas'] = 0
        
        return performance
    
    async def create_ad_group(self, customer_id: str, campaign_id: str, name: str, 
                             status: str = "ENABLED", cpc_bid_micros: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a new ad group within a campaign.
        
        Args:
            customer_id: Google Ads customer ID
            campaign_id: Campaign ID to create the ad group in
            name: Name of the ad group
            status: Ad group status (ENABLED, PAUSED, REMOVED)
            cpc_bid_micros: CPC bid amount in micros (1/1,000,000 of the account currency)
            
        Returns:
            Dictionary with created ad group details
        """
        logger.info(f"Creating ad group '{name}' in campaign {campaign_id}")
        
        result = await self.google_ads_service.create_ad_group(
            campaign_id=campaign_id,
            name=name,
            status=status,
            cpc_bid_micros=cpc_bid_micros,
            customer_id=customer_id
        )
        
        return result
    
    async def update_ad_group(self, customer_id: str, ad_group_id: str, 
                             name: Optional[str] = None, status: Optional[str] = None, 
                             cpc_bid_micros: Optional[int] = None) -> Dict[str, Any]:
        """
        Update an existing ad group's attributes.
        
        Args:
            customer_id: Google Ads customer ID
            ad_group_id: Ad group ID to update
            name: New name for the ad group (optional)
            status: New status for the ad group (optional)
            cpc_bid_micros: New CPC bid amount in micros (optional)
            
        Returns:
            Dictionary with updated ad group details
        """
        logger.info(f"Updating ad group {ad_group_id}")
        
        # Validate status if provided
        if status and status not in ["ENABLED", "PAUSED", "REMOVED"]:
            raise ValueError(f"Invalid status: {status}. Must be one of: ENABLED, PAUSED, REMOVED")
        
        result = await self.google_ads_service.update_ad_group(
            ad_group_id=ad_group_id,
            name=name,
            status=status,
            cpc_bid_micros=cpc_bid_micros,
            customer_id=customer_id
        )
        
        return result

def main():
    # Load environment variables
    if os.path.exists(".env"):
        load_dotenv(".env")
        logger.info("Loaded environment variables from ./.env")
    
    # Check required environment variables
    required_vars = [
        "GOOGLE_ADS_DEVELOPER_TOKEN", 
        "GOOGLE_ADS_CLIENT_ID",
        "GOOGLE_ADS_CLIENT_SECRET",
        "GOOGLE_ADS_REFRESH_TOKEN",
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID"
    ]
    
    for var in required_vars:
        if not os.environ.get(var):
            logger.error(f"Missing required environment variable: {var}")
            return 1
    
    # Get customer IDs
    login_customer_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    if '-' in login_customer_id:
        login_customer_id = login_customer_id.replace('-', '')
    
    client_customer_id = os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID")
    if client_customer_id and '-' in client_customer_id:
        client_customer_id = client_customer_id.replace('-', '')
    
    if not client_customer_id:
        client_customer_id = login_customer_id
    
    logger.info(f"Using login customer ID: {login_customer_id}")
    logger.info(f"Using client customer ID: {client_customer_id}")
    
    try:
        # Initialize the Google Ads client
        client = GoogleAdsClient.load_from_env()
        
        # Create a Google Ads service client
        google_ads_service = client.get_service("GoogleAdsService")
        
        # Create a simple query that doesn't use metrics.conversion_value
        query = """
        SELECT
          campaign.id,
          campaign.name,
          campaign.status
        FROM campaign
        LIMIT 10
        """
        
        # Execute the search request
        search_request = client.get_type("SearchGoogleAdsRequest")
        search_request.customer_id = client_customer_id
        search_request.query = query
        
        logger.info("Executing Google Ads query...")
        response = google_ads_service.search(search_request)
        
        # Process the results
        campaign_count = 0
        for row in response:
            campaign = row.campaign
            campaign_count += 1
            logger.info(f"Campaign ID: {campaign.id}, Name: {campaign.name}, Status: {campaign.status.name}")
        
        logger.info(f"Found {campaign_count} campaigns")
        
        return 0
        
    except GoogleAdsException as ex:
        logger.error("Google Ads API Error:")
        for error in ex.failure.errors:
            logger.error(f"Error message: {error.message}")
        return 1
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 