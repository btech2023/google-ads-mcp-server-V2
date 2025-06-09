"""
Dashboard Tools Module

This module contains dashboard-related MCP tools for visualizing Google Ads data.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from google_ads_mcp_server.utils.logging import get_logger
from google_ads_mcp_server.utils.validation import (
    validate_customer_id,
    validate_date_format,
    validate_enum,
    validate_string_length
)
from google_ads_mcp_server.utils.error_handler import (
    create_error_response,
    handle_exception,
    CATEGORY_VALIDATION,
    SEVERITY_ERROR
)
from google_ads_mcp_server.utils.formatting import format_customer_id, clean_customer_id

from visualization.formatters import format_for_visualization
from visualization.dashboards import create_account_dashboard_visualization, create_campaign_dashboard_visualization

# Replace standard logger with utils-provided logger
logger = get_logger(__name__)

def register_dashboard_tools(mcp, google_ads_service, dashboard_service) -> None:
    """
    Register dashboard-related MCP tools.

    Args:
        mcp: The MCP server instance
        google_ads_service: The Google Ads service instance
        dashboard_service: The dashboard service instance
    """
    # Related: mcp.tools.campaign.get_campaigns (Account dashboard includes campaign data)
    # Related: mcp.tools.ad_group.get_ad_groups (Account dashboard includes ad group data)
    # Related: mcp.tools.keyword.get_keywords (Account dashboard may include keyword data)
    @mcp.tool()
    async def get_account_dashboard_json(customer_id: str, date_range: str = "LAST_30_DAYS", comparison_range: str = "PREVIOUS_30_DAYS"):
        """
        Get a comprehensive account dashboard with KPIs, trends, and top performers.

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            date_range: Date range for the dashboard (e.g., LAST_30_DAYS, LAST_7_DAYS, LAST_90_DAYS)
            comparison_range: Period to compare against (e.g., PREVIOUS_30_DAYS, PREVIOUS_YEAR)

        Returns:
            JSON data for account dashboard visualization
        """
        try:
            # Validate inputs
            input_errors = []

            # Validate customer_id
            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            # Validate date_range
            valid_date_ranges = ["LAST_7_DAYS", "LAST_14_DAYS", "LAST_30_DAYS", "LAST_90_DAYS", "THIS_MONTH", "LAST_MONTH"]
            if not validate_enum(date_range, valid_date_ranges):
                input_errors.append(f"Invalid date_range: {date_range}. Expected one of: {', '.join(valid_date_ranges)}.")

            # Validate comparison_range - note: Added more options based on possible usage
            valid_comparison_ranges = ["PREVIOUS_7_DAYS", "PREVIOUS_14_DAYS", "PREVIOUS_30_DAYS", "PREVIOUS_90_DAYS", "PREVIOUS_MONTH", "PREVIOUS_YEAR"]
            if not validate_enum(comparison_range, valid_comparison_ranges):
                input_errors.append(f"Invalid comparison_range: {comparison_range}. Expected one of: {', '.join(valid_comparison_ranges)}.")

            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_account_dashboard_json: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "date_range": date_range, "comparison_range": comparison_range}
                ))

            # Clean customer ID using utility function
            clean_cid = clean_customer_id(customer_id)

            logger.info(f"Getting account dashboard for customer ID {clean_cid}, date range: {date_range}, comparison: {comparison_range}")

            # Get dashboard data using the DashboardService
            dashboard_data = await dashboard_service.get_account_dashboard(
                customer_id=clean_cid,
                date_range=date_range,
                comparison_range=comparison_range
            )

            # Standardize error handling for service response
            if not dashboard_data or "error" in dashboard_data:
                error_message = dashboard_data.get("error", "Failed to retrieve account dashboard data")
                logger.error(f"Error getting account dashboard from service: {error_message}")
                return create_error_response(handle_exception(
                    ValueError(error_message),
                    category=CATEGORY_VALIDATION, # Or potentially CATEGORY_API_ERROR depending on service detail
                    context={"customer_id": customer_id, "date_range": date_range}
                ))

            # Format display customer ID with dashes using utility function
            display_customer_id = format_customer_id(clean_cid)

            # Create visualization using the formatter
            visualization = create_account_dashboard_visualization(
                account_data=dashboard_data
            )

            # Return the formatted dashboard response
            return {
                "type": "success",
                "data": {
                    "customer_id": display_customer_id,
                    "date_range": date_range,
                    "comparison_range": comparison_range,
                    "account_name": dashboard_data.get("account_name", "My Account"),
                    "metrics": dashboard_data.get("metrics", {}),
                    "time_series": dashboard_data.get("time_series", []),
                    "campaigns": dashboard_data.get("campaigns", []),
                    "ad_groups": dashboard_data.get("ad_groups", [])
                },
                "visualization": visualization
            }
        except Exception as e:
            # Standardize exception handling
            error_details = handle_exception(
                e,
                context={
                    "customer_id": customer_id,
                    "date_range": date_range,
                    "comparison_range": comparison_range
                }
            )
            logger.error(f"Error getting account dashboard: {str(e)}")
            return create_error_response(error_details)

    # Related: mcp.tools.campaign.get_campaign_performance (Campaign dashboard extends campaign performance)
    # Related: mcp.tools.ad_group.get_ad_groups (Campaign dashboard includes ad group data)
    # Related: mcp.tools.keyword.get_keywords (Campaign dashboard includes keyword data)
    @mcp.tool()
    async def get_campaign_dashboard_json(customer_id: str, campaign_id: str, date_range: str = "LAST_30_DAYS", comparison_range: str = "PREVIOUS_30_DAYS"):
        """
        Get a detailed dashboard for a specific campaign.

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            campaign_id: Campaign ID
            date_range: Date range for the dashboard (e.g., LAST_30_DAYS, LAST_7_DAYS, LAST_90_DAYS)
            comparison_range: Period to compare against (e.g., PREVIOUS_30_DAYS, PREVIOUS_YEAR)

        Returns:
            JSON data for campaign dashboard visualization
        """
        try:
            # Validate inputs
            input_errors = []

            # Validate customer_id
            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            # Validate campaign_id
            if not validate_string_length(campaign_id, min_length=1):
                 input_errors.append(f"Invalid campaign_id: {campaign_id}. Must be a non-empty string.")

            # Validate date_range
            valid_date_ranges = ["LAST_7_DAYS", "LAST_14_DAYS", "LAST_30_DAYS", "LAST_90_DAYS", "THIS_MONTH", "LAST_MONTH"]
            if not validate_enum(date_range, valid_date_ranges):
                input_errors.append(f"Invalid date_range: {date_range}. Expected one of: {', '.join(valid_date_ranges)}.")

            # Validate comparison_range
            valid_comparison_ranges = ["PREVIOUS_7_DAYS", "PREVIOUS_14_DAYS", "PREVIOUS_30_DAYS", "PREVIOUS_90_DAYS", "PREVIOUS_MONTH", "PREVIOUS_YEAR"]
            if not validate_enum(comparison_range, valid_comparison_ranges):
                input_errors.append(f"Invalid comparison_range: {comparison_range}. Expected one of: {', '.join(valid_comparison_ranges)}.")

            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_campaign_dashboard_json: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "campaign_id": campaign_id, "date_range": date_range, "comparison_range": comparison_range}
                ))

            # Clean customer ID using utility function
            clean_cid = clean_customer_id(customer_id)

            logger.info(f"Getting campaign dashboard for campaign ID {campaign_id}, customer ID {clean_cid}, date range: {date_range}")

            # Get dashboard data using the DashboardService
            dashboard_data = await dashboard_service.get_campaign_dashboard(
                customer_id=clean_cid,
                campaign_id=campaign_id,
                date_range=date_range,
                comparison_range=comparison_range
            )

            # Standardize error handling for service response
            if not dashboard_data or "error" in dashboard_data:
                error_message = dashboard_data.get("error", "Failed to retrieve campaign dashboard data")
                logger.error(f"Error getting campaign dashboard from service: {error_message}")
                return create_error_response(handle_exception(
                    ValueError(error_message),
                    category=CATEGORY_VALIDATION, # Or API_ERROR
                    context={"customer_id": customer_id, "campaign_id": campaign_id, "date_range": date_range}
                ))

            # Format display customer ID with dashes using utility function
            display_customer_id = format_customer_id(clean_cid)

            # Create visualization using the formatter
            visualization = create_campaign_dashboard_visualization(
                campaign_data=dashboard_data
            )

            # Return the formatted dashboard response
            return {
                "type": "success",
                "data": {
                    "customer_id": display_customer_id,
                    "campaign_id": campaign_id,
                    "campaign_name": dashboard_data.get("name", "Unknown Campaign"),
                    "date_range": date_range,
                    "comparison_range": comparison_range,
                    "metrics": dashboard_data.get("metrics", {}),
                    "time_series": dashboard_data.get("time_series", []),
                    "ad_groups": dashboard_data.get("ad_groups", []),
                    "device_performance": dashboard_data.get("device_performance", []),
                    "keywords": dashboard_data.get("keywords", [])
                },
                "visualization": visualization
            }
        except Exception as e:
            # Standardize exception handling
            error_details = handle_exception(
                e,
                context={
                    "customer_id": customer_id,
                    "campaign_id": campaign_id,
                    "date_range": date_range,
                    "comparison_range": comparison_range
                }
            )
            logger.error(f"Error getting campaign dashboard: {str(e)}")
            return create_error_response(error_details)

    # Related: mcp.tools.campaign.get_campaigns (Compares multiple campaigns)
    @mcp.tool()
    async def get_campaigns_comparison_json(customer_id: str, campaign_ids: str, date_range: str = "LAST_30_DAYS", metrics: str = None):
        """
        Compare performance metrics across multiple campaigns.

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            campaign_ids: Comma-separated list of campaign IDs to compare
            date_range: Date range for the comparison (e.g., LAST_30_DAYS, LAST_7_DAYS)
            metrics: Optional comma-separated list of metrics to include (defaults to key metrics)

        Returns:
            JSON data for campaigns comparison visualization
        """
        try:
            # Validate inputs
            input_errors = []

            # Validate customer_id
            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            # Validate campaign_ids
            if not validate_string_length(campaign_ids, min_length=1):
                 input_errors.append(f"Invalid campaign_ids: {campaign_ids}. Must be a non-empty comma-separated string.")
            else:
                # Basic check for comma separation and non-empty IDs
                 campaign_id_list_val = [cid.strip() for cid in campaign_ids.split(",") if cid.strip()]
                 if not campaign_id_list_val:
                     input_errors.append(f"Invalid campaign_ids: {campaign_ids}. Must contain at least one valid campaign ID.")
                 elif len(campaign_id_list_val) != len(campaign_ids.split(",")):
                     input_errors.append(f"Invalid campaign_ids format: {campaign_ids}. Ensure IDs are separated by commas without extra empty entries.")

            # Validate date_range
            valid_date_ranges = ["LAST_7_DAYS", "LAST_14_DAYS", "LAST_30_DAYS", "LAST_90_DAYS", "THIS_MONTH", "LAST_MONTH"]
            if not validate_enum(date_range, valid_date_ranges):
                input_errors.append(f"Invalid date_range: {date_range}. Expected one of: {', '.join(valid_date_ranges)}.")

            # Validate metrics if provided
            metric_list = None
            if metrics:
                 if not validate_string_length(metrics, min_length=1):
                     input_errors.append(f"Invalid metrics: {metrics}. Must be a non-empty comma-separated string.")
                 else:
                     metric_list = [m.strip() for m in metrics.split(",") if m.strip()]
                     if not metric_list:
                         input_errors.append(f"Invalid metrics format: {metrics}. Must contain at least one metric.")
                     elif len(metric_list) != len(metrics.split(",")):
                         input_errors.append(f"Invalid metrics format: {metrics}. Ensure metrics are separated by commas without extra empty entries.")

            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_campaigns_comparison_json: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "campaign_ids": campaign_ids, "date_range": date_range, "metrics": metrics}
                ))

            # Clean customer ID using utility function
            clean_cid = clean_customer_id(customer_id)

            # Parse campaign IDs (already validated partially)
            campaign_id_list = [cid.strip() for cid in campaign_ids.split(",") if cid.strip()]

            logger.info(f"Getting campaigns comparison for campaign IDs: {campaign_id_list}, customer ID {clean_cid}")

            # Get comparison data using the DashboardService
            comparison_data = await dashboard_service.get_campaigns_comparison(
                customer_id=clean_cid,
                campaign_ids=campaign_id_list,
                date_range=date_range,
                metrics=metric_list # Use validated metric list
            )

            # Standardize error handling for service response
            if not comparison_data or "error" in comparison_data:
                error_message = comparison_data.get("error", "Failed to retrieve campaigns comparison data")
                logger.error(f"Error getting campaigns comparison from service: {error_message}")
                return create_error_response(handle_exception(
                    ValueError(error_message),
                    category=CATEGORY_VALIDATION, # Or API_ERROR
                    context={"customer_id": customer_id, "campaign_ids": campaign_ids, "date_range": date_range}
                ))

            # Format display customer ID with dashes using utility function
            display_customer_id = format_customer_id(clean_cid)

            # Create visualization for campaign comparison
            visualization = {
                "title": "Campaign Performance Comparison",
                "description": f"Comparing {len(campaign_id_list)} campaigns for {date_range}",
                "charts": [
                    # Bar chart for each metric
                    {
                        "chart_type": "bar",
                        "title": f"Campaign Comparison - {metric.replace('_', ' ').title()}"
                                if not metric.endswith("micros") else
                                f"Campaign Comparison - {metric.replace('_micros', '').replace('_', ' ').title()}",
                        "labels": [c.get("name", f"Campaign {c.get('id', 'Unknown')}") for c in comparison_data.get("campaigns", [])],
                        "values": [c.get(metric, 0) if not metric.endswith("micros") else c.get(metric, 0) / 1000000
                                  for c in comparison_data.get("campaigns", [])],
                        "format": "currency" if metric.endswith("micros") else ("percentage" if metric in ["ctr", "conversion_rate"] else None)
                    }
                    # Limit visualization to a reasonable number of metrics if many are returned
                    for metric in comparison_data.get("metrics", [])[:5]
                ],
                # Comparison table with all metrics
                "table": {
                    "title": "Campaign Performance Metrics",
                    "headers": ["Campaign", "Status"] +
                               [metric.replace("_micros", "").replace("_", " ").title()
                                for metric in comparison_data.get("metrics", [])],
                    "rows": [
                        [
                            c.get("name", "Unknown"),
                            c.get("status", "Unknown")
                        ] +
                        [
                            f"${c.get(metric, 0) / 1000000:.2f}" if metric.endswith("micros") else
                            f"{c.get(metric, 0):.2f}%" if metric in ["ctr", "conversion_rate"] else
                            f"{c.get(metric, 0):,}"
                            for metric in comparison_data.get("metrics", [])
                        ]
                        for c in comparison_data.get("campaigns", [])
                    ]
                }
            }

            # Return the formatted comparison response
            return {
                "type": "success",
                "data": {
                    "customer_id": display_customer_id,
                    "date_range": date_range,
                    "campaigns": comparison_data.get("campaigns", []),
                    "metrics": comparison_data.get("metrics", [])
                },
                "visualization": visualization
            }

        except Exception as e:
            # Standardize exception handling
            error_details = handle_exception(
                e,
                context={
                    "customer_id": customer_id,
                    "campaign_ids": campaign_ids,
                    "date_range": date_range,
                    "metrics": metrics
                }
            )
            logger.error(f"Error getting campaigns comparison: {str(e)}")
            return create_error_response(error_details)

    # Related: mcp.tools.campaign.get_campaign_performance (Provides entity performance breakdown)
    # Related: mcp.tools.ad_group.get_ad_group_performance (Provides entity performance breakdown)
    @mcp.tool()
    async def get_performance_breakdown_json(customer_id: str, entity_type: str, entity_id: str = None, dimensions: str = "device", date_range: str = "LAST_30_DAYS"):
        """
        Break down performance by various dimensions (device, geo, time, etc.).

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            entity_type: Type of entity ("account", "campaign", or "ad_group")
            entity_id: Optional ID of the entity (required if entity_type is "campaign" or "ad_group")
            dimensions: Comma-separated list of dimensions to break down by (device, day, week, month, geo, network)
            date_range: Date range for the breakdown (e.g., LAST_30_DAYS, LAST_7_DAYS)

        Returns:
            JSON data for performance breakdown visualization
        """
        try:
            # Validate inputs
            input_errors = []

            # Validate customer_id
            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            # Validate entity_type
            valid_entity_types = ["account", "campaign", "ad_group"]
            if not validate_enum(entity_type, valid_entity_types):
                input_errors.append(f"Invalid entity_type: {entity_type}. Expected one of: {', '.join(valid_entity_types)}.")

            # Validate entity_id when required
            if entity_type in ["campaign", "ad_group"]:
                if not entity_id:
                    input_errors.append(f"entity_id is required when entity_type is '{entity_type}'.")
                elif not validate_string_length(entity_id, min_length=1):
                    input_errors.append(f"Invalid entity_id: {entity_id}. Must be a non-empty string.")

            # Validate date_range
            valid_date_ranges = ["LAST_7_DAYS", "LAST_14_DAYS", "LAST_30_DAYS", "LAST_90_DAYS", "THIS_MONTH", "LAST_MONTH"]
            if not validate_enum(date_range, valid_date_ranges):
                input_errors.append(f"Invalid date_range: {date_range}. Expected one of: {', '.join(valid_date_ranges)}.")

            # Validate dimensions
            if not validate_string_length(dimensions, min_length=1):
                input_errors.append(f"Invalid dimensions: {dimensions}. Must be a non-empty comma-separated string.")
            else:
                valid_dimensions_enum = ["device", "day", "week", "month", "geo", "network"]
                dimension_list_val = [dim.strip() for dim in dimensions.split(",") if dim.strip()]
                if not dimension_list_val:
                    input_errors.append(f"Invalid dimensions format: {dimensions}. Must contain at least one dimension.")
                else:
                    for dimension in dimension_list_val:
                        if not validate_enum(dimension, valid_dimensions_enum):
                            input_errors.append(f"Invalid dimension value: {dimension}. Expected one of: {', '.join(valid_dimensions_enum)}.")

            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_performance_breakdown_json: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "entity_type": entity_type, "entity_id": entity_id, "dimensions": dimensions, "date_range": date_range}
                ))

            # Clean customer ID using utility function
            clean_cid = clean_customer_id(customer_id)

            # Parse dimensions (already validated)
            dimension_list = [dim.strip() for dim in dimensions.split(",") if dim.strip()]

            logger.info(f"Getting performance breakdown for {entity_type} {entity_id or 'account'}, dimensions: {dimension_list}")

            # Get breakdown data using the DashboardService
            breakdown_data = await dashboard_service.get_performance_breakdown(
                customer_id=clean_cid,
                entity_type=entity_type,
                entity_id=entity_id,
                dimensions=dimension_list,
                date_range=date_range
            )

            # Standardize error handling for service response
            if not breakdown_data or "error" in breakdown_data:
                error_message = breakdown_data.get("error", "Failed to retrieve performance breakdown data")
                logger.error(f"Error getting performance breakdown from service: {error_message}")
                return create_error_response(handle_exception(
                    ValueError(error_message),
                    category=CATEGORY_VALIDATION, # Or API_ERROR
                    context={"customer_id": customer_id, "entity_type": entity_type, "entity_id": entity_id, "dimensions": dimensions}
                ))

            # Format display customer ID with dashes using utility function
            display_customer_id = format_customer_id(clean_cid)

            # Create visualizations for each dimension
            visualization = {
                "title": f"{breakdown_data.get('entity_name', entity_type.title())} Performance Breakdown",
                "description": f"Breakdown by {dimensions} for {date_range}",
                "charts": [],
                "table": None # Initialize table
            }

            # Process each dimension's data for visualization
            # Note: This assumes breakdown_data['data'] is a list of dicts, one per dimension requested
            processed_dimensions = 0
            for dimension_data in breakdown_data.get("data", []):
                dimension = dimension_data.get("dimension")
                segments = dimension_data.get("segments", [])

                if not dimension or not segments:
                    logger.warning(f"Missing dimension or segments in breakdown data for {dimension}")
                    continue

                processed_dimensions += 1

                # Time-based dimensions (day, week, month) get line charts
                if dimension in ["day", "week", "month"]:
                    metrics_to_show = ["impressions", "clicks", "cost", "conversions"] # Key metrics
                    for metric in metrics_to_show:
                        chart_values = [
                            segment.get(metric, 0) if metric != "cost" else segment.get("cost_micros", 0) / 1000000
                            for segment in segments
                        ]
                        chart_labels = [segment.get(dimension, "Unknown") for segment in segments]

                        # Skip chart if no data
                        if not any(v for v in chart_values if v is not None and v != 0): continue

                        chart = {
                            "chart_type": "line",
                            "title": f"{metric.replace('_', ' ').title()} by {dimension.title()}",
                            "labels": chart_labels,
                            "values": chart_values,
                            "format": "currency" if metric == "cost" else ("percentage" if metric in ["ctr", "conversion_rate"] else None)
                        }
                        visualization["charts"].append(chart)

                # Categorical dimensions (device, geo, network) get pie/bar charts
                else:
                    # Cost distribution
                    cost_labels = [segment.get(dimension, "Unknown") for segment in segments]
                    cost_values = [segment.get("cost_micros", 0) / 1000000 for segment in segments]
                    if any(v for v in cost_values if v is not None and v != 0): # Check if there's data
                        cost_chart = {
                            "chart_type": "pie" if len(segments) <= 6 else "bar", # Pie for few segments
                            "title": f"Cost Distribution by {dimension.title()}",
                            "labels": cost_labels,
                            "values": cost_values,
                            "format": "currency"
                        }
                        visualization["charts"].append(cost_chart)

                    # Clicks distribution (example - could add others like conversions)
                    click_labels = [segment.get(dimension, "Unknown") for segment in segments]
                    click_values = [segment.get("clicks", 0) for segment in segments]
                    if any(v for v in click_values if v is not None and v != 0): # Check if there's data
                        clicks_chart = {
                            "chart_type": "pie" if len(segments) <= 6 else "bar",
                            "title": f"Clicks Distribution by {dimension.title()}",
                            "labels": click_labels,
                            "values": click_values
                        }
                        visualization["charts"].append(clicks_chart)

                # Add a data table only for the *first* dimension processed for simplicity
                # A multi-dimension table could be complex to render/interpret
                if processed_dimensions == 1:
                    table_rows = []
                    for segment in segments:
                         # Safely calculate CTR
                        impressions = segment.get('impressions', 0)
                        clicks = segment.get('clicks', 0)
                        ctr_str = f"{(clicks / impressions * 100):.2f}%" if impressions > 0 else "0.00%"

                        table_rows.append([
                            segment.get(dimension, "Unknown"),
                            f"{impressions:,}",
                            f"{clicks:,}",
                            f"${segment.get('cost_micros', 0) / 1000000:.2f}",
                            ctr_str,
                            f"{segment.get('conversions', 0):.1f}"
                        ])

                    if table_rows:
                        visualization["table"] = {
                            "title": f"Performance by {dimension.title()}",
                            "headers": [dimension.title(), "Impressions", "Clicks", "Cost", "CTR", "Conv."],
                            "rows": table_rows
                        }

            # Handle case where no valid dimensions were processed
            if processed_dimensions == 0:
                 logger.warning(f"No valid breakdown data processed for dimensions: {dimensions}")
                 # Optionally return an error or an empty success state
                 return create_error_response(handle_exception(
                     ValueError(f"Could not generate breakdown for dimensions: {dimensions}. Data might be missing or invalid."),
                     category=CATEGORY_VALIDATION,
                     context={"customer_id": customer_id, "entity_type": entity_type, "dimensions": dimensions}
                 ))

            # Return the formatted breakdown response
            return {
                "type": "success",
                "data": {
                    "customer_id": display_customer_id,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "entity_name": breakdown_data.get("entity_name", ""),
                    "date_range": date_range,
                    "dimensions": dimension_list,
                    "breakdown_data": breakdown_data.get("data", []) # Return raw data as well
                },
                "visualization": visualization
            }

        except Exception as e:
            # Standardize exception handling
            error_details = handle_exception(
                e,
                context={
                    "customer_id": customer_id,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "dimensions": dimensions,
                    "date_range": date_range
                }
            )
            logger.error(f"Error getting performance breakdown: {str(e)}")
            return create_error_response(error_details)
