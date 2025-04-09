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
        
    @monitor_google_ads_api("get_labels")
    async def get_labels(self, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all labels defined in the Google Ads account.
        
        Args:
            customer_id: Optional customer ID (defaults to client_customer_id if not provided)
            
        Returns:
            List of label dictionaries containing id, name, status, and attributes
        """
        # Validate the customer ID
        try:
            validated_customer_id = self._validate_customer_id(customer_id)
        except GoogleAdsClientError as e:
            self.logger.error(f"Customer ID validation failed: {str(e)}")
            raise
        
        # Check cache first
        cache_key = self._generate_cache_key("get_labels", validated_customer_id)
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
            
        query = f"""
            SELECT
                label.id,
                label.name,
                label.status,
                label.text_label.background_color,
                label.text_label.description
            FROM label
            ORDER BY label.name
        """
        
        self.logger.info(f"Executing labels query for customer ID {validated_customer_id}")
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
            labels = []
            for row in response:
                label = {
                    "id": row.label.id,
                    "name": row.label.name,
                    "status": row.label.status.name,
                    "background_color": row.label.text_label.background_color if row.label.text_label.background_color else None,
                    "description": row.label.text_label.description if row.label.text_label.description else None
                }
                labels.append(label)
            
            self.logger.info(f"Retrieved {len(labels)} labels for customer ID {validated_customer_id}")
            
            # Cache the results
            self._cache_data(cache_key, labels)
            
            return labels
            
        except GoogleAdsException as ex:
            self.logger.error(f"Google Ads API request failed for customer ID {validated_customer_id}: {ex}")
            error_details = []
            for error in ex.failure.errors:
                error_details.append(f"{error.error_code.name}: {error.message}")
            error_message = "Google Ads API errors:\n" + "\n".join(error_details)
            raise GoogleAdsClientError(error_message)
        except Exception as e:
            self.logger.error(f"Unexpected error during Google Ads API request for customer ID {validated_customer_id}: {str(e)}")
            raise GoogleAdsClientError(f"Unexpected error: {str(e)}")
    
    @monitor_google_ads_api("get_campaigns_by_label")
    async def get_campaigns_by_label(self, label_id: str, start_date: str = None, end_date: str = None, 
                                  customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get campaigns that have the specified label, along with performance data.
        
        Args:
            label_id: The ID of the label to filter by
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            customer_id: Optional customer ID (defaults to client_customer_id if not provided)
            
        Returns:
            List of campaign dictionaries with performance metrics
        """
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
        # Validate the customer ID
        try:
            validated_customer_id = self._validate_customer_id(customer_id)
        except GoogleAdsClientError as e:
            self.logger.error(f"Customer ID validation failed: {str(e)}")
            raise
        
        # Check cache first
        cache_key = self._generate_cache_key("get_campaigns_by_label", label_id, start_date, end_date, validated_customer_id)
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
            
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign_label.label,
                label.id,
                label.name,
                label.status,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value
            FROM campaign
            JOIN campaign_label ON campaign.id = campaign_label.campaign
            JOIN label ON campaign_label.label = label.resource_name
            WHERE 
                label.id = {label_id}
                AND segments.date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY campaign.name
        """
        
        self.logger.info(f"Executing campaigns-by-label query for customer ID {validated_customer_id}, label ID {label_id}")
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
            seen_campaign_ids = set()  # To avoid duplicates due to date segmentation
            
            for row in response:
                campaign_id = row.campaign.id
                
                # Skip if we've already processed this campaign
                if campaign_id in seen_campaign_ids:
                    continue
                    
                seen_campaign_ids.add(campaign_id)
                
                campaign = {
                    "id": campaign_id,
                    "name": row.campaign.name,
                    "status": row.campaign.status.name,
                    "channel_type": row.campaign.advertising_channel_type.name,
                    "label": {
                        "id": row.label.id,
                        "name": row.label.name
                    },
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "cost": row.metrics.cost_micros / 1000000,  # Convert micros to dollars
                    "conversions": row.metrics.conversions,
                    "conversion_value": row.metrics.conversions_value
                }
                
                # Calculate derived metrics
                if campaign["impressions"] > 0:
                    campaign["ctr"] = (campaign["clicks"] / campaign["impressions"]) * 100
                else:
                    campaign["ctr"] = 0
                    
                if campaign["clicks"] > 0:
                    campaign["cpc"] = campaign["cost"] / campaign["clicks"]
                else:
                    campaign["cpc"] = 0
                    
                if campaign["conversions"] > 0:
                    campaign["cpa"] = campaign["cost"] / campaign["conversions"]
                else:
                    campaign["cpa"] = 0
                
                campaigns.append(campaign)
            
            self.logger.info(f"Retrieved {len(campaigns)} campaigns with label ID {label_id} for customer ID {validated_customer_id}")
            
            # Cache the results
            self._cache_data(cache_key, campaigns)
            
            return campaigns
            
        except GoogleAdsException as ex:
            self.logger.error(f"Google Ads API request failed for customer ID {validated_customer_id}: {ex}")
            error_details = []
            for error in ex.failure.errors:
                error_details.append(f"{error.error_code.name}: {error.message}")
            error_message = "Google Ads API errors:\n" + "\n".join(error_details)
            raise GoogleAdsClientError(error_message)
        except Exception as e:
            self.logger.error(f"Unexpected error during Google Ads API request for customer ID {validated_customer_id}: {str(e)}")
            raise GoogleAdsClientError(f"Unexpected error: {str(e)}")
    
    @monitor_google_ads_api("get_ad_groups_by_label")
    async def get_ad_groups_by_label(self, label_id: str, start_date: str = None, end_date: str = None, 
                                  customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get ad groups that have the specified label, along with performance data.
        
        Args:
            label_id: The ID of the label to filter by
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            customer_id: Optional customer ID (defaults to client_customer_id if not provided)
            
        Returns:
            List of ad group dictionaries with performance metrics
        """
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
        # Validate the customer ID
        try:
            validated_customer_id = self._validate_customer_id(customer_id)
        except GoogleAdsClientError as e:
            self.logger.error(f"Customer ID validation failed: {str(e)}")
            raise
        
        # Check cache first
        cache_key = self._generate_cache_key("get_ad_groups_by_label", label_id, start_date, end_date, validated_customer_id)
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
            
        query = f"""
            SELECT
                ad_group.id,
                ad_group.name,
                ad_group.status,
                campaign.id,
                campaign.name,
                ad_group_label.label,
                label.id,
                label.name,
                label.status,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value
            FROM ad_group
            JOIN campaign ON ad_group.campaign = campaign.resource_name
            JOIN ad_group_label ON ad_group.id = ad_group_label.ad_group
            JOIN label ON ad_group_label.label = label.resource_name
            WHERE 
                label.id = {label_id}
                AND segments.date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY ad_group.name
        """
        
        self.logger.info(f"Executing ad-groups-by-label query for customer ID {validated_customer_id}, label ID {label_id}")
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
            ad_groups = []
            seen_ad_group_ids = set()  # To avoid duplicates due to date segmentation
            
            for row in response:
                ad_group_id = row.ad_group.id
                
                # Skip if we've already processed this ad group
                if ad_group_id in seen_ad_group_ids:
                    continue
                    
                seen_ad_group_ids.add(ad_group_id)
                
                ad_group = {
                    "id": ad_group_id,
                    "name": row.ad_group.name,
                    "status": row.ad_group.status.name,
                    "campaign": {
                        "id": row.campaign.id,
                        "name": row.campaign.name
                    },
                    "label": {
                        "id": row.label.id,
                        "name": row.label.name
                    },
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "cost": row.metrics.cost_micros / 1000000,  # Convert micros to dollars
                    "conversions": row.metrics.conversions,
                    "conversion_value": row.metrics.conversions_value
                }
                
                # Calculate derived metrics
                if ad_group["impressions"] > 0:
                    ad_group["ctr"] = (ad_group["clicks"] / ad_group["impressions"]) * 100
                else:
                    ad_group["ctr"] = 0
                    
                if ad_group["clicks"] > 0:
                    ad_group["cpc"] = ad_group["cost"] / ad_group["clicks"]
                else:
                    ad_group["cpc"] = 0
                    
                if ad_group["conversions"] > 0:
                    ad_group["cpa"] = ad_group["cost"] / ad_group["conversions"]
                else:
                    ad_group["cpa"] = 0
                
                ad_groups.append(ad_group)
            
            self.logger.info(f"Retrieved {len(ad_groups)} ad groups with label ID {label_id} for customer ID {validated_customer_id}")
            
            # Cache the results
            self._cache_data(cache_key, ad_groups)
            
            return ad_groups
            
        except GoogleAdsException as ex:
            self.logger.error(f"Google Ads API request failed for customer ID {validated_customer_id}: {ex}")
            error_details = []
            for error in ex.failure.errors:
                error_details.append(f"{error.error_code.name}: {error.message}")
            error_message = "Google Ads API errors:\n" + "\n".join(error_details)
            raise GoogleAdsClientError(error_message)
        except Exception as e:
            self.logger.error(f"Unexpected error during Google Ads API request for customer ID {validated_customer_id}: {str(e)}")
            raise GoogleAdsClientError(f"Unexpected error: {str(e)}")
    
    @monitor_google_ads_api("get_ads_by_label")
    async def get_ads_by_label(self, label_id: str, start_date: str = None, end_date: str = None, 
                            customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get ads that have the specified label, along with performance data.
        
        Args:
            label_id: The ID of the label to filter by
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            customer_id: Optional customer ID (defaults to client_customer_id if not provided)
            
        Returns:
            List of ad dictionaries with performance metrics
        """
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
        # Validate the customer ID
        try:
            validated_customer_id = self._validate_customer_id(customer_id)
        except GoogleAdsClientError as e:
            self.logger.error(f"Customer ID validation failed: {str(e)}")
            raise
        
        # Check cache first
        cache_key = self._generate_cache_key("get_ads_by_label", label_id, start_date, end_date, validated_customer_id)
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
            
        query = f"""
            SELECT
                ad_group_ad.ad.id,
                ad_group_ad.ad.name,
                ad_group_ad.ad.type,
                ad_group_ad.status,
                ad_group.id,
                ad_group.name,
                campaign.id,
                campaign.name,
                ad_group_ad_label.label,
                label.id,
                label.name,
                label.status,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value
            FROM ad_group_ad
            JOIN ad_group ON ad_group_ad.ad_group = ad_group.resource_name
            JOIN campaign ON ad_group.campaign = campaign.resource_name
            JOIN ad_group_ad_label ON ad_group_ad.resource_name = ad_group_ad_label.ad_group_ad
            JOIN label ON ad_group_ad_label.label = label.resource_name
            WHERE 
                label.id = {label_id}
                AND segments.date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY ad_group_ad.ad.name
        """
        
        self.logger.info(f"Executing ads-by-label query for customer ID {validated_customer_id}, label ID {label_id}")
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
            ads = []
            seen_ad_ids = set()  # To avoid duplicates due to date segmentation
            
            for row in response:
                ad_id = row.ad_group_ad.ad.id
                
                # Skip if we've already processed this ad
                if ad_id in seen_ad_ids:
                    continue
                    
                seen_ad_ids.add(ad_id)
                
                ad = {
                    "id": ad_id,
                    "name": row.ad_group_ad.ad.name,
                    "type": row.ad_group_ad.ad.type.name,
                    "status": row.ad_group_ad.status.name,
                    "ad_group": {
                        "id": row.ad_group.id,
                        "name": row.ad_group.name
                    },
                    "campaign": {
                        "id": row.campaign.id,
                        "name": row.campaign.name
                    },
                    "label": {
                        "id": row.label.id,
                        "name": row.label.name
                    },
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "cost": row.metrics.cost_micros / 1000000,  # Convert micros to dollars
                    "conversions": row.metrics.conversions,
                    "conversion_value": row.metrics.conversions_value
                }
                
                # Calculate derived metrics
                if ad["impressions"] > 0:
                    ad["ctr"] = (ad["clicks"] / ad["impressions"]) * 100
                else:
                    ad["ctr"] = 0
                    
                if ad["clicks"] > 0:
                    ad["cpc"] = ad["cost"] / ad["clicks"]
                else:
                    ad["cpc"] = 0
                    
                if ad["conversions"] > 0:
                    ad["cpa"] = ad["cost"] / ad["conversions"]
                else:
                    ad["cpa"] = 0
                
                ads.append(ad)
            
            self.logger.info(f"Retrieved {len(ads)} ads with label ID {label_id} for customer ID {validated_customer_id}")
            
            # Cache the results
            self._cache_data(cache_key, ads)
            
            return ads
            
        except GoogleAdsException as ex:
            self.logger.error(f"Google Ads API request failed for customer ID {validated_customer_id}: {ex}")
            error_details = []
            for error in ex.failure.errors:
                error_details.append(f"{error.error_code.name}: {error.message}")
            error_message = "Google Ads API errors:\n" + "\n".join(error_details)
            raise GoogleAdsClientError(error_message)
        except Exception as e:
            self.logger.error(f"Unexpected error during Google Ads API request for customer ID {validated_customer_id}: {str(e)}")
            raise GoogleAdsClientError(f"Unexpected error: {str(e)}")
    
    @monitor_google_ads_api("get_keywords_by_label")
    async def get_keywords_by_label(self, label_id: str, start_date: str = None, end_date: str = None, 
                                customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get keywords that have the specified label, along with performance data.
        
        Args:
            label_id: The ID of the label to filter by
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            customer_id: Optional customer ID (defaults to client_customer_id if not provided)
            
        Returns:
            List of keyword dictionaries with performance metrics
        """
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
        # Validate the customer ID
        try:
            validated_customer_id = self._validate_customer_id(customer_id)
        except GoogleAdsClientError as e:
            self.logger.error(f"Customer ID validation failed: {str(e)}")
            raise
        
        # Check cache first
        cache_key = self._generate_cache_key("get_keywords_by_label", label_id, start_date, end_date, validated_customer_id)
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
            
        query = f"""
            SELECT
                ad_group_criterion.criterion_id,
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                ad_group_criterion.status,
                ad_group.id,
                ad_group.name,
                campaign.id,
                campaign.name,
                ad_group_criterion_label.label,
                label.id,
                label.name,
                label.status,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.average_cpc,
                metrics.ctr
            FROM keyword_view
            JOIN ad_group_criterion ON keyword_view.resource_name = ad_group_criterion.resource_name
            JOIN ad_group ON ad_group_criterion.ad_group = ad_group.resource_name
            JOIN campaign ON ad_group.campaign = campaign.resource_name
            JOIN ad_group_criterion_label ON ad_group_criterion.resource_name = ad_group_criterion_label.ad_group_criterion
            JOIN label ON ad_group_criterion_label.label = label.resource_name
            WHERE 
                label.id = {label_id}
                AND segments.date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY ad_group_criterion.keyword.text
        """
        
        self.logger.info(f"Executing keywords-by-label query for customer ID {validated_customer_id}, label ID {label_id}")
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
            keywords = []
            seen_criterion_ids = set()  # To avoid duplicates due to date segmentation
            
            for row in response:
                criterion_id = row.ad_group_criterion.criterion_id
                
                # Skip if we've already processed this keyword
                if criterion_id in seen_criterion_ids:
                    continue
                    
                seen_criterion_ids.add(criterion_id)
                
                keyword = {
                    "id": criterion_id,
                    "text": row.ad_group_criterion.keyword.text,
                    "match_type": row.ad_group_criterion.keyword.match_type.name,
                    "status": row.ad_group_criterion.status.name,
                    "ad_group": {
                        "id": row.ad_group.id,
                        "name": row.ad_group.name
                    },
                    "campaign": {
                        "id": row.campaign.id,
                        "name": row.campaign.name
                    },
                    "label": {
                        "id": row.label.id,
                        "name": row.label.name
                    },
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "cost": row.metrics.cost_micros / 1000000,  # Convert micros to dollars
                    "conversions": row.metrics.conversions,
                    "conversion_value": row.metrics.conversions_value
                }
                
                # Get CTR from the metrics or calculate it
                if hasattr(row.metrics, 'ctr'):
                    keyword["ctr"] = row.metrics.ctr
                elif keyword["impressions"] > 0:
                    keyword["ctr"] = (keyword["clicks"] / keyword["impressions"]) * 100
                else:
                    keyword["ctr"] = 0
                
                # Get CPC from the metrics or calculate it
                if hasattr(row.metrics, 'average_cpc'):
                    keyword["cpc"] = row.metrics.average_cpc / 1000000  # Convert micros to dollars
                elif keyword["clicks"] > 0:
                    keyword["cpc"] = keyword["cost"] / keyword["clicks"]
                else:
                    keyword["cpc"] = 0
                    
                if keyword["conversions"] > 0:
                    keyword["cpa"] = keyword["cost"] / keyword["conversions"]
                else:
                    keyword["cpa"] = 0
                
                keywords.append(keyword)
            
            self.logger.info(f"Retrieved {len(keywords)} keywords with label ID {label_id} for customer ID {validated_customer_id}")
            
            # Cache the results
            self._cache_data(cache_key, keywords)
            
            return keywords
            
        except GoogleAdsException as ex:
            self.logger.error(f"Google Ads API request failed for customer ID {validated_customer_id}: {ex}")
            error_details = []
            for error in ex.failure.errors:
                error_details.append(f"{error.error_code.name}: {error.message}")
            error_message = "Google Ads API errors:\n" + "\n".join(error_details)
            raise GoogleAdsClientError(error_message)
        except Exception as e:
            self.logger.error(f"Unexpected error during Google Ads API request for customer ID {validated_customer_id}: {str(e)}")
            raise GoogleAdsClientError(f"Unexpected error: {str(e)}")
    
    @monitor_google_ads_api("pause_ad")
    async def pause_ad(self, ad_group_id: str, ad_id: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Pause an ad in Google Ads.
        
        Args:
            ad_group_id: The ad group ID containing the ad
            ad_id: The ID of the ad to pause
            customer_id: Optional customer ID (defaults to client_customer_id if not provided)
            
        Returns:
            Dictionary with operation status and resource name
        """
        # Validate the customer ID
        try:
            validated_customer_id = self._validate_customer_id(customer_id)
        except GoogleAdsClientError as e:
            self.logger.error(f"Customer ID validation failed: {str(e)}")
            raise
            
        try:
            # Get the AdGroupAdService
            ad_group_ad_service = self.client.get_service("AdGroupAdService")
            
            # Create an ad group ad operation
            ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")
            
            # Set update for the ad group ad
            ad_group_ad = ad_group_ad_operation.update
            
            # Create the resource name for the ad
            ad_group_ad.resource_name = ad_group_ad_service.ad_group_ad_path(
                validated_customer_id, ad_group_id, ad_id
            )
            
            # Set the status to PAUSED
            ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum.PAUSED
            
            # Create update mask for the status field
            from google.api_core import protobuf_helpers
            self.client.copy_from(
                ad_group_ad_operation.update_mask,
                protobuf_helpers.field_mask(None, ad_group_ad._pb),
            )
            
            # Submit the operation
            response = ad_group_ad_service.mutate_ad_group_ads(
                customer_id=validated_customer_id, 
                operations=[ad_group_ad_operation]
            )
            
            # Process the response
            result = {
                "status": "SUCCESS",
                "resource_name": response.results[0].resource_name if response.results else None,
                "message": f"Ad successfully paused."
            }
            
            self.logger.info(f"Successfully paused ad for customer ID {validated_customer_id}, ad group ID {ad_group_id}, ad ID {ad_id}")
            
            return result
            
        except GoogleAdsException as ex:
            self.logger.error(f"Failed to pause ad for customer ID {validated_customer_id}, ad group ID {ad_group_id}, ad ID {ad_id}: {ex}")
            error_details = []
            for error in ex.failure.errors:
                error_details.append(f"{error.error_code.name}: {error.message}")
            error_message = "Google Ads API errors:\n" + "\n".join(error_details)
            raise GoogleAdsClientError(error_message)
        except Exception as e:
            self.logger.error(f"Unexpected error pausing ad: {str(e)}")
            raise GoogleAdsClientError(f"Unexpected error: {str(e)}")
    
    @monitor_google_ads_api("create_responsive_search_ad")
    async def create_responsive_search_ad(
        self, 
        ad_group_id: str, 
        headlines: List[str], 
        descriptions: List[str], 
        final_url: str, 
        path1: Optional[str] = None, 
        path2: Optional[str] = None, 
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new responsive search ad.
        
        Args:
            ad_group_id: The ad group ID where to create the ad
            headlines: List of headlines for the ad (3-15 allowed)
            descriptions: List of descriptions for the ad (2-4 allowed)
            final_url: The URL for the ad
            path1: Optional first path for the display URL
            path2: Optional second path for the display URL
            customer_id: Optional customer ID (defaults to client_customer_id if not provided)
            
        Returns:
            Dictionary with operation status and resource name
        """
        # Validate the customer ID
        try:
            validated_customer_id = self._validate_customer_id(customer_id)
        except GoogleAdsClientError as e:
            self.logger.error(f"Customer ID validation failed: {str(e)}")
            raise
            
        # Validate ad elements
        if len(headlines) < 3 or len(headlines) > 15:
            raise GoogleAdsClientError("Responsive search ads require 3-15 headlines")
            
        if len(descriptions) < 2 or len(descriptions) > 4:
            raise GoogleAdsClientError("Responsive search ads require 2-4 descriptions")
            
        if not final_url:
            raise GoogleAdsClientError("Final URL is required")
            
        # If path2 is specified, path1 must also be specified
        if path2 and not path1:
            raise GoogleAdsClientError("Path1 must be specified if Path2 is specified")
            
        try:
            # Get the AdGroupAdService
            ad_group_ad_service = self.client.get_service("AdGroupAdService")
            ad_group_service = self.client.get_service("AdGroupService")
            
            # Create an ad group ad operation
            ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")
            ad_group_ad = ad_group_ad_operation.create
            
            # Set the ad group
            ad_group_ad.ad_group = ad_group_service.ad_group_path(
                validated_customer_id, ad_group_id
            )
            
            # Set the status to PAUSED initially for safety
            ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum.PAUSED
            
            # Set the final URL
            ad_group_ad.ad.final_urls.append(final_url)
            
            # Add headlines
            for headline_text in headlines:
                headline = self.client.get_type("AdTextAsset")
                headline.text = headline_text
                ad_group_ad.ad.responsive_search_ad.headlines.append(headline)
                
            # Add descriptions
            for description_text in descriptions:
                description = self.client.get_type("AdTextAsset")
                description.text = description_text
                ad_group_ad.ad.responsive_search_ad.descriptions.append(description)
                
            # Add paths if specified
            if path1:
                ad_group_ad.ad.responsive_search_ad.path1 = path1
                
            if path2:
                ad_group_ad.ad.responsive_search_ad.path2 = path2
                
            # Submit the operation
            response = ad_group_ad_service.mutate_ad_group_ads(
                customer_id=validated_customer_id, 
                operations=[ad_group_ad_operation]
            )
            
            # Process the response
            result = {
                "status": "SUCCESS",
                "resource_name": response.results[0].resource_name if response.results else None,
                "message": f"Responsive search ad successfully created."
            }
            
            self.logger.info(f"Successfully created responsive search ad for customer ID {validated_customer_id}, ad group ID {ad_group_id}")
            
            return result
            
        except GoogleAdsException as ex:
            self.logger.error(f"Failed to create responsive search ad for customer ID {validated_customer_id}, ad group ID {ad_group_id}: {ex}")
            error_details = []
            for error in ex.failure.errors:
                error_details.append(f"{error.error_code.name}: {error.message}")
            error_message = "Google Ads API errors:\n" + "\n".join(error_details)
            raise GoogleAdsClientError(error_message)
        except Exception as e:
            self.logger.error(f"Unexpected error creating responsive search ad: {str(e)}")
            raise GoogleAdsClientError(f"Unexpected error: {str(e)}")
    
    @monitor_google_ads_api("get_ad_groups")
    async def get_ad_groups(self, start_date: str, end_date: str, campaign_id: Optional[str] = None, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get ad group data for the specified date range and customer ID.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            campaign_id: Optional campaign ID to filter by
            customer_id: Optional customer ID (defaults to client_customer_id if not provided)
            
        Returns:
            List of ad group data dictionaries
        """
        # Validate the customer ID
        try:
            validated_customer_id = self._validate_customer_id(customer_id)
        except GoogleAdsClientError as e:
            self.logger.error(f"Customer ID validation failed: {str(e)}")
            raise
        
        # Check cache first
        cache_key = self._generate_cache_key("get_ad_groups", start_date, end_date, campaign_id, validated_customer_id)
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
            
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                ad_group.id,
                ad_group.name,
                ad_group.status,
                ad_group.type,
                ad_group.cpc_bid_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value
            FROM ad_group
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
        """
        
        # Add campaign ID filter if provided
        if campaign_id:
            query += f" AND campaign.id = {campaign_id}"
        
        query += " ORDER BY ad_group.id"
        
        self.logger.info(f"Executing ad_group query for customer ID {validated_customer_id}, date range {start_date} to {end_date}" + 
                        (f", campaign ID {campaign_id}" if campaign_id else ""))
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
            ad_groups = []
            for row in response:
                ad_group = {
                    "campaign_id": row.campaign.id,
                    "campaign_name": row.campaign.name,
                    "id": row.ad_group.id,
                    "name": row.ad_group.name,
                    "status": row.ad_group.status.name,
                    "type": row.ad_group.type_.name,
                    "cpc_bid": row.ad_group.cpc_bid_micros / 1000000 if row.ad_group.cpc_bid_micros else None,  # Convert micros to dollars
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "cost": row.metrics.cost_micros / 1000000,  # Convert micros to dollars
                    "conversions": row.metrics.conversions,
                    "conversion_value": row.metrics.conversions_value
                }
                
                # Calculate derived metrics
                if ad_group["impressions"] > 0:
                    ad_group["ctr"] = (ad_group["clicks"] / ad_group["impressions"]) * 100
                else:
                    ad_group["ctr"] = 0
                
                if ad_group["clicks"] > 0:
                    ad_group["cpc"] = ad_group["cost"] / ad_group["clicks"]
                else:
                    ad_group["cpc"] = 0
                
                if ad_group["conversions"] > 0:
                    ad_group["cost_per_conversion"] = ad_group["cost"] / ad_group["conversions"]
                else:
                    ad_group["cost_per_conversion"] = 0
                
                ad_groups.append(ad_group)
            
            self.logger.info(f"Retrieved {len(ad_groups)} ad groups for customer ID {validated_customer_id}")
            
            # Cache the results
            self._cache_data(cache_key, ad_groups)
            
            return ad_groups
            
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
    
    @monitor_google_ads_api("create_ad_group")
    async def create_ad_group(
        self, 
        campaign_id: str, 
        name: str, 
        status: str = "ENABLED", 
        cpc_bid_micros: Optional[int] = None,
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new ad group in the specified campaign.
        
        Args:
            campaign_id: The campaign ID where the ad group will be created
            name: The name of the ad group
            status: Ad group status (ENABLED, PAUSED, REMOVED)
            cpc_bid_micros: Optional CPC bid in micros (1/1,000,000 of the account currency)
            customer_id: Optional customer ID (defaults to client_customer_id if not provided)
            
        Returns:
            Dictionary with operation status and resource name
        """
        # Validate the customer ID
        try:
            validated_customer_id = self._validate_customer_id(customer_id)
        except GoogleAdsClientError as e:
            self.logger.error(f"Customer ID validation failed: {str(e)}")
            raise
        
        # Validate inputs
        if not campaign_id:
            raise GoogleAdsClientError("Campaign ID is required")
        if not name:
            raise GoogleAdsClientError("Ad group name is required")
        
        # Validate status
        valid_statuses = ["ENABLED", "PAUSED", "REMOVED"]
        if status not in valid_statuses:
            raise GoogleAdsClientError(f"Invalid status: {status}. Must be one of: {', '.join(valid_statuses)}")
        
        try:
            # Get the services
            ad_group_service = self.client.get_service("AdGroupService")
            campaign_service = self.client.get_service("CampaignService")
            
            # Create campaign resource name
            campaign_resource_name = campaign_service.campaign_path(
                validated_customer_id, campaign_id
            )
            
            # Create an ad group operation
            ad_group_operation = self.client.get_type("AdGroupOperation")
            ad_group = ad_group_operation.create
            
            # Set ad group properties
            ad_group.name = name
            ad_group.campaign = campaign_resource_name
            
            # Set status
            if status == "ENABLED":
                ad_group.status = self.client.enums.AdGroupStatusEnum.ENABLED
            elif status == "PAUSED":
                ad_group.status = self.client.enums.AdGroupStatusEnum.PAUSED
            elif status == "REMOVED":
                ad_group.status = self.client.enums.AdGroupStatusEnum.REMOVED
            
            # Set CPC bid if provided
            if cpc_bid_micros is not None:
                ad_group.cpc_bid_micros = cpc_bid_micros
            
            # Submit the operation
            response = ad_group_service.mutate_ad_groups(
                customer_id=validated_customer_id, 
                operations=[ad_group_operation]
            )
            
            # Process the response
            result = {
                "status": "SUCCESS",
                "resource_name": response.results[0].resource_name if response.results else None,
                "message": f"Ad group '{name}' created successfully."
            }
            
            # Clear relevant caches since data has changed
            self._clear_cache_by_prefix("get_ad_groups")
            
            self.logger.info(f"Successfully created ad group '{name}' in campaign {campaign_id} for customer ID {validated_customer_id}")
            
            return result
            
        except GoogleAdsException as ex:
            self.logger.error(f"Failed to create ad group for customer ID {validated_customer_id}, campaign ID {campaign_id}: {ex}")
            error_details = []
            for error in ex.failure.errors:
                error_details.append(f"{error.error_code.name}: {error.message}")
            error_message = "Google Ads API errors:\n" + "\n".join(error_details)
            raise GoogleAdsClientError(error_message)
        except Exception as e:
            self.logger.error(f"Unexpected error creating ad group: {str(e)}")
            raise GoogleAdsClientError(f"Unexpected error: {str(e)}")
    
    @monitor_google_ads_api("update_ad_group")
    async def update_ad_group(
        self, 
        ad_group_id: str, 
        name: Optional[str] = None, 
        status: Optional[str] = None, 
        cpc_bid_micros: Optional[int] = None,
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing ad group.
        
        Args:
            ad_group_id: The ID of the ad group to update
            name: Optional new name for the ad group
            status: Optional new status (ENABLED, PAUSED, REMOVED)
            cpc_bid_micros: Optional new CPC bid in micros (1/1,000,000 of the account currency)
            customer_id: Optional customer ID (defaults to client_customer_id if not provided)
            
        Returns:
            Dictionary with operation status and resource name
        """
        # Validate the customer ID
        try:
            validated_customer_id = self._validate_customer_id(customer_id)
        except GoogleAdsClientError as e:
            self.logger.error(f"Customer ID validation failed: {str(e)}")
            raise
        
        # Validate inputs
        if not ad_group_id:
            raise GoogleAdsClientError("Ad group ID is required")
        
        # Ensure at least one field is being updated
        if name is None and status is None and cpc_bid_micros is None:
            raise GoogleAdsClientError("At least one field (name, status, or cpc_bid_micros) must be provided for update")
        
        # Validate status if provided
        if status is not None:
            valid_statuses = ["ENABLED", "PAUSED", "REMOVED"]
            if status not in valid_statuses:
                raise GoogleAdsClientError(f"Invalid status: {status}. Must be one of: {', '.join(valid_statuses)}")
        
        try:
            # Get the services
            ad_group_service = self.client.get_service("AdGroupService")
            
            # Create ad group resource name
            ad_group_resource_name = ad_group_service.ad_group_path(
                validated_customer_id, ad_group_id
            )
            
            # Create an ad group operation
            ad_group_operation = self.client.get_type("AdGroupOperation")
            ad_group = ad_group_operation.update
            
            # Set ad group resource name
            ad_group.resource_name = ad_group_resource_name
            
            # Track which fields are updated for field mask
            updated_fields = []
            
            # Update name if provided
            if name is not None:
                ad_group.name = name
                updated_fields.append("name")
            
            # Update status if provided
            if status is not None:
                if status == "ENABLED":
                    ad_group.status = self.client.enums.AdGroupStatusEnum.ENABLED
                elif status == "PAUSED":
                    ad_group.status = self.client.enums.AdGroupStatusEnum.PAUSED
                elif status == "REMOVED":
                    ad_group.status = self.client.enums.AdGroupStatusEnum.REMOVED
                updated_fields.append("status")
            
            # Update CPC bid if provided
            if cpc_bid_micros is not None:
                ad_group.cpc_bid_micros = cpc_bid_micros
                updated_fields.append("cpc_bid_micros")
            
            # Create update mask
            from google.api_core import protobuf_helpers
            self.client.copy_from(
                ad_group_operation.update_mask,
                protobuf_helpers.field_mask(None, ad_group._pb),
            )
            
            # Submit the operation
            response = ad_group_service.mutate_ad_groups(
                customer_id=validated_customer_id, 
                operations=[ad_group_operation]
            )
            
            # Process the response
            result = {
                "status": "SUCCESS",
                "resource_name": response.results[0].resource_name if response.results else None,
                "message": f"Ad group with ID {ad_group_id} updated successfully.",
                "updated_fields": updated_fields
            }
            
            # Clear relevant caches since data has changed
            self._clear_cache_by_prefix("get_ad_groups")
            
            self.logger.info(f"Successfully updated ad group {ad_group_id} for customer ID {validated_customer_id}")
            
            return result
            
        except GoogleAdsException as ex:
            self.logger.error(f"Failed to update ad group for customer ID {validated_customer_id}, ad group ID {ad_group_id}: {ex}")
            error_details = []
            for error in ex.failure.errors:
                error_details.append(f"{error.error_code.name}: {error.message}")
            error_message = "Google Ads API errors:\n" + "\n".join(error_details)
            raise GoogleAdsClientError(error_message)
        except Exception as e:
            self.logger.error(f"Unexpected error updating ad group: {str(e)}")
            raise GoogleAdsClientError(f"Unexpected error: {str(e)}")
    
    def _clear_cache_by_prefix(self, prefix: str) -> None:
        """
        Clear all cache entries with keys starting with the given prefix.
        
        Args:
            prefix: The prefix to match against cache keys
        """
        keys_to_remove = [k for k in self.cache.keys() if k.startswith(prefix)]
        for key in keys_to_remove:
            del self.cache[key]
        
        if keys_to_remove:
            self.logger.info(f"Cleared {len(keys_to_remove)} cache entries with prefix '{prefix}'")
    
    @monitor_google_ads_api("get_ad_group_daily_stats")
    async def get_ad_group_daily_stats(self, ad_group_id: str, start_date: str, end_date: str, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get daily performance metrics for a specific ad group.
        
        Args:
            ad_group_id: The ID of the ad group to get data for
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            customer_id: Optional customer ID (defaults to client_customer_id if not provided)
            
        Returns:
            List of daily performance data dictionaries
        """
        # Validate the customer ID
        try:
            validated_customer_id = self._validate_customer_id(customer_id)
        except GoogleAdsClientError as e:
            self.logger.error(f"Customer ID validation failed: {str(e)}")
            raise
        
        # Check cache first
        cache_key = self._generate_cache_key("get_ad_group_daily_stats", ad_group_id, start_date, end_date, validated_customer_id)
        cached_data = self._get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
            
        query = f"""
            SELECT
                segments.date,
                ad_group.id,
                ad_group.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.average_cpc,
                metrics.ctr
            FROM ad_group
            WHERE 
                segments.date BETWEEN '{start_date}' AND '{end_date}'
                AND ad_group.id = {ad_group_id}
            ORDER BY segments.date
        """
        
        self.logger.info(f"Executing daily stats query for ad group {ad_group_id}, customer ID {validated_customer_id}, date range {start_date} to {end_date}")
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
            daily_stats = []
            for row in response:
                stat = {
                    "date": row.segments.date,
                    "ad_group_id": row.ad_group.id,
                    "ad_group_name": row.ad_group.name,
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "cost": row.metrics.cost_micros / 1000000,  # Convert micros to dollars
                    "conversions": row.metrics.conversions,
                    "conversion_value": row.metrics.conversions_value,
                    "cpc": row.metrics.average_cpc / 1000000 if row.metrics.average_cpc > 0 else 0,  # Convert micros to dollars
                    "ctr": row.metrics.ctr  # Already in percentage
                }
                
                # Calculate additional metrics if not provided directly by the API
                if stat["conversions"] > 0:
                    stat["cost_per_conversion"] = stat["cost"] / stat["conversions"]
                else:
                    stat["cost_per_conversion"] = 0
                    
                if stat["conversion_value"] > 0 and stat["cost"] > 0:
                    stat["roas"] = stat["conversion_value"] / stat["cost"]
                else:
                    stat["roas"] = 0
                
                daily_stats.append(stat)
            
            self.logger.info(f"Retrieved {len(daily_stats)} days of performance data for ad group {ad_group_id}")
            
            # Cache the results
            self._cache_data(cache_key, daily_stats)
            
            return daily_stats
            
        except GoogleAdsException as ex:
            self.logger.error(f"Google Ads API request failed for ad group {ad_group_id}, customer ID {validated_customer_id}: {ex}")
            error_details = []
            for error in ex.failure.errors:
                error_details.append(f"{error.error_code.name}: {error.message}")
            error_message = "Google Ads API errors:\n" + "\n".join(error_details)
            raise GoogleAdsClientError(error_message)
        except Exception as e:
            self.logger.error(f"Unexpected error during Google Ads API request: {str(e)}")
            raise GoogleAdsClientError(f"Unexpected error: {str(e)}") 