"""
Google Ads Client with SQLite-based Caching

This module provides an enhanced version of the GoogleAdsService that uses 
SQLite-based caching instead of in-memory caching for better performance
and persistence across server restarts.
"""

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

from .client_base import GoogleAdsClient, GoogleAdsClientError
from ..db.interface import DatabaseInterface
from ..db.factory import get_database_manager
from ..utils.api_tracker import APICallTracker
from .batch_operations import BatchManager

# Import utilities
from ..utils.logging import get_logger
from ..utils.validation import (
    validate_customer_id,
    validate_positive_integer,
    validate_enum
)
from ..utils.error_handler import (
    handle_exception,
    handle_google_ads_exception,
    CATEGORY_API_ERROR,
    CATEGORY_CACHE,
    CATEGORY_CONFIG,
    SEVERITY_ERROR,
    SEVERITY_WARNING
)
from ..utils.formatting import clean_customer_id, micros_to_currency

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

VALID_DB_TYPES = ["sqlite", "postgres"] # Defined here as well for __init__ validation

class GoogleAdsServiceWithSQLiteCache(GoogleAdsClient):
    """Enhanced service for interacting with the Google Ads API with SQLite-based caching."""
    
    def __init__(
        self, 
        cache_enabled: bool = True, 
        cache_ttl: int = 3600, 
        db_manager: Optional[DatabaseInterface] = None,
        db_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Google Ads service with database-based caching.
        
        Args:
            cache_enabled: Whether to enable caching (default: True)
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
            db_manager: Optional DatabaseInterface instance to use
            db_config: Optional database configuration dictionary
                       For SQLite: {'db_path': '/path/to/db.sqlite', 'auto_clean_interval': 3600}
                       For PostgreSQL: {'host': 'localhost', 'port': 5432, 'database': 'db_name', ...}
        """
        # Call the parent class's __init__ method to set up the base client
        super().__init__()
        
        # Ensure logger exists (might be skipped by patched base init in tests)
        if not hasattr(self, 'logger'):
            # Use get_logger
            self.logger = get_logger(self.__class__.__name__)
            self.logger.warning("Base class did not initialize logger, initializing locally.")
            
        # Set up caching-specific attributes
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        
        context = {"method": "__init__", "cache_enabled": cache_enabled, "cache_ttl": cache_ttl}
        
        # Initialize the database manager if caching is enabled
        if cache_enabled:
            # Validate TTL
            if not validate_positive_integer(cache_ttl):
                 raise ValueError("cache_ttl must be a positive integer")
            context["cache_ttl"] = cache_ttl

            try:
                if db_manager is not None:
                    self.db_manager = db_manager
                    self.logger.info("Using provided database manager for caching")
                else:
                    # Determine DB type, validate if needed
                    if db_config and 'db_type' in db_config:
                         db_type_to_use = db_config['db_type'].lower()
                         if not validate_enum(db_type_to_use, VALID_DB_TYPES):
                              raise ValueError(f"Invalid db_type in db_config: {db_config['db_type']}. Must be one of {VALID_DB_TYPES}")
                    else:
                         db_type_to_use = os.environ.get("DB_TYPE", "sqlite").lower()
                         if not validate_enum(db_type_to_use, VALID_DB_TYPES):
                              raise ValueError(f"Invalid DB_TYPE environment variable: {os.environ.get('DB_TYPE')}. Must be one of {VALID_DB_TYPES}")
                    context["db_type"] = db_type_to_use
                    
                    # Populate db_config from environment if needed
                    if db_config is None: db_config = {}
                    if db_type_to_use == "sqlite" and "db_path" not in db_config:
                        db_path = os.environ.get("DB_PATH")
                        if db_path: db_config["db_path"] = db_path
                    if db_type_to_use == "postgres":
                        for param in ["host", "port", "database", "user", "password"]:
                            env_var = f"POSTGRES_{param.upper()}"
                            if os.environ.get(env_var) and param not in db_config:
                                db_config[param] = os.environ.get(env_var)
                    
                    self.logger.info(f"Attempting to initialize DB manager for type: {db_type_to_use}")
                    self.db_manager = get_database_manager(
                        db_type=db_type_to_use,
                        db_config=db_config
                    )
                self.logger.info(f"Initialized caching with TTL of {cache_ttl} seconds using {self.db_manager.__class__.__name__}")
            except ValueError as ve:
                 error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_CONFIG)
                 self.logger.warning(f"Invalid configuration for cache DB: {error_details.message}")
                 raise GoogleAdsClientError(f"Invalid cache configuration: {error_details.message}") from ve
            except Exception as e:
                 error_details = handle_exception(e, context=context, category=CATEGORY_CONFIG)
                 self.logger.error(f"Failed to initialize cache database manager: {error_details.message}")
                 raise GoogleAdsClientError(f"Cache database initialization failed: {error_details.message}") from e
        
        # Initialize API Call Tracker for query analysis
        self.api_tracker = APICallTracker(enabled=True)
        
        # Initialize batch manager for batch operations
        self._batch_manager = None
        
        self.logger.info(f"Caching {'enabled' if cache_enabled else 'disabled'} with TTL of {cache_ttl} seconds")
        self.logger.info(f"API call tracking enabled for analysis")
    
    @property
    def batch_manager(self) -> BatchManager:
        """
        Get the batch manager for batch operations.
        
        Returns:
            Batch manager instance
        """
        if not self._batch_manager:
            self._batch_manager = BatchManager(self)
            self.logger.info("Created new batch manager for batch operations")
        
        return self._batch_manager
    
    def create_batch(self) -> BatchManager:
        """
        Create a new batch manager for batch operations.
        
        Returns:
            New batch manager instance
        """
        self._batch_manager = BatchManager(self)
        self.logger.info("Created new batch manager for batch operations")
        return self._batch_manager

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
        # Standardize: only include kwargs relevant to the query itself
        # Exclude args if they are not consistently used or stable for caching keys
        key_kwargs = {k: v for k, v in kwargs.items() if k in ['customer_id', 'start_date', 'end_date', 'campaign_id', 'ad_group_id', 'query']} 
        call_repr = {
            "method": method_name,
            # "args": args, # Consider if args are needed and stable
            "kwargs": key_kwargs
        }
        
        # Convert to a stable JSON string and hash it
        json_str = json.dumps(call_repr, sort_keys=True)
        return hashlib.md5(json_str.encode()).hexdigest()
    
    def _get_cached_data(self, method_name: str, *args, **kwargs) -> Optional[Any]:
        """
        Get data from cache if it exists and is not expired.
        
        Args:
            method_name: The name of the method being called
            *args: Positional arguments to the method
            **kwargs: Keyword arguments to the method
            
        Returns:
            The cached data or None if not found or expired
        """
        if not self.cache_enabled:
            return None
            
        # Determine customer ID for this method call
        customer_id = None
        for arg_name, arg_value in kwargs.items():
            if arg_name == 'customer_id' and arg_value:
                customer_id = arg_value
                break
        
        if not customer_id:
            # Check if customer_id is in args
            for arg in args:
                if isinstance(arg, str) and len(arg) == 10 and arg.isdigit():
                    customer_id = arg
                    break
            
            if not customer_id:
                customer_id = self.client_customer_id
        
        # Generate cache key
        cache_key = self._generate_cache_key(method_name, *args, **kwargs)
        
        # Get data from cache
        result = self.db_manager.get_api_response(
            customer_id=customer_id,
            query_type=method_name,
            query_params={"args": args, "kwargs": kwargs}
        )
        
        if result is not None:
            self.logger.info(f"Cache hit for method {method_name}, key: {cache_key}")
            if MONITORING_ENABLED:
                record_cache_hit()
            return result
        
        self.logger.info(f"Cache miss for method {method_name}, key: {cache_key}")
        if MONITORING_ENABLED:
            record_cache_miss()
        return None
    
    def _cache_data(self, method_name: str, data: Any, *args, **kwargs) -> None:
        """
        Store data in the cache.
        
        Args:
            method_name: The name of the method being called
            data: The data to cache
            *args: Positional arguments to the method
            **kwargs: Keyword arguments to the method
        """
        if not self.cache_enabled:
            return
            
        # Determine customer ID for this method call
        customer_id = None
        for arg_name, arg_value in kwargs.items():
            if arg_name == 'customer_id' and arg_value:
                customer_id = arg_value
                break
        
        if not customer_id:
            # Check if customer_id is in args
            for arg in args:
                if isinstance(arg, str) and len(arg) == 10 and arg.isdigit():
                    customer_id = arg
                    break
            
            if not customer_id:
                customer_id = self.client_customer_id
        
        # Generate cache key
        cache_key = self._generate_cache_key(method_name, *args, **kwargs)
        
        # Store data in cache
        self.db_manager.store_api_response(
            customer_id=customer_id,
            query_type=method_name,
            query_params={"args": args, "kwargs": kwargs},
            response_data=data,
            ttl_seconds=self.cache_ttl
        )
        
        self.logger.info(f"Cached data for method {method_name}, key: {cache_key}")
    
    def _clear_cache(self) -> None:
        """Clear all cached data."""
        if self.cache_enabled:
            self.db_manager.clear_cache()
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

    async def _execute_query(self, 
                          method_name: str, 
                          query: str, 
                          customer_id: str, 
                          process_results_func: Optional[callable] = None, 
                          fetch_all_fields: bool = False,
                          use_paging: bool = False,
                          page_size: int = 1000,
                          **kwargs) -> Any:
        """
        Execute a GAQL query with logging and caching.
        
        Args:
            method_name: The name of the method being called (for caching and logging)
            query: The GAQL query string to execute
            customer_id: The customer ID to execute the query against
            process_results_func: Optional function to process the results
            fetch_all_fields: Whether to include all fields in the SELECT clause
            use_paging: Whether to use pagination for large result sets
            page_size: Number of results per page when using pagination
            **kwargs: Additional parameters to include in the cache key
            
        Returns:
            Processed query results (depends on process_results_func)
        """
        # Generate cache key parameters including the query
        cache_params = {
            'query': query,
            'customer_id': customer_id,
            **kwargs
        }
        
        # Check cache first
        cached_data = self._get_cached_data(method_name, **cache_params)
        if cached_data is not None:
            # Track as cache hit
            with self.api_tracker.track_call(
                method_name=method_name,
                customer_id=customer_id,
                parameters=cache_params,
                query_hash=self._generate_cache_key(method_name, **cache_params)
            ) as tracker:
                tracker.set_cache_status("HIT")
            return cached_data
            
        # Log query details before execution
        query_size = len(query)
        query_hash = self._generate_cache_key(method_name, **cache_params)
        self.logger.info(f"Executing GAQL query for {method_name}, customer ID: {customer_id}, query size: {query_size} bytes")
        self.logger.debug(f"GAQL query: {query}")
        
        # Use API tracker to monitor this API call
        with self.api_tracker.track_call(
            method_name=method_name,
            customer_id=customer_id,
            parameters=cache_params,
            query_hash=query_hash
        ) as tracker:
            tracker.set_cache_status("MISS")
            
            try:
                # Get Google Ads service
                ga_service = self.client.get_service("GoogleAdsService")
                
                # Execute the query with or without paging
                start_time = time.time()
                
                if use_paging:
                    self.logger.info(f"Using paging for query with page_size={page_size}")
                    # Use the search_paged approach for large result sets
                    result = None
                    row_count = 0
                    all_rows = []
                    
                    # Create a search request
                    search_request = self.client.get_type("SearchGoogleAdsRequest")
                    search_request.customer_id = customer_id
                    search_request.query = query
                    search_request.page_size = page_size
                    
                    # Get an iterable which will return all pages
                    pager = ga_service.search(request=search_request)
                    
                    # Iterate through the pages
                    for page in pager:
                        page_row_count = 0
                        for row in page.results:
                            all_rows.append(row)
                            page_row_count += 1
                            row_count += 1
                        
                        self.logger.info(f"Retrieved page with {page_row_count} rows, total so far: {row_count}")
                    
                    if process_results_func:
                        # Process all the rows together
                        result, _ = process_results_func(all_rows)
                    else:
                        result = all_rows
                else:
                    # Use the standard approach for regular queries
                    response = ga_service.search(
                        customer_id=customer_id,
                        query=query,
                        retry=None  # Using default retry strategy
                    )
                    
                    # Process the results
                    result = None
                    row_count = 0
                    
                    if process_results_func:
                        # Use the provided function to process results
                        result, row_count = process_results_func(response)
                    else:
                        # Default processing (collect all rows)
                        rows = []
                        for row in response:
                            rows.append(row)
                            row_count += 1
                        result = rows
                
                # Log execution details
                execution_time = (time.time() - start_time) * 1000  # ms
                self.logger.info(f"Query returned {row_count} rows in {execution_time:.2f}ms")
                
                # Additional metadata for API tracking
                tracker.set_response_size(len(json.dumps(str(result))) if result else 0)
                
                # Cache the results
                self._cache_data(method_name, result, **cache_params)
                
                return result
                
            except GoogleAdsException as ex:
                self.logger.error(f"Google Ads API request failed for customer ID {customer_id}: {ex}")
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
                self.logger.error(f"Unexpected error during Google Ads API request for customer ID {customer_id}: {str(e)}")
                raise GoogleAdsClientError(f"Unexpected error: {str(e)}")

    @monitor_google_ads_api("list_accessible_accounts")
    async def list_accessible_accounts(self) -> List[Dict[str, str]]:
        """
        List all accounts accessible from the MCC account.
        
        Returns:
            List of accessible accounts with their IDs and names
        """
        # Check cache first
        cached_data = self._get_cached_data("list_accessible_accounts")
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
            self._cache_data("list_accessible_accounts", accounts)
            
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
        
        # OPTIMIZATION: 
        # 1. Only request fields that are actually used in the processing function
        # 2. Added explicit ACTIVE status filter to avoid retrieving removed campaigns
        # 3. Added metrics filters to avoid retrieving campaigns with no impressions
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
            WHERE 
                segments.date BETWEEN '{start_date}' AND '{end_date}'
                AND campaign.status != 'REMOVED'
                AND metrics.impressions > 0
            ORDER BY metrics.impressions DESC
        """
        
        # Define results processing function
        def process_results(response):
            campaigns = []
            row_count = 0
            
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
                row_count += 1
            
            return campaigns, row_count
        
        # Execute query using centralized method, including date parameters for cache key
        return await self._execute_query(
            method_name="get_campaigns",
            query=query,
            customer_id=validated_customer_id,
            process_results_func=process_results,
            start_date=start_date,
            end_date=end_date
        )

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
        
        # OPTIMIZATION:
        # 1. Only selecting metrics fields that are needed for summary calculation
        # 2. No additional WHERE filtering needed as we want all date-range data
        # 3. No ORDER BY needed as we're aggregating all results anyway
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
        
        # Define results processing function
        def process_results(response):
            # Initialize counters
            total_impressions = 0
            total_clicks = 0
            total_cost_micros = 0
            total_conversions = 0
            total_conversion_value = 0
            row_count = 0
            
            for row in response:
                total_impressions += row.metrics.impressions
                total_clicks += row.metrics.clicks
                total_cost_micros += row.metrics.cost_micros
                total_conversions += row.metrics.conversions
                total_conversion_value += row.metrics.conversions_value
                row_count += 1
            
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
            
            return summary, row_count
            
        # Execute query using centralized method
        return await self._execute_query(
            method_name="get_account_summary",
            query=query,
            customer_id=validated_customer_id,
            process_results_func=process_results,
            start_date=start_date,
            end_date=end_date
        )

    # Utility method to update customer budgets
    @monitor_google_ads_api("update_campaign_budget")
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
            
        # Track this mutation API call
        parameters = {
            'budget_id': budget_id,
            'amount_micros': amount_micros,
            'customer_id': validated_customer_id
        }
        
        # Generate query hash for consistency with other API calls
        query_hash = self._generate_cache_key("update_campaign_budget", **parameters)
        
        with self.api_tracker.track_call(
            method_name="update_campaign_budget",
            customer_id=validated_customer_id,
            parameters=parameters,
            query_hash=query_hash
        ) as tracker:
            # This is a mutation, so no cache is used
            tracker.set_cache_status("N/A")
            
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
                
                # Measure execution time
                start_time = time.time()
                
                # Send the update operation
                response = campaign_budget_service.mutate_campaign_budgets(
                    customer_id=validated_customer_id,
                    operations=[campaign_budget_operation]
                )
                
                # Calculate execution time
                execution_time = (time.time() - start_time) * 1000  # ms
                self.logger.info(f"Budget update completed in {execution_time:.2f}ms")
                
                # Process and return the response
                updated_budget = {
                    "budget_id": budget_id,
                    "resource_name": response.results[0].resource_name,
                    "amount_micros": amount_micros,
                    "amount_dollars": amount_micros / 1000000
                }
                
                # Clear any cached data related to budgets for this customer
                if self.cache_enabled:
                    # This is a write operation, so clear any budget-related cache
                    self.db_manager.clear_cache('budget', customer_id=validated_customer_id)
                    self.logger.info(f"Cleared budget cache for customer ID {validated_customer_id}")
                
                self.logger.info(f"Updated budget {budget_id} for customer ID {validated_customer_id} to {amount_micros} micros (${amount_micros/1000000:.2f})")
                
                # Set response size for tracking
                tracker.set_response_size(len(json.dumps(updated_budget)))
                
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

    @monitor_google_ads_api("get_keywords")
    async def get_keywords(self, 
                         campaign_id: Optional[str] = None, 
                         ad_group_id: Optional[str] = None,
                         start_date: Optional[str] = None, 
                         end_date: Optional[str] = None, 
                         customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get keyword performance data with pagination support for the specified parameters.
        
        Args:
            campaign_id: Optional campaign ID to filter by
            ad_group_id: Optional ad group ID to filter by
            start_date: Optional start date in YYYY-MM-DD format (defaults to last 30 days)
            end_date: Optional end date in YYYY-MM-DD format (defaults to today)
            customer_id: Optional customer ID (defaults to client_customer_id if not provided)
            
        Returns:
            List of keyword data dictionaries
        """
        # Validate the customer ID
        try:
            validated_customer_id = self._validate_customer_id(customer_id)
        except GoogleAdsClientError as e:
            self.logger.error(f"Customer ID validation failed: {str(e)}")
            raise
        
        # Set default date range if not provided
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Build filters
        filters = [f"segments.date BETWEEN '{start_date}' AND '{end_date}'"]
        
        if campaign_id:
            filters.append(f"ad_group.campaign = '{campaign_id}'")
        
        if ad_group_id:
            filters.append(f"ad_group.id = {ad_group_id}")
        
        # OPTIMIZATION:
        # 1. Only select the fields we actually need
        # 2. Filter by status to exclude removed keywords
        # 3. Support filtering by campaign or ad group
        # 4. Order by impressions desc to get the most important keywords first
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
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.average_cpc
            FROM keyword_view
            WHERE {" AND ".join(filters)}
                AND ad_group_criterion.status != 'REMOVED'
            ORDER BY metrics.impressions DESC
        """
        
        # Define results processing function
        def process_results(response):
            keywords = []
            row_count = 0
            
            for row in response:
                keyword = {
                    "id": row.ad_group_criterion.criterion_id,
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
                    "metrics": {
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "cost": row.metrics.cost_micros / 1000000,  # Convert micros to dollars
                        "conversions": row.metrics.conversions,
                        "conversion_value": row.metrics.conversions_value,
                        "average_cpc": row.metrics.average_cpc / 1000000 if row.metrics.average_cpc else 0
                    }
                }
                keywords.append(keyword)
                row_count += 1
            
            return keywords, row_count
        
        # Execute query using centralized method with paging enabled
        # Keywords can potentially have thousands of entries, so paging is important
        return await self._execute_query(
            method_name="get_keywords",
            query=query,
            customer_id=validated_customer_id,
            process_results_func=process_results,
            use_paging=True,
            page_size=5000,  # Large page size for efficiency
            campaign_id=campaign_id,
            ad_group_id=ad_group_id,
            start_date=start_date,
            end_date=end_date
        ) 

    async def update_campaign_budgets_batch(self, 
                                          updates: List[Dict[str, Any]], 
                                          customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Update multiple campaign budgets in a single batch operation.
        
        Args:
            updates: List of budget updates, each containing 'budget_id' and 'amount_micros'
            customer_id: Optional customer ID (defaults to client_customer_id if not provided)
            
        Returns:
            List of results for each budget update
        """
        # Validate the customer ID
        try:
            validated_customer_id = self._validate_customer_id(customer_id)
        except GoogleAdsClientError as e:
            self.logger.error(f"Customer ID validation failed: {str(e)}")
            raise
        
        if not updates:
            self.logger.warning("No updates provided for batch update")
            return []
            
        # Create a new batch for these operations
        batch = self.create_batch()
        
        # Add each budget update to the batch
        for update in updates:
            budget_id = update.get("budget_id")
            amount_micros = update.get("amount_micros")
            
            if not budget_id or not amount_micros:
                self.logger.warning(f"Skipping invalid update (missing required fields): {update}")
                continue
                
            batch.add_campaign_budget_update(
                budget_id=budget_id,
                amount_micros=amount_micros,
                customer_id=validated_customer_id
            )
        
        # Execute the batch and return results
        with self.api_tracker.track_call(
            method_name="update_campaign_budgets_batch",
            customer_id=validated_customer_id,
            parameters={"updates_count": len(updates)},
            query_hash=self._generate_cache_key("update_campaign_budgets_batch", **{"updates": updates})
        ) as tracker:
            try:
                # Execute batch operations
                start_time = time.time()
                results = await batch.execute_batch()
                execution_time = (time.time() - start_time) * 1000  # ms
                
                self.logger.info(f"Batch update of {len(updates)} budgets completed in {execution_time:.2f}ms")
                tracker.set_response_size(len(json.dumps(results)))
                
                # Clear any cached data related to budgets for this customer
                if self.cache_enabled:
                    self.db_manager.clear_cache('budget', customer_id=validated_customer_id)
                    self.logger.info(f"Cleared budget cache for customer ID {validated_customer_id}")
                
                return results
            
            except Exception as e:
                error_msg = f"Error in batch update: {str(e)}"
                self.logger.error(error_msg)
                raise GoogleAdsClientError(error_msg) 