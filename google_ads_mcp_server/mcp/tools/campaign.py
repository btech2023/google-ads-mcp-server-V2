"""
Campaign Tools Module

This module contains campaign-related MCP tools.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from visualization.formatters import format_for_visualization
from visualization.campaign_charts import format_campaign_performance_chart, format_campaign_trend_chart, format_campaign_comparison_table
from visualization.dashboards import create_campaign_dashboard_visualization

from google_ads_mcp_server.utils.logging import get_logger
from google_ads_mcp_server.utils.validation import (
    validate_customer_id,
    validate_date_format,
    validate_numeric_range,
    validate_enum,
    validate_string_length
)
from google_ads_mcp_server.utils.error_handler import (
    create_error_response,
    handle_exception,
    CATEGORY_VALIDATION,
    SEVERITY_ERROR
)
from google_ads_mcp_server.utils.formatting import format_customer_id

logger = get_logger(__name__)

def register_campaign_tools(mcp, google_ads_service, campaign_service) -> None:
    """
    Register campaign-related MCP tools.

    Args:
        mcp: The MCP server instance
        google_ads_service: The Google Ads service instance
        campaign_service: The campaign service instance
    """
    @mcp.tool()
    async def get_campaign_performance(start_date: str = None, end_date: str = None, customer_id: str = None):
        """
        Get performance metrics for Google Ads campaigns.

        Args:
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            customer_id: Specific customer/account ID to query (defaults to the one in .env file)

        Returns:
            A formatted report of campaign performance metrics
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

            # Validate inputs
            input_errors = []

            if start_date and not validate_date_format(start_date):
                input_errors.append(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD.")

            if end_date and not validate_date_format(end_date):
                input_errors.append(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD.")

            if customer_id and not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            # Check date order
            if start_date and end_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                if start_dt > end_dt:
                    input_errors.append(f"start_date ({start_date}) must be before end_date ({end_date}).")

            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_campaign_performance: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "start_date": start_date, "end_date": end_date}
                ))

            logger.info(f"Getting campaign performance for customer ID {customer_id or 'default'}, date range: {start_date} to {end_date}")

            # Get campaign data
            campaigns = await google_ads_service.get_campaigns(start_date, end_date, customer_id)

            if not campaigns:
                return create_error_response(handle_exception(
                    ValueError("No campaigns found for the specified customer ID and date range."),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "start_date": start_date, "end_date": end_date}
                ))

            # Get the actual customer ID that was used (for display purposes)
            used_customer_id = customer_id or google_ads_service.client_customer_id
            if used_customer_id:
                # Format with dashes for display
                used_customer_id = format_customer_id(used_customer_id)

            # Format the results as a text report
            report = [
                f"Google Ads Campaign Performance Report",
                f"Account ID: {used_customer_id}",
                f"Date Range: {start_date} to {end_date}\n",
                f"{'Campaign ID':<15} {'Campaign Name':<30} {'Status':<15} {'Impressions':<12} {'Clicks':<8} {'Cost':<10} {'CTR':<8} {'CPC':<8}",
                "-" * 100
            ]

            # Add data rows
            for campaign in sorted(campaigns, key=lambda x: x["cost"], reverse=True):
                name = campaign["name"]
                if len(name) > 27:
                    name = name[:24] + "..."

                ctr = (campaign["clicks"] / campaign["impressions"] * 100) if campaign["impressions"] > 0 else 0
                cpc = campaign["cost"] / campaign["clicks"] if campaign["clicks"] > 0 else 0

                report.append(
                    f"{campaign['id']:<15} {name:<30} {campaign['status']:<15} "
                    f"{int(campaign['impressions']):,d} {int(campaign['clicks']):,d} "
                    f"${campaign['cost']:,.2f} {ctr:.2f}% ${cpc:.2f}"
                )

            return "\n".join(report)

        except Exception as e:
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "start_date": start_date, "end_date": end_date}
            )
            logger.error(f"Error getting campaign performance: {str(e)}")
            return create_error_response(error_details)

    @mcp.tool()
    async def get_campaigns(customer_id: str, status: str = None):
        """
        Get campaigns for a Google Ads account with optional filtering.

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            status: Optional status filter (ENABLED, PAUSED, REMOVED, etc.)

        Returns:
            Formatted list of campaigns
        """
        try:
            # Validate inputs
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            if status and not validate_enum(status, ["ENABLED", "PAUSED", "REMOVED", "UNKNOWN"], case_sensitive=False):
                input_errors.append(f"Invalid status: {status}. Expected one of: ENABLED, PAUSED, REMOVED, UNKNOWN.")

            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_campaigns: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "status": status}
                ))

            # Remove dashes from customer ID if present
            clean_customer_id = customer_id.replace('-', '') if customer_id else None

            logger.info(f"Getting campaigns for customer ID {clean_customer_id}")

            # Get campaigns using the CampaignService
            campaigns = await campaign_service.get_campaigns(
                customer_id=clean_customer_id,
                status_filter=status
            )

            if not campaigns:
                return create_error_response(handle_exception(
                    ValueError("No campaigns found with the specified filters."),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "status": status}
                ))

            # Format with dashes for display
            display_customer_id = format_customer_id(clean_customer_id)

            # Format the results as a text report
            report = [
                f"Google Ads Campaigns",
                f"Account ID: {display_customer_id}",
                f"Status Filter: {status if status else 'All Statuses'}\n",
                f"{'Campaign ID':<15} {'Campaign Name':<30} {'Status':<15} {'Budget':<15} {'Channel':<20} {'Bidding Strategy':<20}",
                "-" * 115
            ]

            # Add data rows
            for campaign in sorted(campaigns, key=lambda x: x["name"]):
                name = campaign["name"]
                if len(name) > 27:
                    name = name[:24] + "..."

                # Format budget
                budget = f"${campaign.get('budget_amount', 0):,.2f}"

                # Format channel type
                channel = campaign.get("advertising_channel_type", "Unknown")

                # Format bidding strategy
                bidding = campaign.get("bidding_strategy_type", "Unknown")
                if len(bidding) > 17:
                    bidding = bidding[:14] + "..."

                report.append(
                    f"{campaign['id']:<15} {name:<30} {campaign['status']:<15} "
                    f"{budget:<15} {channel:<20} {bidding:<20}"
                )

            return "\n".join(report)

        except Exception as e:
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "status": status}
            )
            logger.error(f"Error getting campaigns: {str(e)}")
            return create_error_response(error_details)

    @mcp.tool()
    async def get_campaign_dashboard_json(campaign_id: str, date_range: str = "LAST_30_DAYS", comparison_range: str = "PREVIOUS_30_DAYS"):
        """
        Get a comprehensive campaign dashboard in JSON format for visualization.

        The dashboard includes:
        - Campaign KPI cards with period-over-period comparison
        - Trend charts for key metrics
        - Ad group performance
        - Device and network distribution

        Args:
            campaign_id: The campaign ID to analyze
            date_range: Date range for the dashboard. Supported values:
                        LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS,
                        THIS_MONTH, LAST_MONTH, THIS_QUARTER, LAST_QUARTER
            comparison_range: Comparison period for period-over-period metrics.
                             Supported values: PREVIOUS_7_DAYS, PREVIOUS_30_DAYS,
                             PREVIOUS_90_DAYS, PREVIOUS_MONTH, PREVIOUS_QUARTER

        Returns:
            JSON data with dashboard visualizations
        """
        try:
            logger.info(f"Getting campaign dashboard for campaign ID {campaign_id}, date range {date_range}")

            # Validate inputs
            input_errors = []

            if not validate_string_length(campaign_id, min_length=1):
                input_errors.append("Campaign ID is required.")

            # Validate date range input
            valid_date_ranges = [
                "LAST_7_DAYS", "LAST_30_DAYS", "LAST_90_DAYS",
                "THIS_MONTH", "LAST_MONTH", "THIS_QUARTER", "LAST_QUARTER"
            ]

            if not validate_enum(date_range, valid_date_ranges):
                input_errors.append(f"Invalid date_range. Supported values: {', '.join(valid_date_ranges)}")

            # Validate comparison range input
            valid_comparison_ranges = [
                "PREVIOUS_7_DAYS", "PREVIOUS_30_DAYS", "PREVIOUS_90_DAYS",
                "PREVIOUS_MONTH", "PREVIOUS_QUARTER", "NONE"
            ]

            if comparison_range and not validate_enum(comparison_range, valid_comparison_ranges):
                input_errors.append(f"Invalid comparison_range. Supported values: {', '.join(valid_comparison_ranges)}")

            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_campaign_dashboard_json: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"campaign_id": campaign_id, "date_range": date_range, "comparison_range": comparison_range}
                ))

            # Set comparison_range to None if "NONE" is specified
            if comparison_range == "NONE":
                comparison_range = None

            # Get dashboard data from service
            dashboard_data = await campaign_service.get_campaign_dashboard(
                campaign_id=campaign_id,
                date_range=date_range,
                comparison_range=comparison_range
            )

            # Check if there was an error
            if isinstance(dashboard_data, dict) and "error" in dashboard_data:
                return create_error_response(handle_exception(
                    ValueError(dashboard_data["error"]),
                    context={"campaign_id": campaign_id, "date_range": date_range, "comparison_range": comparison_range}
                ))

            # Generate visualization
            visualization = create_campaign_dashboard_visualization(
                dashboard_data,
                dashboard_data.get("comparison_metrics", None) if comparison_range else None
            )

            return {
                "type": "success",
                "data": dashboard_data,
                "visualization": visualization
            }

        except Exception as e:
            error_details = handle_exception(
                e,
                context={"campaign_id": campaign_id, "date_range": date_range, "comparison_range": comparison_range}
            )
            logger.error(f"Error getting campaign dashboard: {str(e)}")
            return create_error_response(error_details)

    @mcp.tool()
    async def get_campaign_performance(customer_id: str, campaign_id: str, date_range: int = 30):
        """
        Get performance metrics for a specific campaign.

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            campaign_id: Campaign ID
            date_range: Number of days of data to retrieve (default: 30)

        Returns:
            Formatted performance report for the campaign
        """
        try:
            # Validate inputs
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            if not validate_string_length(campaign_id, min_length=1):
                input_errors.append("Campaign ID is required.")

            if not validate_numeric_range(date_range, min_value=1, max_value=365):
                input_errors.append(f"Invalid date_range: {date_range}. Expected a value between 1 and 365.")

            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_campaign_performance: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "campaign_id": campaign_id, "date_range": date_range}
                ))

            # Remove dashes from customer ID if present
            clean_customer_id = customer_id.replace('-', '')

            logger.info(f"Getting performance for campaign ID {campaign_id}")

            # Calculate date range
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=date_range)).strftime("%Y-%m-%d")

            # Get campaign performance using the CampaignService
            performance = await campaign_service.get_campaign_performance(
                customer_id=clean_customer_id,
                campaign_id=campaign_id,
                start_date=start_date,
                end_date=end_date
            )

            if not performance:
                return create_error_response(handle_exception(
                    ValueError(f"No performance data found for campaign ID {campaign_id}."),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "campaign_id": campaign_id, "date_range": date_range}
                ))

            # Format with dashes for display
            display_customer_id = format_customer_id(clean_customer_id)

            # Format the results as a text report
            report = [
                f"Google Ads Campaign Performance Report",
                f"Account ID: {display_customer_id}",
                f"Campaign ID: {campaign_id}",
                f"Date Range: {start_date} to {end_date}\n",
                "Performance Summary:",
                f"- Impressions: {int(performance['impressions']):,d}",
                f"- Clicks: {int(performance['clicks']):,d}",
                f"- Cost: ${performance['cost']:,.2f}",
                f"- Conversions: {performance['conversions']:,.2f}",
                f"- Conversion Value: ${performance['conversion_value']:,.2f}\n",
                "Key Metrics:",
                f"- CTR: {performance['ctr']:.2f}%",
                f"- CPC: ${performance['cpc']:,.2f}",
                f"- ROAS: {performance['roas']:.2f}x",
                "\nDaily Performance:",
                f"{'Date':<12} {'Impressions':<12} {'Clicks':<8} {'Cost':<10} {'Conv.':<8} {'Value':<10}",
                "-" * 60
            ]

            # Add daily data rows
            for day in performance['daily_stats']:
                report.append(
                    f"{day['date']:<12} {int(day['impressions']):,d} {int(day['clicks']):,d} "
                    f"${day['cost']:,.2f} {day['conversions']:,.2f} ${day['conversion_value']:,.2f}"
                )

            return "\n".join(report)

        except Exception as e:
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "campaign_id": campaign_id, "date_range": date_range}
            )
            logger.error(f"Error getting campaign performance: {str(e)}")
            return create_error_response(error_details)

    # Related: mcp.tools.dashboard.get_campaign_dashboard_json (Provides a comprehensive dashboard for the campaign)
    @mcp.tool()
    async def get_campaign_performance_json(customer_id: str, campaign_id: str, date_range: int = 30):
        """
        Get performance metrics for a specific campaign in JSON format for visualization.

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            campaign_id: Campaign ID
            date_range: Number of days of data to retrieve (default: 30)

        Returns:
            JSON data for campaign performance visualization
        """
        try:
            # Validate inputs
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            if not validate_string_length(campaign_id, min_length=1):
                input_errors.append("Campaign ID is required.")

            if not validate_numeric_range(date_range, min_value=1, max_value=365):
                input_errors.append(f"Invalid date_range: {date_range}. Expected a value between 1 and 365.")

            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_campaign_performance_json: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "campaign_id": campaign_id, "date_range": date_range}
                ))

            # Remove dashes from customer ID if present
            clean_customer_id = customer_id.replace('-', '')

            logger.info(f"Getting performance for campaign ID {campaign_id}")

            # Calculate date range
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=date_range)).strftime("%Y-%m-%d")

            # Get campaign performance using the CampaignService
            performance = await campaign_service.get_campaign_performance(
                customer_id=clean_customer_id,
                campaign_id=campaign_id,
                start_date=start_date,
                end_date=end_date
            )

            if not performance:
                return create_error_response(handle_exception(
                    ValueError(f"No performance data found for campaign ID {campaign_id}."),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "campaign_id": campaign_id, "date_range": date_range}
                ))

            # Format with dashes for display
            display_customer_id = format_customer_id(clean_customer_id)

            # Format the results for visualization
            formatted_data = format_for_visualization({
                "customer_id": clean_customer_id,
                "campaign_id": campaign_id,
                "start_date": start_date,
                "end_date": end_date,
                "performance": performance
            })

            # Create visualizations
            visualizations = {
                "performance_chart": format_campaign_performance_chart(performance),
                "trend_chart": format_campaign_trend_chart(performance['daily_stats']),
                "comparison_table": format_campaign_comparison_table(performance)
            }

            return {
                "type": "success",
                "data": formatted_data,
                "visualizations": visualizations
            }

        except Exception as e:
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "campaign_id": campaign_id, "date_range": date_range}
            )
            logger.error(f"Error getting campaign performance JSON: {str(e)}")
            return create_error_response(error_details)
