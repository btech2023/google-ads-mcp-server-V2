#!/usr/bin/env python

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    if os.path.exists(".env"):
        load_dotenv(".env")
        logger.info("Loaded environment variables from ./.env")
    else:
        logger.warning("No .env file found")
except ImportError:
    logger.warning("python-dotenv not installed. Environment variables must be set directly.")

# Import Google Ads client 
try:
    from google.ads.googleads.client import GoogleAdsClient as GoogleAdsSDKClient
    from google.ads.googleads.errors import GoogleAdsException
except ImportError:
    logger.error("google-ads package not installed. Install with: pip install google-ads")
    sys.exit(1)

class GoogleAdsClientError(Exception):
    """Exception raised for errors in the GoogleAdsClient."""
    pass

class GoogleAdsClient:
    """Client for interacting with the Google Ads API."""

    def __init__(
        self,
        developer_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        login_customer_id: Optional[str] = None,
        client_customer_id: Optional[str] = None,
        config_path: Optional[str] = None,
    ):
        """Initialize the Google Ads client."""
        # Store customer IDs
        self.client_customer_id = None
        if client_customer_id:
            # Remove hyphens if present
            if '-' in client_customer_id:
                client_customer_id = client_customer_id.replace('-', '')
            self.client_customer_id = client_customer_id
            logger.info(f"Using client customer ID: {self.client_customer_id}")
        
        try:
            # Initialize with config file path
            if config_path:
                logger.info(f"Initializing with config file: {config_path}")
                self.client = GoogleAdsSDKClient.load_from_storage(config_path)
                return
                
            # Initialize with individual parameters
            if all([developer_token, client_id, client_secret, refresh_token, login_customer_id]):
                # Clean login_customer_id if it contains hyphens
                if login_customer_id and '-' in login_customer_id:
                    login_customer_id = login_customer_id.replace('-', '')
                    
                logger.info(f"Initializing with login customer ID: {login_customer_id}")
                
                config = {
                    "developer_token": developer_token,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                    "login_customer_id": login_customer_id,
                    "use_proto_plus": True,
                }
                self.client = GoogleAdsSDKClient.load_from_dict(config)
                return
                
            # Try to use environment variables if nothing else is provided
            if (
                os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")
                and os.environ.get("GOOGLE_ADS_CLIENT_ID")
                and os.environ.get("GOOGLE_ADS_CLIENT_SECRET")
                and os.environ.get("GOOGLE_ADS_REFRESH_TOKEN")
                and os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
            ):
                login_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
                # Clean login_customer_id if it contains hyphens
                if login_id and '-' in login_id:
                    login_id = login_id.replace('-', '')
                    
                # If client_customer_id not provided in constructor, try from env
                if not self.client_customer_id and os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID"):
                    client_id = os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID")
                    if client_id and '-' in client_id:
                        client_id = client_id.replace('-', '')
                    self.client_customer_id = client_id
                    logger.info(f"Using client customer ID from env: {self.client_customer_id}")
                
                logger.info(f"Initializing with login customer ID from env: {login_id}")
                config = {
                    "developer_token": os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN"),
                    "client_id": os.environ.get("GOOGLE_ADS_CLIENT_ID"),
                    "client_secret": os.environ.get("GOOGLE_ADS_CLIENT_SECRET"),
                    "refresh_token": os.environ.get("GOOGLE_ADS_REFRESH_TOKEN"),
                    "login_customer_id": login_id,
                    "use_proto_plus": True,
                }
                self.client = GoogleAdsSDKClient.load_from_dict(config)
                return
                
            # If we got here, we couldn't authenticate
            raise GoogleAdsClientError(
                "Missing Google Ads API credentials. Please provide either credentials "
                "as parameters, a config file path, or set environment variables."
            )
            
        except Exception as e:
            error_message = f"Failed to initialize Google Ads client: {str(e)}"
            logger.error(error_message)
            raise GoogleAdsClientError(error_message) from e
    
    def get_campaigns(self, date_range: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Get campaign data for the specified date range."""
        try:
            # Determine customer ID to use
            customer_id = self.client_customer_id or os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
            if '-' in customer_id:
                customer_id = customer_id.replace('-', '')
            
            # Get default date range if not provided
            if not date_range:
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=7)
                date_range = {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                }
            
            # Create Google Ads service and query
            google_ads_service = self.client.get_service("GoogleAdsService")
            
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
            WHERE segments.date BETWEEN '{date_range["start_date"]}' AND '{date_range["end_date"]}'
            ORDER BY metrics.cost_micros DESC
            LIMIT 10
            """
            
            # Execute the search request
            search_request = self.client.get_type("SearchGoogleAdsRequest")
            search_request.customer_id = customer_id
            search_request.query = query
            
            logger.info("Executing Google Ads query...")
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
                    "conversion_value": 0  # Default since this field is not available
                })
            
            return campaigns
            
        except GoogleAdsException as ex:
            logger.error("Google Ads API Error:")
            for error in ex.failure.errors:
                error_code_str = str(error.error_code)
                logger.error(f"Error code: {error_code_str}")
                logger.error(f"Error message: {error.message}")
            raise
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
    
    def get_account_summary(self, date_range: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get account summary metrics for the specified date range."""
        campaigns = self.get_campaigns(date_range)
        
        # Calculate summary metrics
        total_cost = sum(campaign["cost"] for campaign in campaigns)
        total_clicks = sum(campaign["clicks"] for campaign in campaigns)
        total_impressions = sum(campaign["impressions"] for campaign in campaigns)
        total_conversions = sum(campaign["conversions"] for campaign in campaigns)
        total_conversion_value = sum(campaign["conversion_value"] for campaign in campaigns)
        
        # Calculate derived metrics
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        cpc = (total_cost / total_clicks) if total_clicks > 0 else 0
        conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        cost_per_conversion = (total_cost / total_conversions) if total_conversions > 0 else 0
        roas = (total_conversion_value / total_cost) if total_cost > 0 else 0
        
        return {
            "total_cost": total_cost,
            "total_clicks": total_clicks,
            "total_impressions": total_impressions,
            "total_conversions": total_conversions,
            "total_conversion_value": total_conversion_value,
            "ctr": ctr,
            "cpc": cpc,
            "conversion_rate": conversion_rate,
            "cost_per_conversion": cost_per_conversion,
            "roas": roas,
            "date_range": date_range
        }
    
    def close(self):
        """Close any resources."""
        pass

def format_visualization_data(account_summary, campaigns):
    """Format data for visualization in Claude artifacts."""
    return {
        "summary_cards": format_summary_visualization(account_summary),
        "campaign_chart": format_campaign_visualization(campaigns)
    }

def format_summary_visualization(account_summary):
    """Format account summary for visualization."""
    return {
        "title": "Google Ads Performance Summary",
        "date_range": f"{account_summary['date_range']['start_date']} to {account_summary['date_range']['end_date']}",
        "kpi_cards": [
            {
                "title": "Cost",
                "value": f"${account_summary['total_cost']:.2f}",
                "metric": "cost"
            },
            {
                "title": "Conversions",
                "value": f"{account_summary['total_conversions']:.1f}",
                "metric": "conversions"
            },
            {
                "title": "ROAS",
                "value": f"{account_summary['roas']:.2f}",
                "metric": "roas"
            },
            {
                "title": "CTR",
                "value": f"{account_summary['ctr']:.2f}%",
                "metric": "ctr"
            },
            {
                "title": "Cost per Conversion",
                "value": f"${account_summary['cost_per_conversion']:.2f}",
                "metric": "cpa"
            }
        ]
    }

def format_campaign_visualization(campaigns):
    """Format campaign data for visualization."""
    return {
        "title": "Top Campaigns by Cost",
        "type": "bar",
        "data": [
            {
                "campaign": campaign["name"],
                "cost": campaign["cost"],
                "clicks": campaign["clicks"],
                "conversions": campaign["conversions"]
            }
            for campaign in campaigns[:10]  # Top 10 campaigns
        ],
        "axes": {
            "x": "campaign",
            "y": "cost"
        }
    }

def main():
    """Run the Google Ads API test."""
    try:
        # Initialize Google Ads client
        ads_client = GoogleAdsClient()
        logger.info("Google Ads client initialized successfully")
        
        # Get default date range (last 7 days)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        date_range = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d")
        }
        
        # Get campaigns
        logger.info(f"Fetching campaign data for {date_range['start_date']} to {date_range['end_date']}...")
        campaigns = ads_client.get_campaigns(date_range)
        logger.info(f"Retrieved {len(campaigns)} campaigns")
        
        # Get account summary
        logger.info("Calculating account summary...")
        account_summary = ads_client.get_account_summary(date_range)
        
        # Format for visualization
        visualization_data = format_visualization_data(account_summary, campaigns)
        
        # Create complete response
        result = {
            "summary": account_summary,
            "campaigns": campaigns,
            "visualization_data": visualization_data
        }
        
        # Display the result
        logger.info("Results:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 