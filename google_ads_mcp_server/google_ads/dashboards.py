"""
Dashboard service for Google Ads MCP Server.

This module provides the DashboardService class which aggregates data from various
Google Ads API endpoints to create comprehensive dashboards for accounts and campaigns.
"""

from typing import Dict, List, Any, Optional, Union
import logging
from datetime import datetime, timedelta

# Import utilities
from ..utils.logging import get_logger
from ..utils.validation import (
    validate_customer_id,
    validate_string_length,
    validate_enum,
    validate_list_not_empty,
    validate_list_of_strings,
    validate_date_range_string
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

# Assuming GoogleAdsService is the core service that makes API calls
# GoogleAdsService is defined as an alias in client.py for backward compatibility
from .client import GoogleAdsService

# Initialize logger
logger = get_logger(__name__)

# Define valid enum values
VALID_ENTITY_TYPES = ["account", "campaign", "ad_group"]
VALID_DATE_RANGES = ["LAST_30_DAYS", "LAST_7_DAYS", "LAST_14_DAYS", "LAST_90_DAYS", "THIS_MONTH", "LAST_MONTH"]
VALID_DIMENSIONS = ["device", "day", "week", "month", "geo", "network"]

class DashboardService:
    """
    Service for retrieving and aggregating data for account and campaign dashboards.

    This service combines data from multiple Google Ads API endpoints (campaigns,
    ad groups, keywords, etc.) to provide comprehensive dashboards with performance
    metrics, trends, and breakdowns.
    """

    def __init__(self, google_ads_service: GoogleAdsService):
        """
        Initialize the DashboardService.

        Args:
            google_ads_service: Instance of GoogleAdsService for making API calls
        """
        self.google_ads_service = google_ads_service
        logger.info("DashboardService initialized")

    def get_account_dashboard(self,
                           date_range: str = "LAST_30_DAYS",
                           comparison_range: Optional[str] = "PREVIOUS_30_DAYS") -> Dict[str, Any]:
        """
        Get comprehensive account dashboard data.

        Args:
            date_range: Date range for the dashboard data (e.g., "LAST_30_DAYS", "LAST_7_DAYS")
            comparison_range: Optional date range for period-over-period comparison

        Returns:
            Dictionary containing metrics, time series, and entity data for the account dashboard
        """
        context = {
            "date_range": date_range,
            "comparison_range": comparison_range,
            "method": "get_account_dashboard"
        }

        try:
            # Validate inputs
            validation_errors = []

            if not validate_date_range_string(date_range):
                validation_errors.append(f"Invalid date_range: {date_range}. Must be one of {VALID_DATE_RANGES}")

            if comparison_range is not None and not validate_date_range_string(comparison_range):
                validation_errors.append(f"Invalid comparison_range: {comparison_range}. Must be one of {VALID_DATE_RANGES}")

            # If validation errors found, raise ValueError
            if validation_errors:
                raise ValueError("; ".join(validation_errors))

            logger.info(f"Retrieving account dashboard data for {date_range}")

            # Initialize result structure
            dashboard_data = {
                "metrics": {},
                "time_series": [],
                "campaigns": [],
                "ad_groups": []
            }

            # 1. Get account-level metrics
            metrics = self.google_ads_service.get_account_metrics(date_range=date_range)
            dashboard_data["metrics"] = metrics

            # 2. Get time series data (daily breakdown)
            time_series = self.google_ads_service.get_account_performance_time_series(date_range=date_range)
            dashboard_data["time_series"] = time_series

            # 3. Get campaign data
            campaigns = self.google_ads_service.get_campaigns(date_range=date_range, limit=20)
            dashboard_data["campaigns"] = campaigns

            # 4. Get top ad groups
            ad_groups = self.google_ads_service.get_ad_groups(date_range=date_range, limit=20)
            dashboard_data["ad_groups"] = ad_groups

            # 5. Get comparison data if requested
            if comparison_range:
                comparison_metrics = self.google_ads_service.get_account_metrics(date_range=comparison_range)
                dashboard_data["comparison_metrics"] = comparison_metrics

            logger.info("Account dashboard data retrieved successfully")
            return dashboard_data

        except ValueError as ve:
            error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
            logger.warning(f"Validation error retrieving account dashboard: {error_details.message}")
            return {
                "metrics": {},
                "time_series": [],
                "campaigns": [],
                "ad_groups": [],
                "error": error_details.message
            }
        except Exception as e:
            # Handle Google Ads API exceptions specifically
            if "GoogleAdsException" in str(type(e)):
                error_details = handle_google_ads_exception(e, context=context)
                logger.error(f"Google Ads API error retrieving account dashboard: {error_details.message}")
            else:
                error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
                logger.error(f"Error retrieving account dashboard data: {error_details.message}")

            # Return minimal dashboard data with error information
            return {
                "metrics": {},
                "time_series": [],
                "campaigns": [],
                "ad_groups": [],
                "error": error_details.message
            }

    def get_campaign_dashboard(self,
                              campaign_id: str,
                              date_range: str = "LAST_30_DAYS",
                              comparison_range: Optional[str] = "PREVIOUS_30_DAYS") -> Dict[str, Any]:
        """
        Get comprehensive campaign dashboard data for a specific campaign.

        Args:
            campaign_id: ID of the campaign
            date_range: Date range for the dashboard data
            comparison_range: Optional date range for period-over-period comparison

        Returns:
            Dictionary containing metrics, time series, and entity data for the campaign dashboard
        """
        context = {
            "campaign_id": campaign_id,
            "date_range": date_range,
            "comparison_range": comparison_range,
            "method": "get_campaign_dashboard"
        }

        try:
            # Validate inputs
            validation_errors = []

            if not validate_string_length(campaign_id, min_length=1):
                validation_errors.append("campaign_id must not be empty")

            if not validate_date_range_string(date_range):
                validation_errors.append(f"Invalid date_range: {date_range}. Must be one of {VALID_DATE_RANGES}")

            if comparison_range is not None and not validate_date_range_string(comparison_range):
                validation_errors.append(f"Invalid comparison_range: {comparison_range}. Must be one of {VALID_DATE_RANGES}")

            # If validation errors found, raise ValueError
            if validation_errors:
                raise ValueError("; ".join(validation_errors))

            logger.info(f"Retrieving campaign dashboard data for campaign ID {campaign_id}")

            # Initialize result structure
            dashboard_data = {}

            # 1. Get campaign details
            campaign_details = self.google_ads_service.get_campaign_details(campaign_id)
            if not campaign_details:
                raise ValueError(f"Campaign with ID {campaign_id} not found")

            # Copy relevant campaign details to dashboard data
            for key, value in campaign_details.items():
                dashboard_data[key] = value

            # 2. Get campaign metrics for the specified date range
            metrics = self.google_ads_service.get_campaign_metrics(
                campaign_id=campaign_id,
                date_range=date_range
            )
            dashboard_data["metrics"] = metrics

            # 3. Get time series data (daily breakdown)
            time_series = self.google_ads_service.get_campaign_performance_time_series(
                campaign_id=campaign_id,
                date_range=date_range
            )
            dashboard_data["time_series"] = time_series

            # 4. Get ad groups in this campaign
            ad_groups = self.google_ads_service.get_ad_groups(
                campaign_id=campaign_id,
                date_range=date_range
            )
            dashboard_data["ad_groups"] = ad_groups

            # 5. Get device breakdown
            device_performance = self.google_ads_service.get_campaign_performance_by_device(
                campaign_id=campaign_id,
                date_range=date_range
            )
            dashboard_data["device_performance"] = device_performance

            # 6. Get top keywords for this campaign
            keywords = self.google_ads_service.get_keywords(
                campaign_id=campaign_id,
                date_range=date_range,
                limit=20
            )
            dashboard_data["keywords"] = keywords

            # 7. Get comparison data if requested
            if comparison_range:
                comparison_metrics = self.google_ads_service.get_campaign_metrics(
                    campaign_id=campaign_id,
                    date_range=comparison_range
                )
                dashboard_data["comparison_metrics"] = comparison_metrics

            logger.info(f"Campaign dashboard data for campaign ID {campaign_id} retrieved successfully")
            return dashboard_data

        except ValueError as ve:
            error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
            logger.warning(f"Validation error retrieving campaign dashboard: {error_details.message}")
            return {
                "id": campaign_id,
                "name": "Unknown",
                "metrics": {},
                "time_series": [],
                "ad_groups": [],
                "device_performance": [],
                "keywords": [],
                "error": error_details.message
            }
        except Exception as e:
            # Handle Google Ads API exceptions specifically
            if "GoogleAdsException" in str(type(e)):
                error_details = handle_google_ads_exception(e, context=context)
                logger.error(f"Google Ads API error retrieving campaign dashboard: {error_details.message}")
            else:
                error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
                logger.error(f"Error retrieving campaign dashboard data for ID {campaign_id}: {error_details.message}")

            # Return minimal dashboard data with error information
            return {
                "id": campaign_id,
                "name": "Unknown",
                "metrics": {},
                "time_series": [],
                "ad_groups": [],
                "device_performance": [],
                "keywords": [],
                "error": error_details.message
            }

    def get_campaigns_comparison(self,
                                campaign_ids: List[str],
                                date_range: str = "LAST_30_DAYS",
                                metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get comparison data for multiple campaigns.

        Args:
            campaign_ids: List of campaign IDs to compare
            date_range: Date range for the comparison data
            metrics: Optional list of specific metrics to include (default: all available)

        Returns:
            Dictionary containing comparison data for the specified campaigns
        """
        context = {
            "campaign_count": len(campaign_ids) if campaign_ids else 0,
            "date_range": date_range,
            "method": "get_campaigns_comparison"
        }

        try:
            # Validate inputs
            validation_errors = []

            if not validate_list_not_empty(campaign_ids):
                validation_errors.append("campaign_ids must be a non-empty list")

            if not validate_date_range_string(date_range):
                validation_errors.append(f"Invalid date_range: {date_range}. Must be one of {VALID_DATE_RANGES}")

            if metrics is not None and not validate_list_of_strings(metrics, allow_empty=False):
                validation_errors.append("metrics must be a non-empty list of strings if provided")

            # If validation errors found, raise ValueError
            if validation_errors:
                raise ValueError("; ".join(validation_errors))

            logger.info(f"Retrieving comparison data for {len(campaign_ids)} campaigns")

            if not metrics:
                # Default set of metrics to include in comparison
                metrics = [
                    "impressions", "clicks", "cost_micros", "conversions",
                    "ctr", "average_cpc", "conversion_rate", "cost_per_conversion"
                ]

            campaigns_data = []
            failed_campaigns = []

            # Get data for each campaign
            for campaign_id in campaign_ids:
                try:
                    campaign_details = self.google_ads_service.get_campaign_details(campaign_id)
                    if not campaign_details:
                        logger.warning(f"Campaign with ID {campaign_id} not found")
                        failed_campaigns.append({"id": campaign_id, "error": "Campaign not found"})
                        continue

                    campaign_metrics = self.google_ads_service.get_campaign_metrics(
                        campaign_id=campaign_id,
                        date_range=date_range
                    )

                    # Combine details and metrics
                    campaign_data = {
                        "id": campaign_id,
                        "name": campaign_details.get("name", "Unknown"),
                        "status": campaign_details.get("status", "Unknown")
                    }

                    # Add metrics
                    for metric in metrics:
                        if metric in campaign_metrics:
                            campaign_data[metric] = campaign_metrics[metric]

                    campaigns_data.append(campaign_data)
                except Exception as campaign_error:
                    # Log error but continue with other campaigns
                    error_details = handle_exception(campaign_error, context={**context, "campaign_id": campaign_id})
                    logger.warning(f"Error processing campaign ID {campaign_id}: {error_details.message}")
                    failed_campaigns.append({"id": campaign_id, "error": error_details.message})

            result = {
                "campaigns": campaigns_data,
                "metrics": metrics,
                "date_range": date_range
            }

            # Include failed campaigns if any
            if failed_campaigns:
                result["failed_campaigns"] = failed_campaigns

            return result

        except ValueError as ve:
            error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
            logger.warning(f"Validation error retrieving campaigns comparison: {error_details.message}")
            return {
                "campaigns": [],
                "metrics": metrics or [],
                "date_range": date_range,
                "error": error_details.message
            }
        except Exception as e:
            # Handle Google Ads API exceptions specifically
            if "GoogleAdsException" in str(type(e)):
                error_details = handle_google_ads_exception(e, context=context)
                logger.error(f"Google Ads API error retrieving campaigns comparison: {error_details.message}")
            else:
                error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
                logger.error(f"Error retrieving campaigns comparison data: {error_details.message}")

            return {
                "campaigns": [],
                "metrics": metrics or [],
                "date_range": date_range,
                "error": error_details.message
            }

    def get_performance_breakdown(self,
                                 entity_type: str,
                                 entity_id: str,
                                 dimensions: List[str],
                                 date_range: str = "LAST_30_DAYS") -> Dict[str, Any]:
        """
        Get performance breakdown data for a specific entity by dimensions.

        Args:
            entity_type: Type of entity ("account", "campaign", "ad_group")
            entity_id: ID of the entity (can be None for account-level breakdown)
            dimensions: List of dimensions to break down by (e.g., "device", "day", "geo")
            date_range: Date range for the breakdown data

        Returns:
            Dictionary containing breakdown data for the specified entity and dimensions
        """
        context = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "dimensions": dimensions,
            "date_range": date_range,
            "method": "get_performance_breakdown"
        }

        try:
            # Validate inputs
            validation_errors = []

            if not validate_enum(entity_type, VALID_ENTITY_TYPES):
                validation_errors.append(f"Invalid entity_type: {entity_type}. Must be one of {VALID_ENTITY_TYPES}")

            if entity_type != "account" and not validate_string_length(entity_id, min_length=1):
                validation_errors.append(f"entity_id must not be empty for entity_type: {entity_type}")

            if not validate_list_not_empty(dimensions):
                validation_errors.append("dimensions must be a non-empty list")
            else:
                for dimension in dimensions:
                    if not validate_enum(dimension, VALID_DIMENSIONS):
                        validation_errors.append(f"Invalid dimension: {dimension}. Must be one of {VALID_DIMENSIONS}")

            if not validate_date_range_string(date_range):
                validation_errors.append(f"Invalid date_range: {date_range}. Must be one of {VALID_DATE_RANGES}")

            # If validation errors found, raise ValueError
            if validation_errors:
                raise ValueError("; ".join(validation_errors))

            logger.info(f"Retrieving {entity_type} breakdown by {dimensions} for ID {entity_id}")

            breakdown_data = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "dimensions": dimensions,
                "date_range": date_range,
                "data": []
            }

            # Get entity details for context
            if entity_type == "campaign" and entity_id:
                entity_details = self.google_ads_service.get_campaign_details(entity_id)
                breakdown_data["entity_name"] = entity_details.get("name", "Unknown")
            elif entity_type == "ad_group" and entity_id:
                entity_details = self.google_ads_service.get_ad_group_details(entity_id)
                breakdown_data["entity_name"] = entity_details.get("name", "Unknown")
            elif entity_type == "account":
                breakdown_data["entity_name"] = "Account"

            # Process each dimension
            failed_dimensions = []
            for dimension in dimensions:
                try:
                    dimension_data = self._get_dimension_breakdown(
                        entity_type=entity_type,
                        entity_id=entity_id,
                        dimension=dimension,
                        date_range=date_range
                    )

                    if dimension_data:
                        breakdown_data["data"].append({
                            "dimension": dimension,
                            "segments": dimension_data
                        })
                except Exception as dimension_error:
                    # Log error but continue with other dimensions
                    error_details = handle_exception(dimension_error, context={**context, "dimension": dimension})
                    logger.warning(f"Error processing dimension {dimension}: {error_details.message}")
                    failed_dimensions.append({"dimension": dimension, "error": error_details.message})

            # Include failed dimensions if any
            if failed_dimensions:
                breakdown_data["failed_dimensions"] = failed_dimensions

            return breakdown_data

        except ValueError as ve:
            error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
            logger.warning(f"Validation error retrieving performance breakdown: {error_details.message}")
            return {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "dimensions": dimensions,
                "date_range": date_range,
                "data": [],
                "error": error_details.message
            }
        except Exception as e:
            # Handle Google Ads API exceptions specifically
            if "GoogleAdsException" in str(type(e)):
                error_details = handle_google_ads_exception(e, context=context)
                logger.error(f"Google Ads API error retrieving performance breakdown: {error_details.message}")
            else:
                error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
                logger.error(f"Error retrieving breakdown data: {error_details.message}")

            return {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "dimensions": dimensions,
                "date_range": date_range,
                "data": [],
                "error": error_details.message
            }

    def _get_dimension_breakdown(self,
                               entity_type: str,
                               entity_id: Optional[str],
                               dimension: str,
                               date_range: str) -> List[Dict[str, Any]]:
        """
        Get breakdown data for a specific dimension.

        Args:
            entity_type: Type of entity ("account", "campaign", "ad_group")
            entity_id: ID of the entity (can be None for account-level breakdown)
            dimension: Dimension to break down by
            date_range: Date range for the breakdown data

        Returns:
            List of segments with performance data
        """
        context = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "dimension": dimension,
            "date_range": date_range,
            "method": "_get_dimension_breakdown"
        }

        try:
            # Map dimension names to Google Ads API segment names
            dimension_mapping = {
                "device": "device",
                "day": "date",
                "week": "week",
                "month": "month",
                "geo": "geo_target_country",
                "network": "network_type",
            }

            if dimension not in dimension_mapping:
                logger.warning(f"Unsupported dimension: {dimension}")
                return []

            api_dimension = dimension_mapping[dimension]

            # Call appropriate service method based on entity type and dimension
            if entity_type == "account":
                if dimension in ["day", "week", "month"]:
                    # For time dimensions, get time series data
                    return self.google_ads_service.get_account_performance_time_series(
                        date_range=date_range,
                        time_increment=dimension
                    )
                else:
                    # For other dimensions, get segmented data
                    return self.google_ads_service.get_account_performance_by_segment(
                        segment=api_dimension,
                        date_range=date_range
                    )
            elif entity_type == "campaign" and entity_id:
                if dimension in ["day", "week", "month"]:
                    return self.google_ads_service.get_campaign_performance_time_series(
                        campaign_id=entity_id,
                        date_range=date_range,
                        time_increment=dimension
                    )
                else:
                    return self.google_ads_service.get_campaign_performance_by_segment(
                        campaign_id=entity_id,
                        segment=api_dimension,
                        date_range=date_range
                    )
            elif entity_type == "ad_group" and entity_id:
                if dimension in ["day", "week", "month"]:
                    return self.google_ads_service.get_ad_group_performance_time_series(
                        ad_group_id=entity_id,
                        date_range=date_range,
                        time_increment=dimension
                    )
                else:
                    return self.google_ads_service.get_ad_group_performance_by_segment(
                        ad_group_id=entity_id,
                        segment=api_dimension,
                        date_range=date_range
                    )

            return []

        except Exception as e:
            error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
            logger.error(f"Error getting dimension breakdown: {error_details.message}")
            raise
