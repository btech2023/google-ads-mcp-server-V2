"""
Insights Service Module

This module provides services for generating automated insights from Google Ads data,
including anomaly detection, optimization suggestions, and opportunity discovery.
"""

import logging
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import asyncio

# Import underlying services (using relative imports)
from .client import GoogleAdsService
from .keywords import KeywordService
from .search_terms import SearchTermService
from .budgets import BudgetService
from .ad_groups import AdGroupService

# Import utility modules (using relative imports)
from ..utils.logging import get_logger
from ..utils.validation import (
    validate_customer_id,
    validate_date_format,
    validate_date_range,
    validate_enum,
    validate_list_of_strings,
    validate_float_range,
    validate_numeric_range,
    validate_positive_integer
)
from ..utils.error_handler import (
    handle_exception,
    handle_google_ads_exception,
    create_error_response,
    ErrorDetails,
    CATEGORY_BUSINESS_LOGIC,
    CATEGORY_API_ERROR,
    CATEGORY_VALIDATION,
    SEVERITY_ERROR,
    SEVERITY_WARNING
)
from ..utils.formatting import clean_customer_id, format_customer_id

# Initialize logger using utility
logger = get_logger(__name__)

# Define constants for valid enum values
VALID_ENTITY_TYPES = ["CAMPAIGN", "AD_GROUP", "KEYWORD"]
VALID_COMPARISON_PERIODS = ["PREVIOUS_PERIOD", "SAME_PERIOD_LAST_YEAR"]
DEFAULT_METRICS = ["impressions", "clicks", "cost", "ctr", "conversions"]

class InsightsService:
    """
    Service for generating insights from Google Ads data.
    
    This service provides methods for:
    - Detecting performance anomalies
    - Generating optimization suggestions
    - Discovering new opportunities
    """
    
    def __init__(self, google_ads_service: GoogleAdsService):
        """
        Initialize the InsightsService.
        
        Args:
            google_ads_service: The GoogleAdsService instance
        """
        self.google_ads_service = google_ads_service
        self.keyword_service = KeywordService(google_ads_service)
        self.search_term_service = SearchTermService(google_ads_service)
        self.budget_service = BudgetService(google_ads_service)
        self.ad_group_service = AdGroupService(google_ads_service)
        logger.info("InsightsService initialized")
    
    async def detect_performance_anomalies(
        self,
        customer_id: str,
        entity_type: str = "CAMPAIGN",
        entity_ids: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        comparison_period: str = "PREVIOUS_PERIOD",
        threshold: float = 2.0
    ) -> Dict[str, Any]:
        """
        Detect anomalies in performance metrics. 
        Returns a dictionary with results or raises ValueError/RuntimeError on failure.
        
        Args:
            customer_id: Google Ads customer ID
            entity_type: Type of entity to analyze (CAMPAIGN, AD_GROUP, KEYWORD)
            entity_ids: Optional list of entity IDs to filter by
            metrics: List of metrics to analyze (defaults to impressions, clicks, cost, ctr, conversions)
            start_date: Start date for analysis (defaults to 7 days ago)
            end_date: End date for analysis (defaults to today)
            comparison_period: Period to compare against (PREVIOUS_PERIOD, SAME_PERIOD_LAST_YEAR)
            threshold: Z-score threshold for anomaly detection (default: 2.0)
            
        Returns:
            Dictionary containing detected anomalies, or raises an exception.
        """
        context = {
            "customer_id": customer_id,
            "entity_type": entity_type,
            "entity_ids": entity_ids,
            "metrics": metrics,
            "start_date": start_date,
            "end_date": end_date,
            "comparison_period": comparison_period,
            "threshold": threshold,
            "method": "detect_performance_anomalies"
        }

        try:
            # --- Input Validation ---
            validation_errors = []
            
            if not validate_customer_id(customer_id):
                validation_errors.append(f"Invalid customer ID format: {customer_id}")
            
            if not validate_enum(entity_type, VALID_ENTITY_TYPES):
                validation_errors.append(f"Invalid entity_type: {entity_type}. Must be one of {VALID_ENTITY_TYPES}")

            if not validate_enum(comparison_period, VALID_COMPARISON_PERIODS):
                validation_errors.append(f"Invalid comparison_period: {comparison_period}. Must be one of {VALID_COMPARISON_PERIODS}")

            # Validate threshold (e.g., must be between 0.5 and 5.0)
            if not validate_float_range(threshold, 0.5, 5.0):
                validation_errors.append(f"Invalid threshold: {threshold}. Must be between 0.5 and 5.0")

            # Validate entity_ids if provided
            if entity_ids is not None and not validate_list_of_strings(entity_ids, allow_empty=True):
                validation_errors.append("entity_ids must be None or a list of strings")

            # Set default dates if not provided
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

            # Validate date formats and range
            if not validate_date_format(start_date):
                validation_errors.append(f"Invalid start_date format: {start_date}")
            elif not validate_date_format(end_date):
                validation_errors.append(f"Invalid end_date format: {end_date}")
            elif not validate_date_range(start_date, end_date):
                validation_errors.append(f"Invalid date range: {start_date} to {end_date}")
            
            # Set default metrics if not provided, validate if provided
            if metrics is not None and not validate_list_of_strings(metrics, allow_empty=False):
                validation_errors.append("metrics must be a non-empty list of strings if provided")
                
            # If validation errors found, raise ValueError with all errors
            if validation_errors:
                raise ValueError("; ".join(validation_errors))
                
            # Prepare validated values
            cleaned_customer_id = clean_customer_id(customer_id)
            context["customer_id"] = cleaned_customer_id
            
            metrics_to_use = metrics if metrics is not None else DEFAULT_METRICS
            context["metrics"] = metrics_to_use
                
            context["start_date"] = start_date
            context["end_date"] = end_date
                 
            logger.info(f"Detecting performance anomalies for customer {format_customer_id(cleaned_customer_id)} ({entity_type}) from {start_date} to {end_date}")
        
            # --- Core Logic --- 
            # Get performance data for current period (delegate validation of IDs to underlying service)
            current_data = await self._get_performance_data(
                cleaned_customer_id, entity_type, entity_ids, metrics_to_use, start_date, end_date
            )
            
            # Get comparison data
            comparison_data = await self._get_comparison_data(
                cleaned_customer_id, entity_type, entity_ids, metrics_to_use, start_date, end_date, comparison_period
            )
            
            # Detect anomalies (internal logic, assumes valid inputs now)
            anomalies = self._analyze_for_anomalies(
                current_data, comparison_data, metrics_to_use, threshold
            )
            
            logger.info(f"Detected {len(anomalies)} anomalies for customer {format_customer_id(cleaned_customer_id)}")
            
            # --- Format Results --- 
            return {
                "anomalies": anomalies,
                "metadata": {
                    "customer_id": cleaned_customer_id,
                    "entity_type": entity_type,
                    "start_date": start_date,
                    "end_date": end_date,
                    "comparison_period": comparison_period,
                    "threshold": threshold,
                    "total_entities_analyzed": len(current_data) if current_data else 0,
                    "anomalies_detected": len(anomalies),
                    "metrics_analyzed": metrics_to_use
                }
            }
          
        except ValueError as ve:
            # Handle known validation errors
            error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
            logger.warning(f"Validation error detecting anomalies: {error_details.message}")
            raise ve
        except Exception as e:
            # Handle Google Ads API exceptions specifically
            if "GoogleAdsException" in str(type(e)):
                error_details = handle_google_ads_exception(e, context=context)
                logger.error(f"Google Ads API error detecting anomalies: {error_details.message}")
            else:
                error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
                logger.error(f"Error detecting performance anomalies: {error_details.message}")
            
            raise RuntimeError(f"Failed to detect anomalies: {error_details.message}") from e
        
    async def _get_performance_data(
        self, 
        customer_id: str,
        entity_type: str,
        entity_ids: Optional[List[str]], 
        metrics: List[str],
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Get performance data for the specified entity type and time period.
        
        Args:
            customer_id: Google Ads customer ID
            entity_type: Type of entity (CAMPAIGN, AD_GROUP, KEYWORD)
            entity_ids: Optional list of entity IDs to filter by
            metrics: List of metrics to retrieve
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of entities with performance data
        """
        try:
            if entity_type == "CAMPAIGN":
                return await self.google_ads_service.get_campaigns(
                    start_date=start_date,
                    end_date=end_date,
                    customer_id=customer_id,
                    campaign_ids=entity_ids
                )
            elif entity_type == "AD_GROUP":
                return await self.ad_group_service.get_ad_groups(
                    customer_id=customer_id,
                    ad_group_ids=entity_ids,
                    start_date=start_date,
                    end_date=end_date
                )
            elif entity_type == "KEYWORD":
                return await self.keyword_service.get_keywords(
                    customer_id=customer_id,
                    keyword_ids=entity_ids,
                    start_date=start_date,
                    end_date=end_date
                )
            else:
                logger.warning(f"Unsupported entity type: {entity_type}")
                return []
        except Exception as e:
            logger.error(f"Error getting performance data for {entity_type}: {str(e)}")
            # Propagate exception to calling method
            raise
            
    async def _get_comparison_data(
        self,
        customer_id: str,
        entity_type: str,
        entity_ids: Optional[List[str]],
        metrics: List[str],
        start_date: str,
        end_date: str,
        comparison_period: str
    ) -> List[Dict[str, Any]]:
        """
        Get comparison data for anomaly detection.
        
        Args:
            customer_id: Google Ads customer ID
            entity_type: Type of entity (CAMPAIGN, AD_GROUP, KEYWORD)
            entity_ids: Optional list of entity IDs to filter by
            metrics: List of metrics to retrieve
            start_date: Current period start date
            end_date: Current period end date
            comparison_period: Type of comparison period (PREVIOUS_PERIOD, SAME_PERIOD_LAST_YEAR)
            
        Returns:
            List of entities with comparison performance data
        """
        try:
            # Calculate comparison date range
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            date_range = (end_dt - start_dt).days + 1
            
            if comparison_period == "PREVIOUS_PERIOD":
                comparison_end = start_dt - timedelta(days=1)
                comparison_start = comparison_end - timedelta(days=date_range-1)
            elif comparison_period == "SAME_PERIOD_LAST_YEAR":
                comparison_start = start_dt - timedelta(days=365)
                comparison_end = end_dt - timedelta(days=365)
            else:
                logger.warning(f"Unsupported comparison period: {comparison_period}")
                return []
                
            comparison_start_str = comparison_start.strftime("%Y-%m-%d")
            comparison_end_str = comparison_end.strftime("%Y-%m-%d")
            
            logger.debug(f"Getting comparison data for {entity_type} from {comparison_start_str} to {comparison_end_str}")
            
            return await self._get_performance_data(
                customer_id,
                entity_type,
                entity_ids,
                metrics,
                comparison_start_str,
                comparison_end_str
            )
        except Exception as e:
            logger.error(f"Error getting comparison data: {str(e)}")
            # Propagate exception to calling method
            raise
    
    def _analyze_for_anomalies(
        self,
        current_data: List[Dict[str, Any]],
        comparison_data: List[Dict[str, Any]],
        metrics: List[str],
        threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Analyze performance data to detect anomalies.
        
        Args:
            current_data: Current period performance data
            comparison_data: Comparison period performance data
            metrics: List of metrics to analyze
            threshold: Z-score threshold for anomaly detection
            
        Returns:
            List of detected anomalies
        """
        if not current_data or not comparison_data or not metrics:
            logger.warning("Anomaly analysis skipped: Missing current data, comparison data, or metrics.")
            return []
            
        anomalies = []
        
        # Create a dictionary map from ID to comparison data for faster lookups
        comparison_map = {item.get('id', ''): item for item in comparison_data}
        
        # Pre-calculate metric statistics once to avoid recalculation
        metric_stats = {}
        for metric in metrics:
            # Ensure values are numeric for stats calculation, default to 0 if not found or not numeric
            values = [item.get(metric, 0) for item in current_data if isinstance(item.get(metric), (int, float))]
            if not values or len(values) < 2:
                logger.debug(f"Skipping stats calculation for metric '{metric}': insufficient valid data points ({len(values)} found).")
                continue
                
            mean = sum(values) / len(values)
            # Calculate standard deviation
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5 if variance > 0 else 1.0  # Avoid division by zero
            
            metric_stats[metric] = {
                'mean': mean,
                'std_dev': std_dev
            }
        
        # Analyze each entity
        for item in current_data:
            entity_id = item.get('id', '')
            if not entity_id:
                continue
                
            # Get comparison data for this entity using dictionary lookup (safe access)
            comparison_item = comparison_map.get(entity_id)
            if not comparison_item:
                logger.debug(f"Skipping anomaly check for entity {entity_id}: No comparison data found.")
                continue
                
            entity_anomalies = []
            
            for metric in metrics:
                # Skip if metric doesn't exist in either dataset or stats missing
                if metric not in item or metric not in comparison_item or metric not in metric_stats:
                    logger.debug(f"Skipping anomaly check for metric '{metric}' on entity {entity_id}: Missing data or stats.")
                    continue
                    
                # Ensure values are numeric, default to 0 otherwise
                current_value = item.get(metric, 0) if isinstance(item.get(metric), (int, float)) else 0
                comparison_value = comparison_item.get(metric, 0) if isinstance(comparison_item.get(metric), (int, float)) else 0
                
                # Skip metrics with zero or very small values to avoid false positives
                if abs(current_value) < 1e-9 and abs(comparison_value) < 1e-9:
                    continue
                
                # Calculate change
                if comparison_value != 0:
                    change_pct = (current_value - comparison_value) / abs(comparison_value)
                # Handle division by zero for change_pct calculation safely
                elif abs(comparison_value) < 1e-9 and abs(current_value) >= 1e-9:
                     # Significant change from zero
                    change_pct = 1.0 if current_value > 0 else -1.0 
                else:
                    # Both are zero or near-zero, no change
                    change_pct = 0.0
                
                # Calculate Z-score (standard score)
                mean = metric_stats[metric]['mean']
                std_dev = metric_stats[metric]['std_dev']
                
                if std_dev > 0:
                    z_score = abs((current_value - mean) / std_dev)
                else:
                    # If std_dev is 0, we can't calculate a z-score
                    z_score = 0.0
                
                # Check if it's an anomaly
                if z_score >= threshold:
                    # Create a dictionary with only one direction of change (compared to previous)
                    # This simplifies interpretation of results
                    direction = "increase" if current_value > comparison_value else "decrease"
                    change_pct_abs = abs(change_pct)
                    
                    anomaly = {
                        "entity_id": entity_id,
                        "entity_name": item.get("name", "Unknown"),
                        "metric": metric,
                        "current_value": current_value,
                        "previous_value": comparison_value,
                        "direction": direction,
                        "change_pct": change_pct_abs,
                        "z_score": z_score
                    }
                    
                    # Skip low-value anomalies below absolute thresholds to reduce noise
                    # Thresholds should be adjusted based on the metric
                    if _is_significant_anomaly(anomaly):
                        anomalies.append(anomaly)
                        
        # Sort anomalies by severity (z-score) and limit to top results
        anomalies.sort(key=lambda x: x.get("z_score", 0), reverse=True)
        
        # Return top anomalies (limit to 50 to avoid overwhelming response)
        return anomalies[:50]
    
    async def generate_optimization_suggestions(
        self, 
        customer_id: str, 
        entity_type: Optional[str] = None, 
        entity_ids: Optional[List[str]] = None, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate optimization suggestions for the account or specified entities.
        Returns a dictionary with results or raises ValueError/RuntimeError on failure.
        
        Args:
            customer_id: Google Ads customer ID
            entity_type: Optional entity type (CAMPAIGN, AD_GROUP)
            entity_ids: Optional list of entity IDs to analyze
            start_date: Start date (YYYY-MM-DD) for analysis (defaults to 30 days ago)
            end_date: End date (YYYY-MM-DD) for analysis (defaults to today)
            
        Returns:
            Dictionary containing optimization suggestions, or raises an exception.
        """
        context = {
            "customer_id": customer_id,
            "entity_type": entity_type,
            "entity_ids": entity_ids,
            "start_date": start_date,
            "end_date": end_date,
            "method": "generate_optimization_suggestions"
        }

        try:
            # --- Input Validation ---
            validation_errors = []
            
            if not validate_customer_id(customer_id):
                validation_errors.append(f"Invalid customer ID format: {customer_id}")
            
            # Create valid entity types list with None included
            valid_entity_types_with_none = VALID_ENTITY_TYPES + [None]
            if entity_type not in valid_entity_types_with_none:
                validation_errors.append(f"Invalid entity_type: {entity_type}. Must be one of {VALID_ENTITY_TYPES} or None")
            
            # Validate entity IDs if provided (must match entity_type)
            if entity_ids is not None:
                if not entity_type:
                    validation_errors.append("entity_type must be specified if entity_ids are provided")
                elif not validate_list_of_strings(entity_ids, allow_empty=False):
                    validation_errors.append("entity_ids must be a non-empty list of strings if provided")
            
            # Set default dates if not provided
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            # Validate date formats and range
            if not validate_date_format(start_date):
                validation_errors.append(f"Invalid start_date format: {start_date}")
            elif not validate_date_format(end_date):
                validation_errors.append(f"Invalid end_date format: {end_date}")
            elif not validate_date_range(start_date, end_date):
                validation_errors.append(f"Invalid date range: {start_date} to {end_date}")
            
            # If validation errors found, raise ValueError with all errors
            if validation_errors:
                raise ValueError("; ".join(validation_errors))
                
            # Prepare validated values
            cleaned_customer_id = clean_customer_id(customer_id)
            context["customer_id"] = cleaned_customer_id
            context["start_date"] = start_date
            context["end_date"] = end_date

            logger.info(f"Generating optimization suggestions for customer {format_customer_id(cleaned_customer_id)} ({entity_type or 'ACCOUNT'}) from {start_date} to {end_date}")
          
            # --- Core Logic ---
            # Initialize suggestions dictionary
            suggestions = {
                "bid_management": [],
                "budget_allocation": [],
                "negative_keywords": [],
                "ad_copy": [],
                "account_structure": []
            }
            
            # Batch data retrieval - get all the data we need upfront
            data_cache = {}
            
            # 1. Get account-level data (needed regardless of entity_type)
            account_data = await self._batch_retrieve_account_data(
                cleaned_customer_id, 
                start_date, 
                end_date
            )
            data_cache["account"] = account_data
            
            # 2. Get entity-specific data
            if entity_type == "CAMPAIGN" and entity_ids:
                # Analyze specific campaigns
                campaign_data = await self._analyze_campaigns_for_suggestions(
                    cleaned_customer_id, entity_ids, start_date, end_date
                )
                for category, campaign_suggestions in campaign_data.items():
                    suggestions[category].extend(campaign_suggestions)
            elif entity_type == "AD_GROUP" and entity_ids:
                # Analyze specific ad groups
                ad_group_data = await self._analyze_ad_groups_for_suggestions(
                    cleaned_customer_id, entity_ids, start_date, end_date
                )
                for category, ad_group_suggestions in ad_group_data.items():
                    suggestions[category].extend(ad_group_suggestions)
            else:
                # Analyze the entire account
                # Get campaign data in batch
                campaign_data = await self._batch_retrieve_campaign_data(
                    cleaned_customer_id, 
                    start_date, 
                    end_date
                )
                data_cache["campaigns"] = campaign_data
                
                # Use the cached data for analysis
                campaign_suggestions = self._analyze_campaign_data_for_suggestions(
                    campaign_data, 
                    account_data
                )
                
                for category, campaign_suggs in campaign_suggestions.items():
                    suggestions[category].extend(campaign_suggs)
                
                # Get ad group data in batch
                ad_group_data = await self._batch_retrieve_ad_group_data(
                    cleaned_customer_id, 
                    start_date, 
                    end_date,
                    campaign_data.get("campaigns", [])
                )
                data_cache["ad_groups"] = ad_group_data
                
                # Use the cached data for analysis
                ad_group_suggestions = self._analyze_ad_group_data_for_suggestions(
                    ad_group_data, 
                    campaign_data
                )
                
                for category, ad_group_suggs in ad_group_suggestions.items():
                    suggestions[category].extend(ad_group_suggs)
                
                # Generate account-wide suggestions
                account_suggestions = self._generate_account_suggestions(
                    account_data, 
                    campaign_data, 
                    ad_group_data
                )
                
                for category, account_suggs in account_suggestions.items():
                    suggestions[category].extend(account_suggs)
            
            # Sort suggestions by impact
            for category in suggestions:
                suggestions[category] = sorted(
                    suggestions[category],
                    key=lambda x: x.get("impact_score", 0),
                    reverse=True
                )
                
                # Limit to top 10 suggestions per category
                suggestions[category] = suggestions[category][:10]
            
            logger.info(f"Generated {sum(len(suggestions[key]) for key in suggestions)} suggestions for customer {format_customer_id(cleaned_customer_id)}")
            
            return {
                "suggestions": suggestions,
                "metadata": {
                    "customer_id": cleaned_customer_id,
                    "entity_type": entity_type,
                    "entity_ids": entity_ids,
                    "start_date": start_date,
                    "end_date": end_date,
                    "total_suggestions": sum(len(suggestions[key]) for key in suggestions)
                }
            }
        
        except ValueError as ve:
            # Handle known validation errors
            error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
            logger.warning(f"Validation error generating suggestions: {error_details.message}")
            raise ve
        except Exception as e:
            # Handle Google Ads API exceptions specifically
            if "GoogleAdsException" in str(type(e)):
                error_details = handle_google_ads_exception(e, context=context)
                logger.error(f"Google Ads API error generating suggestions: {error_details.message}")
            else:
                error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
                logger.error(f"Error generating optimization suggestions: {error_details.message}")
            
            raise RuntimeError(f"Failed to generate suggestions: {error_details.message}") from e

    async def _batch_retrieve_account_data(self, customer_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Retrieve all needed account-level data in a single batch of concurrent calls.
        
        Args:
            customer_id: Google Ads customer ID
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary containing account data
        """
        # Execute multiple API calls concurrently
        # Note: asyncio.gather stops on the first exception. Errors from underlying
        # services are expected to propagate and be caught by the calling method.
        account_tasks = [
            self.google_ads_service.get_account_summary(customer_id),
            self.google_ads_service.get_account_performance(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date
            ),
            self.budget_service.get_budgets(customer_id=customer_id)
        ]
        
        # Get search terms data if applicable
        if self.search_term_service:
            account_tasks.append(
                self.search_term_service.get_search_terms(
                    customer_id=customer_id,
                    start_date=start_date,
                    end_date=end_date
                )
            )
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*account_tasks)
        
        # Organize results
        account_data = {
            "account_summary": results[0],
            "account_performance": results[1],
            "budgets": results[2],
            "search_terms": results[3] if len(results) > 3 else []
        }
        
        return account_data
        
    async def _batch_retrieve_campaign_data(self, customer_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Retrieve all needed campaign data in a single batch of concurrent calls.
        
        Args:
            customer_id: Google Ads customer ID
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary containing campaign data
        """
        # Execute multiple API calls concurrently
        # Note: asyncio.gather stops on the first exception.
        campaign_tasks = [
            self.google_ads_service.get_campaigns(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date
            ),
            self.google_ads_service.get_campaign_performance_by_device(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date
            ),
            self.google_ads_service.get_campaign_performance_by_network(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date
            )
        ]
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*campaign_tasks)
        
        # Organize results
        campaign_data = {
            "campaigns": results[0],
            "device_performance": results[1],
            "network_performance": results[2]
        }
        
        return campaign_data
        
    async def _batch_retrieve_ad_group_data(
        self, 
        customer_id: str, 
        start_date: str, 
        end_date: str,
        campaigns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Retrieve all needed ad group data in a single batch of concurrent calls.
        
        Args:
            customer_id: Google Ads customer ID
            start_date: Start date for analysis
            end_date: End date for analysis
            campaigns: List of campaign data for filtering
            
        Returns:
            Dictionary containing ad group data
        """
        # Get campaign IDs for top campaigns only (limit to 10 for efficiency)
        # Sort campaigns by cost (safe access with .get)
        sorted_campaigns = sorted(
            campaigns,
            key=lambda x: x.get("cost_micros", 0),
            reverse=True
        )
        top_campaign_ids = [c.get("id") for c in sorted_campaigns[:10] if c.get("id")]
        
        if not top_campaign_ids:
             logger.warning(f"No top campaign IDs found for customer {customer_id} to retrieve ad group data.")
             return {"ad_groups": [], "keywords": []} # Return empty data if no campaigns to query
             
        # Execute multiple API calls concurrently
        # Note: asyncio.gather stops on the first exception.
        ad_group_tasks = [
            self.ad_group_service.get_ad_groups(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date,
                campaign_ids=top_campaign_ids  # Filter to top campaigns only
            ),
            self.keyword_service.get_keywords(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date,
                campaign_ids=top_campaign_ids,  # Filter to top campaigns only
                status_filter="ENABLED"  # Only get active keywords
            )
        ]
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*ad_group_tasks)
        
        # Organize results
        ad_group_data = {
            "ad_groups": results[0],
            "keywords": results[1]
        }
        
        return ad_group_data
        
    def _analyze_campaign_data_for_suggestions(
        self, 
        campaign_data: Dict[str, Any],
        account_data: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Analyze campaign data for optimization suggestions.
        
        Args:
            campaign_data: Campaign data from batch retrieval
            account_data: Account data from batch retrieval
            
        Returns:
            Dictionary of suggestions by category
        """
        suggestions = {
            "bid_management": [],
            "budget_allocation": [],
            "negative_keywords": [],
            "ad_copy": [],
            "account_structure": []
        }
        
        campaigns = campaign_data.get("campaigns", [])
        budgets = account_data.get("budgets", [])
        
        # Create a lookup map for budget data for efficient access
        budget_map = {budget.get('id', ''): budget for budget in budgets}
        
        # 1. Budget allocation suggestions
        for campaign in campaigns:
            campaign_id = campaign.get('id', '')
            campaign_name = campaign.get('name', 'Unknown')
            budget_id = campaign.get('budget_id', '')
            campaign_status = campaign.get('status', 'UNKNOWN')
            
            # Skip non-active campaigns
            if campaign_status != 'ENABLED':
                continue
                
            # Skip campaigns with no budget or whose budget wasn't retrieved
            budget = budget_map.get(budget_id)
            if not budget:
                logger.debug(f"Skipping budget analysis for campaign {campaign_id}: Budget data missing.")
                continue
                
            # Safely get budget amount, default to 0
            budget_amount_micros = budget.get('amount_micros', 0)
            budget_amount = budget_amount_micros / 1000000 if budget_amount_micros else 0 
            
            # Check budget utilization
            budget_utilization = campaign.get('budget_utilization_placeholder', 0) # Replace with actual calculation logic if needed
            
            # Campaigns with high budget utilization could benefit from budget increase
            if budget_utilization > 0.9 and budget_amount > 0: # Avoid suggesting increase for $0 budget
                suggestions["budget_allocation"].append({
                    "type": "increase_budget",
                    "entity_type": "CAMPAIGN",
                    "entity_id": campaign_id,
                    "entity_name": campaign_name,
                    "current_value": budget_amount,
                    "suggested_value": budget_amount * 1.2,  # 20% increase
                    "impact_score": 0.8 + (budget_utilization - 0.9) * 2,  # Score 0.8-1.0
                    "reason": f"Campaign is achieving {budget_utilization*100:.1f}% budget utilization.",
                    "recommendation": f"Consider increasing the budget by 20% to capture additional traffic."
                })
            
            # Campaigns with very low budget utilization might need optimization or budget reallocation
            elif budget_utilization < 0.5 and budget_amount > 10:
                suggestions["budget_allocation"].append({
                    "type": "decrease_budget",
                    "entity_type": "CAMPAIGN",
                    "entity_id": campaign_id,
                    "entity_name": campaign_name,
                    "current_value": budget_amount,
                    "suggested_value": budget_amount * 0.8,  # 20% decrease
                    "impact_score": 0.5 + (0.5 - budget_utilization),  # Score 0.5-1.0
                    "reason": f"Campaign is only using {budget_utilization*100:.1f}% of its budget.",
                    "recommendation": f"Consider decreasing the budget and reallocating to higher-performing campaigns."
                })
        
        # Add other campaign analysis for bid management, etc.
        
        return suggestions
    
    def _analyze_ad_group_data_for_suggestions(
        self, 
        ad_group_data: Dict[str, Any],
        campaign_data: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Analyze ad group data for optimization suggestions.
        
        Args:
            ad_group_data: Ad group data from batch retrieval
            campaign_data: Campaign data from batch retrieval
            
        Returns:
            Dictionary of suggestions by category
        """
        suggestions = {
            "bid_management": [],
            "budget_allocation": [],
            "negative_keywords": [],
            "ad_copy": [],
            "account_structure": []
        }
        
        ad_groups = ad_group_data.get("ad_groups", [])
        keywords = ad_group_data.get("keywords", [])
        campaigns = campaign_data.get("campaigns", [])
        
        if not ad_groups:
             logger.info("Skipping ad group suggestion analysis: No ad group data available.")
             return suggestions
             
        # Create lookup maps for efficient access
        campaign_map = {campaign.get('id', ''): campaign for campaign in campaigns}
        keyword_by_ad_group = {}
        
        # Group keywords by ad group for more efficient processing
        for keyword in keywords:
            ad_group_id = keyword.get('ad_group_id', '')
            if ad_group_id:
                if ad_group_id not in keyword_by_ad_group:
                    keyword_by_ad_group[ad_group_id] = []
                keyword_by_ad_group[ad_group_id].append(keyword)
        
        # Analyze ad groups for optimization suggestions
        for ad_group in ad_groups:
            ad_group_id = ad_group.get('id', '')
            ad_group_name = ad_group.get('name', 'Unknown')
            campaign_id = ad_group.get('campaign_id', '')
            ad_group_status = ad_group.get('status', 'UNKNOWN')
            
            # Skip non-active ad groups
            if ad_group_status != 'ENABLED':
                continue
            
            # Get campaign data
            campaign = campaign_map.get(campaign_id, {})
            campaign_name = campaign.get('name', 'Unknown')
            
            # Get ad group performance metrics
            impressions = ad_group.get('impressions', 0)
            clicks = ad_group.get('clicks', 0)
            conversions = ad_group.get('conversions', 0)
            cost_micros = ad_group.get('cost_micros', 0)
            cost = cost_micros / 1000000  # Convert to dollars
            
            # Calculate derived metrics
            ctr = clicks / impressions if impressions > 0 else 0
            conversion_rate = conversions / clicks if clicks > 0 else 0
            cpa = cost / conversions if conversions > 0 else 0
            
            # Ad groups with high cost but no conversions
            if cost > 100 and conversions < 1:
                suggestions["bid_management"].append({
                    "type": "reduce_bids",
                    "entity_type": "AD_GROUP",
                    "entity_id": ad_group_id,
                    "entity_name": ad_group_name,
                    "parent_name": campaign_name,
                    "current_value": None,
                    "suggested_value": None,
                    "impact_score": min(1.0, cost / 200),  # Score based on cost (max 1.0)
                    "reason": f"Ad group has spent ${cost:.2f} with no conversions.",
                    "recommendation": "Consider reducing bids or pausing this ad group."
                })
        
        # Add other ad group analysis
        
        return suggestions
    
    def _generate_account_suggestions(
        self,
        account_data: Dict[str, Any],
        campaign_data: Dict[str, Any],
        ad_group_data: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate account-wide suggestions based on all data.
        
        Args:
            account_data: Account data from batch retrieval
            campaign_data: Campaign data from batch retrieval
            ad_group_data: Ad group data from batch retrieval
            
        Returns:
            Dictionary of suggestions by category
        """
        suggestions = {
            "bid_management": [],
            "budget_allocation": [],
            "negative_keywords": [],
            "ad_copy": [],
            "account_structure": []
        }
        
        # Account-wide budget analysis
        account_perf = account_data.get("account_performance", {})
        campaigns = campaign_data.get("campaigns", [])
        search_terms = account_data.get("search_terms", [])
        
        # Find candidates for negative keywords
        if search_terms:
            negative_candidates = []
            
            for term in search_terms:
                impressions = term.get('impressions', 0)
                clicks = term.get('clicks', 0)
                conversions = term.get('conversions', 0)
                cost_micros = term.get('cost_micros', 0)
                cost = cost_micros / 1000000  # Convert to dollars
                
                # High-impression, low-CTR terms
                if impressions > 100 and clicks == 0:
                    negative_candidates.append({
                        "term": term.get('search_term', ''),
                        "impressions": impressions,
                        "clicks": clicks,
                        "cost": cost,
                        "reason": "High impressions, no clicks",
                        "impact_score": min(1.0, impressions / 1000)  # Score based on impressions (max 1.0)
                    })
                # High-cost, no-conversion terms
                elif cost > 20 and conversions == 0:
                    negative_candidates.append({
                        "term": term.get('search_term', ''),
                        "impressions": impressions,
                        "clicks": clicks,
                        "cost": cost,
                        "reason": "High cost, no conversions",
                        "impact_score": min(1.0, cost / 50)  # Score based on cost (max 1.0)
                    })
            
            # Sort by impact score and add top candidates
            negative_candidates.sort(key=lambda x: x['impact_score'], reverse=True)
            for candidate in negative_candidates[:5]:  # Limit to top 5
                suggestions["negative_keywords"].append({
                    "type": "add_negative_keyword",
                    "entity_type": "ACCOUNT",
                    "entity_id": "",
                    "entity_name": "Account-wide",
                    "term": candidate['term'],
                    "impressions": candidate['impressions'],
                    "cost": candidate['cost'],
                    "impact_score": candidate['impact_score'],
                    "reason": candidate['reason'],
                    "recommendation": f"Add '{candidate['term']}' as a negative keyword."
                })
        
        # Add other account-wide analysis
        
        return suggestions
    
    async def discover_opportunities(
        self,
        customer_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Discover growth opportunities in the account.
        
        Args:
            customer_id: Google Ads customer ID
            start_date: Start date for analysis (defaults to 30 days ago)
            end_date: End date for analysis (defaults to today)
            
        Returns:
            Dictionary containing identified opportunities
        """
        logger.info(f"Discovering opportunities for customer {customer_id}")
        
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            # Default to 30 days for opportunity discovery
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
        # Initialize opportunities dictionary
        opportunities = {
            "keyword_expansion": [],
            "ad_variation": [],
            "structure": [],
            "audience": []
        }
        
        # Discover keyword expansion opportunities
        keyword_opps = await self._discover_keyword_opportunities(
            customer_id, start_date, end_date
        )
        opportunities["keyword_expansion"] = keyword_opps
        
        # Discover ad variation opportunities
        ad_opps = await self._discover_ad_variation_opportunities(
            customer_id, start_date, end_date
        )
        opportunities["ad_variation"] = ad_opps
        
        # Discover account structure opportunities
        structure_opps = await self._discover_structure_opportunities(
            customer_id, start_date, end_date
        )
        opportunities["structure"] = structure_opps
        
        return {
            "opportunities": opportunities,
            "metadata": {
                "customer_id": customer_id,
                "start_date": start_date,
                "end_date": end_date,
                "total_opportunities": sum(len(opportunities[key]) for key in opportunities)
            }
        }
    
    async def _discover_keyword_opportunities(
        self,
        customer_id: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Discover keyword expansion opportunities.
        
        Args:
            customer_id: Google Ads customer ID
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            List of keyword expansion opportunities
        """
        opportunities = []
        
        # Get existing keywords
        existing_keywords = await self.keyword_service.get_keywords(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get search terms
        search_terms = await self.search_term_service.get_search_terms(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Create a set of existing keyword texts
        existing_keyword_texts = set()
        for kw in existing_keywords:
            text = kw.get('text', '').lower()
            if text:
                existing_keyword_texts.add(text)
        
        # Find high-performing search terms that aren't already keywords
        for term in search_terms:
            query = term.get('query', '').lower()
            impressions = term.get('impressions', 0)
            clicks = term.get('clicks', 0)
            cost = term.get('cost', 0)
            conversions = term.get('conversions', 0)
            
            # Skip short or irrelevant queries
            if len(query) < 3 or all(c.isdigit() for c in query):
                continue
                
            # Check if this query is already a keyword
            if query in existing_keyword_texts:
                continue
                
            # Calculate performance metrics
            ctr = clicks / impressions if impressions > 0 else 0
            conversion_rate = conversions / clicks if clicks > 0 else 0
            
            # High-performing search terms
            if (conversions > 0 and clicks >= 5) or (ctr > 0.03 and clicks >= 10):
                campaign_id = term.get('campaign_id', '')
                campaign_name = term.get('campaign_name', 'Unknown')
                ad_group_id = term.get('ad_group_id', '')
                ad_group_name = term.get('ad_group_name', 'Unknown')
                
                opportunities.append({
                    "type": "ADD_KEYWORD_FROM_SEARCH_TERM",
                    "search_term": query,
                    "suggested_match_type": "EXACT",
                    "campaign_id": campaign_id,
                    "campaign_name": campaign_name,
                    "ad_group_id": ad_group_id,
                    "ad_group_name": ad_group_name,
                    "impressions": impressions,
                    "clicks": clicks,
                    "conversions": conversions,
                    "ctr": ctr,
                    "conversion_rate": conversion_rate,
                    "opportunity": f"Add '{query}' as a keyword in ad group '{ad_group_name}'",
                    "impact": "HIGH" if conversions > 0 else "MEDIUM",
                    "action": f"Add '{query}' as an exact match keyword to better control bidding and relevance"
                })
        
        # Sort opportunities by impact and conversions
        return sorted(
            opportunities,
            key=lambda x: (0 if x["impact"] == "HIGH" else 1, -x["conversions"]),
        )
    
    async def _discover_ad_variation_opportunities(
        self,
        customer_id: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Discover ad variation opportunities.
        
        Args:
            customer_id: Google Ads customer ID
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            List of ad variation opportunities
        """
        # This is a simplified placeholder implementation
        # In a real implementation, we would analyze ad performance data
        # to identify opportunities for new ad variations
        
        opportunities = []
        
        # Get ad group data
        ad_groups = await self.ad_group_service.get_ad_groups(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Filter for ad groups with significant traffic but limited ad variations
        for ad_group in ad_groups:
            ad_group_id = ad_group.get('id', '')
            ad_group_name = ad_group.get('name', 'Unknown')
            campaign_id = ad_group.get('campaign_id', '')
            campaign_name = ad_group.get('campaign_name', 'Unknown')
            impressions = ad_group.get('impressions', 0)
            
            # Only suggest for ad groups with significant traffic
            if impressions < 1000:
                continue
                
            # In a real implementation, we would check the number of active ads
            # and suggest new variations for ad groups with only 1-2 ads
            # This is a simplified placeholder
            opportunities.append({
                "type": "CREATE_AD_VARIATION",
                "entity_type": "AD_GROUP",
                "entity_id": ad_group_id,
                "entity_name": ad_group_name,
                "campaign_id": campaign_id,
                "campaign_name": campaign_name,
                "impressions": impressions,
                "opportunity": f"Create additional ad variations for ad group '{ad_group_name}'",
                "impact": "MEDIUM",
                "action": "Add at least one more responsive search ad to test different headlines and descriptions"
            })
        
        return opportunities[:5]  # Limit to top 5 opportunities
    
    async def _discover_structure_opportunities(
        self,
        customer_id: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Discover account structure opportunities.
        
        Args:
            customer_id: Google Ads customer ID
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            List of account structure opportunities
        """
        # This is a simplified placeholder implementation
        # In a real implementation, we would analyze account structure
        # to identify opportunities for restructuring
        
        opportunities = []
        
        # Get ad group data
        ad_groups = await self.ad_group_service.get_ad_groups(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Map of campaign IDs to lists of ad groups
        campaign_ad_groups = {}
        
        for ad_group in ad_groups:
            campaign_id = ad_group.get('campaign_id', '')
            if campaign_id:
                if campaign_id not in campaign_ad_groups:
                    campaign_ad_groups[campaign_id] = []
                    
                campaign_ad_groups[campaign_id].append(ad_group)
        
        # Check for campaigns with large ad groups that might benefit from splitting
        for campaign_id, ad_group_list in campaign_ad_groups.items():
            if len(ad_group_list) == 0:
                continue
                
            campaign_name = ad_group_list[0].get('campaign_name', 'Unknown')
            
            # Look for ad groups with lots of keywords (simplified in this placeholder)
            for ad_group in ad_group_list:
                ad_group_id = ad_group.get('id', '')
                ad_group_name = ad_group.get('name', 'Unknown')
                
                # In a real implementation, we would check keyword count and themes
                # This is a simplified placeholder
                if ad_group.get('impressions', 0) > 5000:
                    opportunities.append({
                        "type": "SPLIT_LARGE_AD_GROUP",
                        "entity_type": "AD_GROUP",
                        "entity_id": ad_group_id,
                        "entity_name": ad_group_name,
                        "campaign_id": campaign_id,
                        "campaign_name": campaign_name,
                        "opportunity": f"Consider splitting large ad group '{ad_group_name}' into more specific themes",
                        "impact": "MEDIUM",
                        "action": "Review keywords in this ad group and consider reorganizing into more tightly themed ad groups"
                    })
        
        return opportunities 

# Helper function for anomaly detection
def _is_significant_anomaly(anomaly: Dict[str, Any]) -> bool:
    """
    Determine if an anomaly is significant enough to report.
    
    Args:
        anomaly: Anomaly data dictionary
        
    Returns:
        True if the anomaly is significant, False otherwise
    """
    metric = anomaly.get("metric", "")
    current_value = anomaly.get("current_value", 0)
    change_pct = anomaly.get("change_pct", 0)
    
    # Different thresholds for different metrics
    if metric == "impressions" and current_value < 100 and change_pct < 0.5:
        return False
    if metric == "clicks" and current_value < 10 and change_pct < 0.5:
        return False
    if metric == "cost" and current_value < 5 and change_pct < 0.3:
        return False
    if (metric == "ctr" or metric == "conversion_rate") and change_pct < 0.2:
        return False
    if metric == "conversions" and current_value < 2 and change_pct < 0.5:
        return False
        
    return True 