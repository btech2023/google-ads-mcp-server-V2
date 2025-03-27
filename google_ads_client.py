import os
import logging
import asyncio
import json
import hashlib
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

try:
    # Import monitoring if available
    from monitoring import record_cache_hit, record_cache_miss, monitor_google_ads_api
    MONITORING_ENABLED = True
except ImportError:
    MONITORING_ENABLED = False
    
    # Define dummy monitoring functions if monitoring is not available
    def record_cache_hit(): pass
    def record_cache_miss(): pass
    def monitor_google_ads_api(endpoint): 
        def decorator(func): return func
        return decorator

class GoogleAdsClientError(Exception):
    """Custom exception for Google Ads client errors."""
    pass

class CacheEntry:
    """Class representing a cached response."""
    
    def __init__(self, data: Any, expiry: float):
        """
        Initialize a cache entry.
        
        Args:
            data: The data to cache
            expiry: The timestamp when this cache entry expires
        """
        self.data = data
        self.expiry = expiry
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() > self.expiry

class GoogleAdsService:
    """Service for interacting with the Google Ads API."""
    
    def __init__(self, cache_enabled: bool = True, cache_ttl: int = 3600):
        """
        Initialize the Google Ads service.
        
        Args:
            cache_enabled: Whether to enable caching (default: True)
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        self.logger = logging.getLogger("google-ads-service")
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.cache = {}  # In-memory cache dictionary
        
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
            self.client = GoogleAdsClient.load_from_dict({
                "developer_token": self.developer_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "login_customer_id": self.login_customer_id,
                "use_proto_plus": True
            })
            self.logger.info(f"GoogleAdsClient initialized with login_customer_id: {self.login_customer_id}")
            self.logger.info(f"Default client_customer_id for queries: {self.client_customer_id}")
            self.logger.info(f"Caching {'enabled' if cache_enabled else 'disabled'} with TTL of {cache_ttl} seconds")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize GoogleAdsClient: {str(e)}")
            raise GoogleAdsClientError(f"Google Ads client initialization failed: {str(e)}")
    
    def _generate_cache_key(self, method_name: str, *args, **kwargs) -> str:
        """
        Generate a unique cache key for the given method call.
        
        Args:
            method_name: The name of the method being called
            *args: Positional arguments to the method
            **kwargs: Keyword arguments to the method
            
        Returns:
            A unique string key for caching
        """
        # Create a representation of the call
        call_repr = {
            "method": method_name,
            "args": args,
            "kwargs": kwargs
        }
        
        # Convert to a stable JSON string and hash it
        json_str = json.dumps(call_repr, sort_keys=True)
        return hashlib.md5(json_str.encode()).hexdigest()
    
    def _get_cached_data(self, cache_key: str) -> Optional[Any]:
        """
        Get data from cache if it exists and is not expired.
        
        Args:
            cache_key: The cache key to lookup
            
        Returns:
            The cached data or None if not found or expired
        """
        if not self.cache_enabled:
            return None
            
        entry = self.cache.get(cache_key)
        if entry is None:
            if MONITORING_ENABLED:
                record_cache_miss()
            return None
            
        if entry.is_expired():
            del self.cache[cache_key]
            if MONITORING_ENABLED:
                record_cache_miss()
            return None
            
        self.logger.info(f"Cache hit for key: {cache_key}")
        if MONITORING_ENABLED:
            record_cache_hit()
        return entry.data
    
    def _cache_data(self, cache_key: str, data: Any) -> None:
        """
        Store data in the cache.
        
        Args:
            cache_key: The cache key to store under
            data: The data to cache
        """
        if not self.cache_enabled:
            return
            
        expiry = time.time() + self.cache_ttl
        self.cache[cache_key] = CacheEntry(data, expiry)
        self.logger.info(f"Cached data for key: {cache_key}")
    
    def _clear_cache(self) -> None:
        """Clear all cached data."""
        self.cache.clear()
        self.logger.info("Cache cleared")
    
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

    @monitor_google_ads_api("list_accessible_accounts")
    async def list_accessible_accounts(self) -> List[Dict[str, str]]:
        """
        List all accounts accessible from the MCC account.
        
        Returns:
            List of accessible accounts with their IDs and names
        """
        # Check cache first
        cache_key = self._generate_cache_key("list_accessible_accounts")
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
            
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
            
            # Cache the results
            self._cache_data(cache_key, accounts)
            
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
    
    @monitor_google_ads_api("get_campaigns")
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
        
        # Check cache first
        cache_key = self._generate_cache_key("get_campaigns", start_date, end_date, validated_customer_id)
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
            
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
            
            # Cache the results
            self._cache_data(cache_key, campaigns)
            
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
    
    @monitor_google_ads_api("get_account_summary")
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
        
        # Check cache first
        cache_key = self._generate_cache_key("get_account_summary", start_date, end_date, validated_customer_id)
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
            
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
            
            # Cache the results
            self._cache_data(cache_key, summary)
            
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
            
    @monitor_google_ads_api("get_account_hierarchy")
    async def get_account_hierarchy(self, customer_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the account hierarchy starting from the specified customer ID.
        
        Args:
            customer_id: Optional customer ID (defaults to login_customer_id if not provided)
            
        Returns:
            Dictionary with account hierarchy information
        """
        # Use login_customer_id as default for hierarchy (since it's typically the MCC)
        if not customer_id:
            customer_id = self.login_customer_id
            
        # Validate the customer ID
        try:
            validated_customer_id = self._validate_customer_id(customer_id)
        except GoogleAdsClientError as e:
            self.logger.error(f"Customer ID validation failed: {str(e)}")
            raise
            
        # Check cache first
        cache_key = self._generate_cache_key("get_account_hierarchy", validated_customer_id)
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
        
        # First get all accessible accounts
        accounts = await self.list_accessible_accounts()
        
        # Then build the hierarchy
        hierarchy = {
            "id": validated_customer_id,
            "children": []
        }
        
        # Add account details
        for account in accounts:
            if account["id"] == validated_customer_id:
                hierarchy["name"] = account["name"]
                break
                
        # For now, we're just adding all other accounts as children
        # In a more complex implementation, we would determine the actual parent-child relationships
        for account in accounts:
            if account["id"] != validated_customer_id:
                hierarchy["children"].append({
                    "id": account["id"],
                    "name": account["name"],
                    "children": []  # Placeholder for future expansion
                })
                
        self.logger.info(f"Built account hierarchy for customer ID {validated_customer_id} with {len(hierarchy['children'])} child accounts")
        
        # Cache the results
        self._cache_data(cache_key, hierarchy)
        
        return hierarchy 