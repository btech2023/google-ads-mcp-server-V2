#!/usr/bin/env python

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Import utility functions
from google_ads_mcp_server.utils.validation import (
    validate_customer_id,
    validate_date_format,
    validate_date_range
)
from google_ads_mcp_server.utils.error_handler import (
    handle_exception,
    handle_google_ads_exception,
    create_error_response,
    ErrorDetails,
    CATEGORY_API_ERROR
)
from google_ads_mcp_server.utils.formatting import (
    format_customer_id,
    clean_customer_id,
    micros_to_currency,
    format_percentage,
    format_date,
    format_number
)

# Import logger utility
from google_ads_mcp_server.utils.logging import get_logger
logger = get_logger(__name__)

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
            # Validate and clean customer ID
            if not validate_customer_id(client_customer_id):
                # Use ValueError for validation issues
                raise ValueError(f"Invalid client customer ID format: {client_customer_id}")
                
            # Clean ID (remove hyphens)
            self.client_customer_id = clean_customer_id(client_customer_id)
            logger.info(f"Using client customer ID: {format_customer_id(self.client_customer_id)}")
        
        try:
            # Initialize with config file path
            if config_path:
                logger.info(f"Initializing with config file: {config_path}")
                self.client = GoogleAdsSDKClient.load_from_storage(config_path)
                return
                
            # Initialize with individual parameters
            if all([developer_token, client_id, client_secret, refresh_token, login_customer_id]):
                # Validate and clean login customer ID
                if not validate_customer_id(login_customer_id):
                    # Use ValueError for validation issues
                    raise ValueError(f"Invalid login customer ID format: {login_customer_id}")
                
                # Clean ID (remove hyphens)
                clean_login_id = clean_customer_id(login_customer_id)                
                logger.info(f"Initializing with login customer ID: {format_customer_id(clean_login_id)}")
                
                config = {
                    "developer_token": developer_token,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                    "login_customer_id": clean_login_id,
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
                
                # Validate and clean login customer ID
                if not validate_customer_id(login_id):
                    # Use ValueError for validation issues
                    raise ValueError(f"Invalid login customer ID format in environment: {login_id}")
                
                # Clean ID (remove hyphens)
                clean_login_id = clean_customer_id(login_id)
                    
                # If client_customer_id not provided in constructor, try from env
                if not self.client_customer_id and os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID"):
                    client_id = os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID")
                    
                    # Validate and clean client customer ID
                    if not validate_customer_id(client_id):
                        # Use ValueError for validation issues
                        raise ValueError(f"Invalid client customer ID format in environment: {client_id}")
                    
                    # Clean ID (remove hyphens)
                    clean_client_id = clean_customer_id(client_id)
                    self.client_customer_id = clean_client_id
                    logger.info(f"Using client customer ID from env: {format_customer_id(clean_client_id)}")
                
                logger.info(f"Initializing with login customer ID from env: {format_customer_id(clean_login_id)}")
                config = {
                    "developer_token": os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN"),
                    "client_id": os.environ.get("GOOGLE_ADS_CLIENT_ID"),
                    "client_secret": os.environ.get("GOOGLE_ADS_CLIENT_SECRET"),
                    "refresh_token": os.environ.get("GOOGLE_ADS_REFRESH_TOKEN"),
                    "login_customer_id": clean_login_id,
                    "use_proto_plus": True,
                }
                self.client = GoogleAdsSDKClient.load_from_dict(config)
                return
                
            # If we got here, we couldn't authenticate
            raise GoogleAdsClientError(
                "Missing Google Ads API credentials. Please provide either credentials "
                "as parameters, a config file path, or set environment variables."
            )
            
        except GoogleAdsException as e:
            # Use standardized error handling for Google Ads exceptions
            error_details = handle_google_ads_exception(e, context={"method": "__init__"})
            logger.error(f"Google Ads API Error: {error_details.message}")
            raise GoogleAdsClientError(error_details.message) from e
        except Exception as e:
            # Use standardized error handling for other exceptions
            error_details = handle_exception(e, context={"method": "__init__"})
            logger.error(f"Failed to initialize Google Ads client: {error_details.message}")
            raise GoogleAdsClientError(error_details.message) from e
    
    def get_campaigns(self, date_range: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Get campaign data for the specified date range."""
        try:
            # Determine customer ID to use
            customer_id = self.client_customer_id or os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
            
            # Validate customer ID
            if not validate_customer_id(customer_id):
                raise ValueError(f"Invalid customer ID: {customer_id}")
            
            # Clean ID (remove hyphens)
            customer_id = clean_customer_id(customer_id)
            
            # Get default date range if not provided
            if not date_range:
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=7)
                date_range = {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                }
            
            # Validate date range
            if not validate_date_format(date_range["start_date"]):
                raise ValueError(f"Invalid start date format: {date_range['start_date']}")
            
            if not validate_date_format(date_range["end_date"]):
                raise ValueError(f"Invalid end date format: {date_range['end_date']}")
                
            if not validate_date_range(date_range["start_date"], date_range["end_date"]):
                raise ValueError(f"Invalid date range: {date_range['start_date']} to {date_range['end_date']}")
            
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
            
            logger.info(f"Executing Google Ads query for customer ID: {format_customer_id(customer_id)}")
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
                    "cost": micros_to_currency(metrics.cost_micros),  # Use formatting utility
                    "cost_micros": metrics.cost_micros,  # Keep raw value for calculations
                    "conversions": metrics.conversions,
                    "conversion_value": 0  # Default since this field is not available
                })
            
            logger.info(f"Retrieved {len(campaigns)} campaigns for customer {format_customer_id(customer_id)}")
            return campaigns
            
        except GoogleAdsException as ex:
            # Use standardized error handling for Google Ads exceptions
            error_details = handle_google_ads_exception(ex, context={
                "method": "get_campaigns",
                "customer_id": customer_id,
                "date_range": date_range
            })
            logger.error(f"Google Ads API Error: {error_details.message}")
            raise GoogleAdsClientError(error_details.message) from ex
        except Exception as e:
            # Use standardized error handling for other exceptions
            # Check if it's a validation error we raised
            if isinstance(e, ValueError):
                 error_details = handle_exception(e, context={ "method": "get_campaigns", "customer_id": customer_id, "date_range": date_range }, severity=SEVERITY_WARNING, category=CATEGORY_BUSINESS_LOGIC)
                 logger.warning(f"Validation error getting campaigns: {error_details.message}")
                 raise e # Re-raise validation error directly
                 
            error_details = handle_exception(e, context={
                "method": "get_campaigns",
                "customer_id": customer_id,
                "date_range": date_range
            })
            logger.error(f"Error getting campaigns: {error_details.message}")
            raise GoogleAdsClientError(error_details.message) from e
    
    def get_account_summary(self, date_range: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get account summary metrics for the specified date range."""
        try:
            campaigns = self.get_campaigns(date_range)
            
            # Calculate summary metrics
            total_cost_micros = sum(campaign["cost_micros"] for campaign in campaigns)
            total_clicks = sum(campaign["clicks"] for campaign in campaigns)
            total_impressions = sum(campaign["impressions"] for campaign in campaigns)
            total_conversions = sum(campaign["conversions"] for campaign in campaigns)
            total_conversion_value = sum(campaign["conversion_value"] for campaign in campaigns)
            
            # Calculate derived metrics
            ctr = (total_clicks / total_impressions) if total_impressions > 0 else 0
            cpc_micros = (total_cost_micros / total_clicks) if total_clicks > 0 else 0
            conversion_rate = (total_conversions / total_clicks) if total_clicks > 0 else 0
            cost_per_conversion_micros = (total_cost_micros / total_conversions) if total_conversions > 0 else 0
            roas = (total_conversion_value / (total_cost_micros / 1000000)) if total_cost_micros > 0 else 0
            
            return {
                "total_cost": micros_to_currency(total_cost_micros),
                "total_cost_micros": total_cost_micros,
                "total_clicks": format_number(total_clicks),
                "total_clicks_raw": total_clicks,
                "total_impressions": format_number(total_impressions),
                "total_impressions_raw": total_impressions,
                "total_conversions": format_number(total_conversions, 1),
                "total_conversions_raw": total_conversions,
                "total_conversion_value": micros_to_currency(total_conversion_value),
                "total_conversion_value_raw": total_conversion_value,
                "ctr": format_percentage(ctr),
                "ctr_raw": ctr,
                "cpc": micros_to_currency(cpc_micros),
                "cpc_micros": cpc_micros,
                "conversion_rate": format_percentage(conversion_rate),
                "conversion_rate_raw": conversion_rate,
                "cost_per_conversion": micros_to_currency(cost_per_conversion_micros),
                "cost_per_conversion_micros": cost_per_conversion_micros,
                "roas": f"{roas:.2f}",
                "roas_raw": roas,
                "date_range": date_range
            }
        except Exception as e:
            # Use standardized error handling
            error_details = handle_exception(e, context={
                "method": "get_account_summary",
                "date_range": date_range
            })
            logger.error(f"Error getting account summary: {error_details.message}")
            raise GoogleAdsClientError(error_details.message) from e
    
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
                "value": account_summary['total_cost'],
                "metric": "cost"
            },
            {
                "title": "Conversions",
                "value": account_summary['total_conversions'],
                "metric": "conversions"
            },
            {
                "title": "ROAS",
                "value": account_summary['roas'],
                "metric": "roas"
            },
            {
                "title": "CTR",
                "value": account_summary['ctr'],
                "metric": "ctr"
            },
            {
                "title": "Cost per Conversion",
                "value": account_summary['cost_per_conversion'],
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
        # Use standardized error handling
        error_details = handle_exception(e, context={"method": "main"})
        logger.error(f"Error: {error_details.message}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 