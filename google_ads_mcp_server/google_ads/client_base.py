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

class GoogleAdsClientError(Exception):
    """Custom exception for Google Ads client errors."""
    pass

class GoogleAdsClient:
    """Base service for interacting with the Google Ads API without caching."""
    
    def __init__(self):
        """
        Initialize the Google Ads service.
        """
        self.logger = logging.getLogger("google-ads-service")
        
        # Load credentials from environment variables
        self.developer_token = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")
        self.client_id = os.environ.get("GOOGLE_ADS_CLIENT_ID")
        self.client_secret = os.environ.get("GOOGLE_ADS_CLIENT_SECRET")
        self.refresh_token = os.environ.get("GOOGLE_ADS_REFRESH_TOKEN")
        self.login_customer_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
        self.client_customer_id = os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID") or self.login_customer_id
        
        # Validate credentials
        if not all([self.developer_token, self.client_id, self.client_secret, 
                    self.refresh_token, self.login_customer_id]):
            raise GoogleAdsClientError("Missing required Google Ads API credentials")
        
        # Remove any dashes from customer IDs
        if self.login_customer_id:
            self.login_customer_id = self.login_customer_id.replace("-", "")
        if self.client_customer_id:
            self.client_customer_id = self.client_customer_id.replace("-", "")
        
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
            self.logger.error(f"Failed to initialize GoogleAdsClient: {str(e)}")
            raise GoogleAdsClientError(f"Google Ads client initialization failed: {str(e)}")
    
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
        try:
            # Ensure we're using an MCC account
            customer_id = self._validate_customer_id(self.login_customer_id)
            
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
            
            self.logger.info(f"Retrieved {len(accounts)} accessible accounts")
            
            return accounts
            
        except GoogleAdsException as ex:
            self.logger.error(f"Failed to list accessible accounts: {ex}")
            error_details = []
            for error in ex.failure.errors:
                error_details.append(f"{error.error_code.name}: {error.message}")
            error_message = "Google Ads API errors:\n" + "\n".join(error_details)
            raise GoogleAdsClientError(error_message)
        except Exception as e:
            self.logger.error(f"Unexpected error listing accessible accounts: {str(e)}")
            raise GoogleAdsClientError(f"Unexpected error: {str(e)}")
    
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
        # Validate the customer ID
        try:
            validated_customer_id = self._validate_customer_id(customer_id)
        except GoogleAdsClientError as e:
            self.logger.error(f"Customer ID validation failed: {str(e)}")
            raise
            
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
        
        self.logger.info(f"Executing query for customer ID {validated_customer_id}, date range {start_date} to {end_date}")
        try:
            # Get Google Ads service
            ga_service = self.client.get_service("GoogleAdsService")
            
            # Execute the query
            response = ga_service.search(
                customer_id=validated_customer_id,
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
                    "cost": row.metrics.cost_micros / 1000000,  # Convert micros to dollars
                    "conversions": row.metrics.conversions,
                    "conversion_value": row.metrics.conversions_value
                }
                campaigns.append(campaign)
            
            self.logger.info(f"Retrieved {len(campaigns)} campaigns for customer ID {validated_customer_id}")
            
            return campaigns
            
        except GoogleAdsException as ex:
            self.logger.error(f"Google Ads API request failed for customer ID {validated_customer_id}: {ex}")
            error_details = []
            for error in ex.failure.errors:
                error_details.append(f"{error.error_code.name}: {error.message}")
                
                # Provide more helpful error messages for common issues
                if "CUSTOMER_NOT_FOUND" in error.error_code.name:
                    error_details.append("The specified customer ID was not found or you don't have access to it.")
                elif "CUSTOMER_NOT_ENABLED" in error.error_code.name:
                    error_details.append("The customer account is not enabled for API access.")
                elif "NOT_ADS_USER" in error.error_code.name:
                    error_details.append("The login customer specified in the config is not a valid Ads user.")
                    
            error_message = "Google Ads API errors:\n" + "\n".join(error_details)
            raise GoogleAdsClientError(error_message)
        except Exception as e:
            self.logger.error(f"Unexpected error during Google Ads API request for customer ID {validated_customer_id}: {str(e)}")
            raise GoogleAdsClientError(f"Unexpected error: {str(e)}")

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
        # Validate the customer ID
        try:
            validated_customer_id = self._validate_customer_id(customer_id)
        except GoogleAdsClientError as e:
            self.logger.error(f"Customer ID validation failed: {str(e)}")
            raise
        
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
        
        try:
            # Get Google Ads service
            ga_service = self.client.get_service("GoogleAdsService")
            
            # Execute the query
            response = ga_service.search(
                customer_id=validated_customer_id,
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
            total_cost = total_cost_micros / 1000000  # Convert micros to dollars
            
            # Calculate derived metrics
            ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
            cpc = (total_cost / total_clicks) if total_clicks > 0 else 0
            conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
            cost_per_conversion = (total_cost / total_conversions) if total_conversions > 0 else 0
            
            summary = {
                "customer_id": validated_customer_id,
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                },
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "total_cost": total_cost,
                "total_conversions": total_conversions,
                "total_conversion_value": total_conversion_value,
                "ctr": ctr,
                "cpc": cpc,
                "conversion_rate": conversion_rate,
                "cost_per_conversion": cost_per_conversion
            }
            
            return summary
            
        except GoogleAdsException as ex:
            self.logger.error(f"Google Ads API request failed for customer ID {validated_customer_id}: {ex}")
            error_details = []
            for error in ex.failure.errors:
                error_details.append(f"{error.error_code.name}: {error.message}")
                
                # Provide more helpful error messages for common issues
                if "CUSTOMER_NOT_FOUND" in error.error_code.name:
                    error_details.append("The specified customer ID was not found or you don't have access to it.")
                elif "CUSTOMER_NOT_ENABLED" in error.error_code.name:
                    error_details.append("The customer account is not enabled for API access.")
                    
            error_message = "Google Ads API errors:\n" + "\n".join(error_details)
            raise GoogleAdsClientError(error_message)
        except Exception as e:
            self.logger.error(f"Unexpected error during Google Ads API request for customer ID {validated_customer_id}: {str(e)}")
            raise GoogleAdsClientError(f"Unexpected error: {str(e)}")

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
        # Validate the customer ID
        try:
            validated_customer_id = self._validate_customer_id(customer_id)
        except GoogleAdsClientError as e:
            self.logger.error(f"Customer ID validation failed: {str(e)}")
            raise
            
        try:
            # Get services
            campaign_budget_service = self.client.get_service("CampaignBudgetService")
            
            # Create the budget resource name
            resource_name = campaign_budget_service.campaign_budget_path(validated_customer_id, budget_id)
            
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
                customer_id=validated_customer_id,
                operations=[campaign_budget_operation]
            )
            
            # Process and return the response
            updated_budget = {
                "budget_id": budget_id,
                "resource_name": response.results[0].resource_name,
                "amount_micros": amount_micros,
                "amount_dollars": amount_micros / 1000000
            }
            
            self.logger.info(f"Updated budget {budget_id} for customer ID {validated_customer_id} to {amount_micros} micros (${amount_micros/1000000:.2f})")
            
            return updated_budget
            
        except GoogleAdsException as ex:
            self.logger.error(f"Google Ads API request failed for customer ID {validated_customer_id}: {ex}")
            error_details = []
            for error in ex.failure.errors:
                error_details.append(f"{error.error_code.name}: {error.message}")
                
                # Provide more helpful error messages for common issues
                if "CUSTOMER_NOT_FOUND" in error.error_code.name:
                    error_details.append("The specified customer ID was not found or you don't have access to it.")
                elif "CAMPAIGN_BUDGET_NOT_FOUND" in error.error_code.name:
                    error_details.append(f"Budget with ID {budget_id} was not found in this account.")
                    
            error_message = "Google Ads API errors:\n" + "\n".join(error_details)
            raise GoogleAdsClientError(error_message)
        except Exception as e:
            self.logger.error(f"Unexpected error during Google Ads API request for customer ID {validated_customer_id}: {str(e)}")
            raise GoogleAdsClientError(f"Unexpected error: {str(e)}") 