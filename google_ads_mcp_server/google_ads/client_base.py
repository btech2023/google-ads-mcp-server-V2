"""
Google Ads Base Client Module

This module provides the base client for interacting with the Google Ads API.
It does not include caching functionality.
"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from google.ads.googleads.client import GoogleAdsClient as GoogleAdsAPIClient
from google.ads.googleads.errors import GoogleAdsException

# Import utilities
from google_ads_mcp_server.utils.logging import get_logger
from google_ads_mcp_server.utils.validation import (
    validate_customer_id,
    validate_not_empty_string,
    validate_date_format,
    validate_date_range,
    validate_positive_integer,
    validate_budget_id # Assuming exists
)
from google_ads_mcp_server.utils.error_handler import (
    handle_exception,
    handle_google_ads_exception,
    CATEGORY_API_ERROR,
    CATEGORY_CONFIG,
    CATEGORY_BUSINESS_LOGIC,
    SEVERITY_ERROR,
    SEVERITY_WARNING
)
from google_ads_mcp_server.utils.formatting import clean_customer_id, micros_to_currency

class GoogleAdsClientError(Exception):
    """Custom exception for Google Ads client errors."""
    pass

class GoogleAdsClient:
    """Base service for interacting with the Google Ads API without caching."""
    
    def __init__(self):
        """
        Initialize the Google Ads service.
        """
        # Use get_logger for consistency
        self.logger = get_logger("google-ads-client-base") 
        
        # Load credentials from environment variables
        self.developer_token = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")
        self.client_id = os.environ.get("GOOGLE_ADS_CLIENT_ID")
        self.client_secret = os.environ.get("GOOGLE_ADS_CLIENT_SECRET")
        self.refresh_token = os.environ.get("GOOGLE_ADS_REFRESH_TOKEN")
        self.login_customer_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
        self.client_customer_id = os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID") or self.login_customer_id
        
        context = {"method": "__init__"}

        # Validate credentials
        # Use specific checks for better error messages
        if not validate_not_empty_string(self.developer_token, "GOOGLE_ADS_DEVELOPER_TOKEN") or \
           not validate_not_empty_string(self.client_id, "GOOGLE_ADS_CLIENT_ID") or \
           not validate_not_empty_string(self.client_secret, "GOOGLE_ADS_CLIENT_SECRET") or \
           not validate_not_empty_string(self.refresh_token, "GOOGLE_ADS_REFRESH_TOKEN") or \
           not validate_not_empty_string(self.login_customer_id, "GOOGLE_ADS_LOGIN_CUSTOMER_ID"): 
            # Log detailed error before raising general one
            error_details = handle_exception(ValueError("Missing required Google Ads API credentials from environment variables."), context=context, category=CATEGORY_CONFIG)
            self.logger.error(error_details.message) 
            raise GoogleAdsClientError("Missing required Google Ads API credentials")
        
        # Validate and clean customer IDs
        try:
            if not validate_customer_id(self.login_customer_id):
                raise ValueError(f"Invalid login_customer_id format: {self.login_customer_id}")
            self.login_customer_id = clean_customer_id(self.login_customer_id)
            
            if not validate_customer_id(self.client_customer_id):
                raise ValueError(f"Invalid client_customer_id format: {self.client_customer_id}")
            self.client_customer_id = clean_customer_id(self.client_customer_id)
        except ValueError as ve:
            error_details = handle_exception(ve, context=context, category=CATEGORY_CONFIG)
            self.logger.error(f"Customer ID validation failed during init: {error_details.message}")
            raise GoogleAdsClientError(f"Invalid Customer ID provided in environment: {ve}") from ve
        
        try:
            # Initialize the Google Ads client
            self.client = GoogleAdsAPIClient.load_from_dict({
                "developer_token": self.developer_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "login_customer_id": self.login_customer_id,
                "use_proto_plus": True
            })
            self.logger.info(f"GoogleAdsClient initialized with login_customer_id: {self.login_customer_id}")
            self.logger.info(f"Default client_customer_id for queries: {self.client_customer_id}")
            
        except Exception as e:
            # Use error handler for logging
            error_details = handle_exception(e, context=context, category=CATEGORY_CONFIG)
            self.logger.error(f"Failed to initialize GoogleAdsClient: {error_details.message}")
            # Still raise custom error, but wrap original
            raise GoogleAdsClientError(f"Google Ads client initialization failed: {error_details.message}") from e
    
    def _validate_customer_id(self, customer_id: Optional[str] = None) -> str:
        """
        Validate and format a customer ID.
        
        Args:
            customer_id: The customer ID to validate, or None to use the default
            
        Returns:
            Validated and formatted customer ID
            
        Raises:
            GoogleAdsClientError: If the customer ID is invalid
        """
        # Use default if not provided
        if not customer_id:
            customer_id = self.client_customer_id
            
        if not customer_id:
            raise GoogleAdsClientError("No customer ID provided and no default customer ID available")
            
        # Remove dashes if present
        customer_id = customer_id.replace("-", "")
        
        # Validate format (should be a 10-digit number)
        if not customer_id.isdigit() or len(customer_id) != 10:
            raise GoogleAdsClientError(f"Invalid customer ID format: {customer_id}. Should be a 10-digit number.")
            
        return customer_id

    async def list_accessible_accounts(self) -> List[Dict[str, str]]:
        """
        List all accounts accessible from the MCC account.
        
        Returns:
            List of accessible accounts with their IDs and names
        """
        context = {"method": "list_accessible_accounts", "login_customer_id": self.login_customer_id}
        try:
            # Ensure we're using an MCC account
            # login_customer_id already validated in __init__
            customer_id = self.login_customer_id 
            
            # Get the CustomerService
            customer_service = self.client.get_service("CustomerService")
            
            # Request accessible customers
            accessible_customers = customer_service.list_accessible_customers()
            
            # Get the actual customer details for each accessible customer
            accounts = []
            for resource_name in accessible_customers.resource_names:
                # Extract the customer ID from the resource name
                account_id = resource_name.split('/')[-1]
                
                try:
                    # Get customer details
                    customer = customer_service.get_customer(resource_name=resource_name)
                    accounts.append({
                        "id": account_id,
                        "name": customer.descriptive_name,
                        "resource_name": resource_name
                    })
                except GoogleAdsException as ex:
                    # Log error but continue with other accounts
                    self.logger.warning(f"Could not access details for account {account_id}: {ex}")
            
            self.logger.info(f"Retrieved {len(accounts)} accessible accounts for MCC {customer_id}")
            
            return accounts
            
        except GoogleAdsException as ex:
            # Use error handler for consistent logging
            error_details = handle_google_ads_exception(ex, context=context)
            self.logger.error(f"Failed to list accessible accounts: {error_details.message}")
            raise GoogleAdsClientError(f"Failed to list accessible accounts: {error_details.original_message or error_details.message}") from ex
        except Exception as e:
            error_details = handle_exception(e, context=context)
            self.logger.error(f"Unexpected error listing accessible accounts: {error_details.message}")
            raise GoogleAdsClientError(f"Unexpected error: {error_details.message}") from e
    
    async def get_campaigns(self, start_date: str, end_date: str, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get campaign performance data for the specified date range and customer ID.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            customer_id: Optional customer ID (defaults to client_customer_id if not provided)
            
        Returns:
            List of campaign data dictionaries
        """
        context = {"start_date": start_date, "end_date": end_date, "customer_id": customer_id, "method": "get_campaigns"}
        try:
            # Validate Customer ID
            customer_id_to_use = customer_id or self.client_customer_id
            if not customer_id_to_use:
                raise ValueError("No customer ID provided and no default available.")
            if not validate_customer_id(customer_id_to_use):
                 raise ValueError(f"Invalid customer ID format: {customer_id_to_use}")
            cleaned_customer_id = clean_customer_id(customer_id_to_use)
            context["customer_id"] = cleaned_customer_id # Update context

            # Validate Dates
            if not validate_date_format(start_date):
                raise ValueError(f"Invalid start_date format: {start_date}")
            if not validate_date_format(end_date):
                raise ValueError(f"Invalid end_date format: {end_date}")
            if not validate_date_range(start_date, end_date):
                raise ValueError(f"Invalid date range: {start_date} to {end_date}")
            
            query = f"""
                SELECT
                    campaign.id,
                    campaign.name,
                    campaign.status,
                    campaign.advertising_channel_type,
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.conversions_value
                FROM campaign
                WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
                ORDER BY campaign.id
            """
            
            self.logger.info(f"Executing campaign query for customer ID {cleaned_customer_id}, date range {start_date} to {end_date}")
            try:
                # Get Google Ads service
                ga_service = self.client.get_service("GoogleAdsService")
                
                # Execute the query
                response = ga_service.search(
                    customer_id=cleaned_customer_id,
                    query=query,
                    retry=None  # Using default retry strategy
                )
                
                # Process the results
                campaigns = []
                for row in response:
                    campaign = {
                        "id": row.campaign.id,
                        "name": row.campaign.name,
                        "status": row.campaign.status.name,
                        "channel_type": row.campaign.advertising_channel_type.name,
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost_micros": row.metrics.cost_micros,
                        "cost": micros_to_currency(row.metrics.cost_micros),
                        "conversions": row.metrics.conversions,
                        "conversion_value": row.metrics.conversions_value
                    }
                    campaigns.append(campaign)
                
                self.logger.info(f"Retrieved {len(campaigns)} campaigns for customer ID {cleaned_customer_id}")
                
                return campaigns
                
            except GoogleAdsException as ex:
                error_details = handle_google_ads_exception(ex, context=context)
                self.logger.error(f"Google Ads API request failed for customer ID {cleaned_customer_id}: {error_details.message}")
                raise GoogleAdsClientError(f"Google Ads API error: {error_details.original_message or error_details.message}") from ex
            except Exception as e:
                error_details = handle_exception(e, context=context)
                self.logger.error(f"Unexpected error during Google Ads API request for customer ID {cleaned_customer_id}: {error_details.message}")
                raise GoogleAdsClientError(f"Unexpected error: {error_details.message}") from e
            
        except ValueError as ve:
            error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_BUSINESS_LOGIC)
            self.logger.warning(f"Validation error getting campaigns: {error_details.message}")
            raise GoogleAdsClientError(f"Invalid input: {error_details.message}") from ve

    async def get_account_summary(self, start_date: str, end_date: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get account summary metrics for the specified date range and customer ID.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            customer_id: Optional customer ID (defaults to client_customer_id if not provided)
            
        Returns:
            Dictionary with account summary metrics
        """
        context = {"start_date": start_date, "end_date": end_date, "customer_id": customer_id, "method": "get_account_summary"}
        try:
            # Validate Customer ID
            customer_id_to_use = customer_id or self.client_customer_id
            if not customer_id_to_use:
                raise ValueError("No customer ID provided and no default available.")
            if not validate_customer_id(customer_id_to_use):
                 raise ValueError(f"Invalid customer ID format: {customer_id_to_use}")
            cleaned_customer_id = clean_customer_id(customer_id_to_use)
            context["customer_id"] = cleaned_customer_id # Update context

            # Validate Dates
            if not validate_date_format(start_date):
                raise ValueError(f"Invalid start_date format: {start_date}")
            if not validate_date_format(end_date):
                raise ValueError(f"Invalid end_date format: {end_date}")
            if not validate_date_range(start_date, end_date):
                raise ValueError(f"Invalid date range: {start_date} to {end_date}")
            
            query = f"""
                SELECT
                    metrics.impressions,
                    metrics.clicks,
                    metrics.cost_micros,
                    metrics.conversions,
                    metrics.conversions_value
                FROM customer
                WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
            """
            
            self.logger.info(f"Executing account summary query for customer ID {cleaned_customer_id}, date range {start_date} to {end_date}")
            try:
                # Get Google Ads service
                ga_service = self.client.get_service("GoogleAdsService")
                
                # Execute the query
                response = ga_service.search(
                    customer_id=cleaned_customer_id,
                    query=query
                )
                
                # Process and aggregate the results
                total_impressions = 0
                total_clicks = 0
                total_cost_micros = 0
                total_conversions = 0
                total_conversion_value = 0
                
                for row in response:
                    total_impressions += row.metrics.impressions
                    total_clicks += row.metrics.clicks
                    total_cost_micros += row.metrics.cost_micros
                    total_conversions += row.metrics.conversions
                    total_conversion_value += row.metrics.conversions_value
                
                # Convert to summary dictionary
                total_cost = micros_to_currency(total_cost_micros)
                
                # Calculate derived metrics
                ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
                # Calculate CPC using micros for precision before formatting
                cpc_micros = (total_cost_micros / total_clicks) if total_clicks > 0 else 0
                conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
                # Calculate CPA using micros
                cost_per_conversion_micros = (total_cost_micros / total_conversions) if total_conversions > 0 else 0
                
                summary = {
                    "customer_id": cleaned_customer_id,
                    "date_range": {
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "total_impressions": total_impressions,
                    "total_clicks": total_clicks,
                    "total_cost": total_cost,
                    "total_conversions": total_conversions,
                    "total_conversion_value": total_conversion_value,
                    "cost_micros": total_cost_micros,
                    "ctr": ctr,
                    "cpc_micros": cpc_micros,
                    "cpc": micros_to_currency(cpc_micros),
                    "conversion_rate": conversion_rate,
                    "cost_per_conversion_micros": cost_per_conversion_micros,
                    "cost_per_conversion": micros_to_currency(cost_per_conversion_micros)
                }
                
                return summary
                
            except GoogleAdsException as ex:
                error_details = handle_google_ads_exception(ex, context=context)
                self.logger.error(f"Google Ads API request failed for customer ID {cleaned_customer_id}: {error_details.message}")
                raise GoogleAdsClientError(f"Google Ads API error: {error_details.original_message or error_details.message}") from ex
            except Exception as e:
                error_details = handle_exception(e, context=context)
                self.logger.error(f"Unexpected error during Google Ads API request for customer ID {cleaned_customer_id}: {error_details.message}")
                raise GoogleAdsClientError(f"Unexpected error: {error_details.message}") from e
            
        except ValueError as ve:
            error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_BUSINESS_LOGIC)
            self.logger.warning(f"Validation error getting account summary: {error_details.message}")
            raise GoogleAdsClientError(f"Invalid input: {error_details.message}") from ve

    async def update_campaign_budget(self, 
                                   budget_id: str, 
                                   amount_micros: int, 
                                   customer_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Update a campaign budget amount.
        
        Args:
            budget_id: The ID of the budget to update
            amount_micros: The new budget amount in micros (e.g., 2000000 = $2.00)
            customer_id: Optional customer ID (defaults to client_customer_id if not provided)
            
        Returns:
            Dictionary with updated budget information
        """
        context = {"budget_id": budget_id, "amount_micros": amount_micros, "customer_id": customer_id, "method": "update_campaign_budget"}
        try:
            # Validate Customer ID
            customer_id_to_use = customer_id or self.client_customer_id
            if not customer_id_to_use:
                raise ValueError("No customer ID provided and no default available.")
            if not validate_customer_id(customer_id_to_use):
                 raise ValueError(f"Invalid customer ID format: {customer_id_to_use}")
            cleaned_customer_id = clean_customer_id(customer_id_to_use)
            context["customer_id"] = cleaned_customer_id # Update context

            # Validate budget ID and amount
            if not validate_budget_id(budget_id):
                 raise ValueError(f"Invalid budget_id format: {budget_id}")
            if not validate_positive_integer(amount_micros):
                 raise ValueError(f"amount_micros must be a positive integer: {amount_micros}")
            
            # Get services
            campaign_budget_service = self.client.get_service("CampaignBudgetService")
            
            # Create the budget resource name
            resource_name = campaign_budget_service.campaign_budget_path(cleaned_customer_id, budget_id)
            
            # Create and configure the budget update operation
            campaign_budget_operation = self.client.get_type("CampaignBudgetOperation")
            campaign_budget = campaign_budget_operation.update
            campaign_budget.resource_name = resource_name
            campaign_budget.amount_micros = amount_micros
            
            # Create field mask for amount_micros field
            client = self.client
            field_mask = client.get_type("FieldMask")
            field_mask.paths.append("amount_micros")
            campaign_budget_operation.update_mask = field_mask
            
            # Send the update operation
            response = campaign_budget_service.mutate_campaign_budgets(
                customer_id=cleaned_customer_id,
                operations=[campaign_budget_operation]
            )
            
            # Process and return the response
            updated_budget = {
                "budget_id": budget_id,
                "resource_name": response.results[0].resource_name,
                "amount_micros": amount_micros,
                "amount_formatted": micros_to_currency(amount_micros)
            }
            
            self.logger.info(f"Updated budget {budget_id} for customer ID {cleaned_customer_id} to {amount_micros} micros ({micros_to_currency(amount_micros)})")
            
            return updated_budget
            
        except ValueError as ve:
            error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_BUSINESS_LOGIC)
            self.logger.warning(f"Validation error updating campaign budget: {error_details.message}")
            raise GoogleAdsClientError(f"Invalid input: {error_details.message}") from ve
        except GoogleAdsException as ex:
            error_details = handle_google_ads_exception(ex, context=context)
            self.logger.error(f"Google Ads API request failed for customer ID {cleaned_customer_id}: {error_details.message}")
            raise GoogleAdsClientError(f"Google Ads API error: {error_details.original_message or error_details.message}") from ex
        except Exception as e:
            error_details = handle_exception(e, context=context)
            self.logger.error(f"Unexpected error during Google Ads API request for customer ID {cleaned_customer_id}: {error_details.message}")
            raise GoogleAdsClientError(f"Unexpected error: {error_details.message}") from e 