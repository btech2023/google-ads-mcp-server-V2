#!/usr/bin/env python

import os
import sys
import logging
from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Import utility modules
from google_ads_mcp_server.utils.validation import (
    validate_customer_id,
    validate_date_format,
    validate_date_range,
    validate_enum,
    validate_positive_integer,
    validate_not_empty_string
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
from google_ads_mcp_server.utils.logging import get_logger

# Get logger
logger = get_logger(__name__)

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
        try:
            # Validate customer ID
            if not validate_customer_id(customer_id):
                raise ValueError(f"Invalid customer ID: {customer_id}")
            
            # Clean ID (remove hyphens)
            customer_id = clean_customer_id(customer_id)
            
            # Validate status filter if provided
            if status_filter:
                valid_statuses = ["ENABLED", "PAUSED", "REMOVED"]
                if not validate_enum(status_filter, valid_statuses):
                    raise ValueError(f"Invalid status filter: {status_filter}. Must be one of: {', '.join(valid_statuses)}")
                    
            logger.info(f"Getting ad groups for customer ID {format_customer_id(customer_id)}")
            
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
                
            # Format currency and numeric values
            for ad_group in ad_groups:
                if 'cost_micros' in ad_group:
                    ad_group['cost'] = micros_to_currency(ad_group['cost_micros'])
                if 'impressions' in ad_group:
                    ad_group['impressions_formatted'] = format_number(ad_group['impressions'])
                if 'clicks' in ad_group:
                    ad_group['clicks_formatted'] = format_number(ad_group['clicks'])
                if 'conversions' in ad_group:
                    ad_group['conversions_formatted'] = format_number(ad_group['conversions'], 1)
                if 'ctr' in ad_group:
                    ad_group['ctr_formatted'] = format_percentage(ad_group['ctr'])
                
            logger.info(f"Retrieved {len(ad_groups)} ad groups")
            return ad_groups
        
        except GoogleAdsException as ex:
            # Use standardized error handling for Google Ads exceptions
            error_details = handle_google_ads_exception(ex, context={
                "method": "get_ad_groups",
                "customer_id": customer_id,
                "campaign_id": campaign_id,
                "status_filter": status_filter
            })
            logger.error(f"Google Ads API Error: {error_details.message}")
            raise
        except Exception as e:
            # Use standardized error handling for other exceptions
            error_details = handle_exception(e, context={
                "method": "get_ad_groups",
                "customer_id": customer_id,
                "campaign_id": campaign_id,
                "status_filter": status_filter
            })
            logger.error(f"Error getting ad groups: {error_details.message}")
            raise
    
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
        try:
            # Validate customer ID
            if not validate_customer_id(customer_id):
                raise ValueError(f"Invalid customer ID: {customer_id}")
            
            # Clean ID (remove hyphens)
            customer_id = clean_customer_id(customer_id)
            
            # Calculate default date range if not provided
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                
            # Validate dates
            if not validate_date_format(start_date):
                raise ValueError(f"Invalid start date format: {start_date}. Use YYYY-MM-DD format.")
                
            if not validate_date_format(end_date):
                raise ValueError(f"Invalid end date format: {end_date}. Use YYYY-MM-DD format.")
                
            if not validate_date_range(start_date, end_date):
                raise ValueError(f"Invalid date range: {start_date} to {end_date}. Start date must be before or equal to end date.")
            
            logger.info(f"Getting performance data for ad group {ad_group_id} in customer ID {format_customer_id(customer_id)}")
            
            # Get daily stats for the ad group
            stats = await self.google_ads_service.get_ad_group_daily_stats(
                ad_group_id=ad_group_id,
                start_date=start_date,
                end_date=end_date,
                customer_id=customer_id
            )
            
            # Calculate totals for the period
            total_impressions = sum(day['impressions'] for day in stats)
            total_clicks = sum(day['clicks'] for day in stats)
            total_cost_micros = sum(day.get('cost_micros', 0) for day in stats)
            total_conversions = sum(day['conversions'] for day in stats)
            total_conversion_value = sum(day['conversion_value'] for day in stats)
            
            # Calculate derived metrics
            ctr = (total_clicks / total_impressions) if total_impressions > 0 else 0
            cpc_micros = (total_cost_micros / total_clicks) if total_clicks > 0 else 0
            conversion_rate = (total_conversions / total_clicks) if total_clicks > 0 else 0
            cost_per_conversion_micros = (total_cost_micros / total_conversions) if total_conversions > 0 else 0
            roas = (total_conversion_value / (total_cost_micros / 1000000)) if total_cost_micros > 0 else 0
            
            # Format daily stats with currency and numerics
            for day in stats:
                if 'cost_micros' in day:
                    day['cost'] = micros_to_currency(day['cost_micros'])
                if 'impressions' in day:
                    day['impressions_formatted'] = format_number(day['impressions'])
                if 'clicks' in day:
                    day['clicks_formatted'] = format_number(day['clicks'])
                if 'conversions' in day:
                    day['conversions_formatted'] = format_number(day['conversions'], 1)
                if 'conversion_value' in day:
                    day['conversion_value_formatted'] = micros_to_currency(day['conversion_value'])
            
            performance = {
                "ad_group_id": ad_group_id,
                "start_date": start_date,
                "end_date": end_date,
                "impressions": total_impressions,
                "impressions_formatted": format_number(total_impressions),
                "clicks": total_clicks,
                "clicks_formatted": format_number(total_clicks),
                "cost_micros": total_cost_micros,
                "cost": micros_to_currency(total_cost_micros),
                "conversions": total_conversions,
                "conversions_formatted": format_number(total_conversions, 1),
                "conversion_value": total_conversion_value,
                "conversion_value_formatted": micros_to_currency(total_conversion_value),
                "ctr": ctr,
                "ctr_formatted": format_percentage(ctr),
                "cpc_micros": cpc_micros,
                "cpc": micros_to_currency(cpc_micros),
                "conversion_rate": conversion_rate,
                "conversion_rate_formatted": format_percentage(conversion_rate),
                "cost_per_conversion_micros": cost_per_conversion_micros,
                "cost_per_conversion": micros_to_currency(cost_per_conversion_micros),
                "roas": roas,
                "roas_formatted": f"{roas:.2f}x",
                "daily_stats": stats
            }
            
            return performance
        
        except GoogleAdsException as ex:
            # Use standardized error handling for Google Ads exceptions
            error_details = handle_google_ads_exception(ex, context={
                "method": "get_ad_group_performance",
                "customer_id": customer_id,
                "ad_group_id": ad_group_id,
                "start_date": start_date,
                "end_date": end_date
            })
            logger.error(f"Google Ads API Error: {error_details.message}")
            raise
        except Exception as e:
            # Use standardized error handling for other exceptions
            error_details = handle_exception(e, context={
                "method": "get_ad_group_performance",
                "customer_id": customer_id,
                "ad_group_id": ad_group_id,
                "start_date": start_date,
                "end_date": end_date
            })
            logger.error(f"Error getting ad group performance: {error_details.message}")
            raise
    
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
        try:
            # Validate customer ID
            if not validate_customer_id(customer_id):
                raise ValueError(f"Invalid customer ID format: {customer_id}")
            
            # Clean ID (remove hyphens)
            customer_id = clean_customer_id(customer_id)
            
            # Validate name
            if not validate_not_empty_string(name, "name"):
                raise ValueError("Ad group name cannot be empty")
            
            # Validate status
            valid_statuses = ["ENABLED", "PAUSED", "REMOVED"]
            if not validate_enum(status, valid_statuses):
                raise ValueError(f"Invalid status: {status}. Must be one of: {', '.join(valid_statuses)}")
            
            # Validate CPC bid if provided
            if cpc_bid_micros is not None and not validate_positive_integer(cpc_bid_micros):
                raise ValueError("cpc_bid_micros must be a positive integer")
            
            logger.info(f"Creating ad group '{name}' in campaign {campaign_id} for customer ID {format_customer_id(customer_id)}")
            
            result = await self.google_ads_service.create_ad_group(
                campaign_id=campaign_id,
                name=name,
                status=status,
                cpc_bid_micros=cpc_bid_micros,
                customer_id=customer_id
            )
            
            # Add formatted bid if available
            if cpc_bid_micros:
                result["cpc_bid"] = micros_to_currency(cpc_bid_micros)
                
            return result
        
        except GoogleAdsException as ex:
            # Use standardized error handling for Google Ads exceptions
            error_details = handle_google_ads_exception(ex, context={
                "method": "create_ad_group",
                "customer_id": customer_id,
                "campaign_id": campaign_id,
                "name": name,
                "status": status
            })
            logger.error(f"Google Ads API Error: {error_details.message}")
            raise
        except Exception as e:
            # Use standardized error handling for other exceptions
            error_details = handle_exception(e, context={
                "method": "create_ad_group",
                "customer_id": customer_id,
                "campaign_id": campaign_id,
                "name": name,
                "status": status
            })
            logger.error(f"Error creating ad group: {error_details.message}")
            raise
    
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
        try:
            # Validate customer ID
            if not validate_customer_id(customer_id):
                raise ValueError(f"Invalid customer ID format: {customer_id}")
            
            # Clean ID (remove hyphens)
            customer_id = clean_customer_id(customer_id)
            
            # Validate name if provided
            if name is not None and not validate_not_empty_string(name, "name"):
                raise ValueError("Ad group name cannot be empty if provided")
            
            # Validate status if provided
            if status:
                valid_statuses = ["ENABLED", "PAUSED", "REMOVED"]
                if not validate_enum(status, valid_statuses):
                    raise ValueError(f"Invalid status: {status}. Must be one of: {', '.join(valid_statuses)}")
            
            # Validate CPC bid if provided
            if cpc_bid_micros is not None and not validate_positive_integer(cpc_bid_micros):
                raise ValueError("cpc_bid_micros must be a positive integer")
            
            # Ensure at least one field is being updated
            if not any([name, status, cpc_bid_micros is not None]): # Check cpc_bid_micros presence
                raise ValueError("At least one of name, status, or cpc_bid_micros must be provided")
                
            logger.info(f"Updating ad group {ad_group_id} for customer ID {format_customer_id(customer_id)}")
            
            result = await self.google_ads_service.update_ad_group(
                ad_group_id=ad_group_id,
                name=name,
                status=status,
                cpc_bid_micros=cpc_bid_micros,
                customer_id=customer_id
            )
            
            # Add formatted bid if available
            if cpc_bid_micros:
                result["cpc_bid"] = micros_to_currency(cpc_bid_micros)
                
            return result
        
        except GoogleAdsException as ex:
            # Use standardized error handling for Google Ads exceptions
            error_details = handle_google_ads_exception(ex, context={
                "method": "update_ad_group",
                "customer_id": customer_id,
                "ad_group_id": ad_group_id,
                "name": name,
                "status": status
            })
            logger.error(f"Google Ads API Error: {error_details.message}")
            raise
        except Exception as e:
            # Use standardized error handling for other exceptions
            error_details = handle_exception(e, context={
                "method": "update_ad_group",
                "customer_id": customer_id,
                "ad_group_id": ad_group_id,
                "name": name,
                "status": status
            })
            logger.error(f"Error updating ad group: {error_details.message}")
            raise

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
    if not validate_customer_id(login_customer_id):
        logger.error(f"Invalid login customer ID: {login_customer_id}")
        return 1
    
    login_customer_id = clean_customer_id(login_customer_id)
    
    client_customer_id = os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID")
    if client_customer_id:
        if not validate_customer_id(client_customer_id):
            logger.error(f"Invalid client customer ID: {client_customer_id}")
            return 1
        client_customer_id = clean_customer_id(client_customer_id)
    else:
        client_customer_id = login_customer_id
    
    logger.info(f"Using login customer ID: {format_customer_id(login_customer_id)}")
    logger.info(f"Using client customer ID: {format_customer_id(client_customer_id)}")
    
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
        # Use standardized error handling for Google Ads exceptions
        error_details = handle_google_ads_exception(ex, context={"method": "main"})
        logger.error(f"Google Ads API Error: {error_details.message}")
        return 1
    except Exception as e:
        # Use standardized error handling for other exceptions
        error_details = handle_exception(e, context={"method": "main"})
        logger.error(f"Error: {error_details.message}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 