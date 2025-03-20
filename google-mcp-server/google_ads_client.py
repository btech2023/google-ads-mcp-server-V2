#!/usr/bin/env python
"""
Google Ads API Client for MCP Server
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Import Google Ads client
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

class GoogleAdsClientError(Exception):
    """Exception raised for errors in the GoogleAdsClient."""
    pass

class GoogleAdsService:
    """Service for interacting with the Google Ads API."""

    def __init__(self):
        """Initialize the Google Ads service using environment variables."""
        try:
            # Configure Google Ads client
            config = {
                "developer_token": os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN"),
                "client_id": os.environ.get("GOOGLE_ADS_CLIENT_ID"),
                "client_secret": os.environ.get("GOOGLE_ADS_CLIENT_SECRET"),
                "refresh_token": os.environ.get("GOOGLE_ADS_REFRESH_TOKEN"),
                "login_customer_id": os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID").replace('-', ''),
                "use_proto_plus": True,
            }
            
            self.client = GoogleAdsClient.load_from_dict(config)
            self.client_customer_id = os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID", "").replace('-', '')
            if not self.client_customer_id:
                self.client_customer_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace('-', '')
                
        except Exception as e:
            raise GoogleAdsClientError(f"Failed to initialize Google Ads client: {str(e)}")
    
    async def get_campaigns(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get campaign data for the specified date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            List of campaign data dictionaries
        """
        try:
            # Determine date range
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            # Create Google Ads service and query
            google_ads_service = self.client.get_service("GoogleAdsService")
            
            # Build query
            query = f"""
            SELECT
              campaign.id,
              campaign.name,
              campaign.status,
              campaign.advertising_channel_type,
              metrics.impressions,
              metrics.clicks,
              metrics.cost_micros,
              metrics.conversions
            FROM campaign
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY metrics.cost_micros DESC
            LIMIT 10
            """
            
            # Execute the search request
            search_request = self.client.get_type("SearchGoogleAdsRequest")
            search_request.customer_id = self.client_customer_id
            search_request.query = query
            
            response = google_ads_service.search(search_request)
            
            # Process the results
            campaigns = []
            for row in response:
                campaign = row.campaign
                metrics = row.metrics
                
                campaigns.append({
                    "id": campaign.id,
                    "name": campaign.name,
                    "status": campaign.status.name,
                    "channel_type": campaign.advertising_channel_type.name,
                    "impressions": metrics.impressions,
                    "clicks": metrics.clicks,
                    "cost": metrics.cost_micros / 1000000,  # Convert micros to dollars
                    "conversions": metrics.conversions,
                    "conversion_value": 0  # Default placeholder since field was removed
                })
            
            return campaigns
            
        except GoogleAdsException as ex:
            error_messages = []
            for error in ex.failure.errors:
                error_messages.append(f"Error {error.error_code}: {error.message}")
            error_str = "; ".join(error_messages)
            raise GoogleAdsClientError(f"Google Ads API Error: {error_str}")
        except Exception as e:
            raise GoogleAdsClientError(f"Error: {str(e)}")
    
    async def get_account_summary(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get account summary metrics for the specified date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Dictionary with account summary metrics
        """
        # Get campaigns with performance data
        campaigns = await self.get_campaigns(start_date, end_date)
        
        # Set date range for the response
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Calculate summary metrics
        total_cost = sum(campaign["cost"] for campaign in campaigns)
        total_clicks = sum(campaign["clicks"] for campaign in campaigns)
        total_impressions = sum(campaign["impressions"] for campaign in campaigns)
        total_conversions = sum(campaign["conversions"] for campaign in campaigns)
        
        # Calculate derived metrics (with safeguards against division by zero)
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        cpc = (total_cost / total_clicks) if total_clicks > 0 else 0
        conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        cost_per_conversion = (total_cost / total_conversions) if total_conversions > 0 else 0
        
        return {
            "total_cost": total_cost,
            "total_clicks": total_clicks,
            "total_impressions": total_impressions,
            "total_conversions": total_conversions,
            "ctr": ctr,
            "cpc": cpc,
            "conversion_rate": conversion_rate,
            "cost_per_conversion": cost_per_conversion,
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            }
        } 