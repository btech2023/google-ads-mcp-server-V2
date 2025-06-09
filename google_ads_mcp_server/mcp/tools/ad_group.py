"""
Ad Group Tools Module

This module contains ad group-related MCP tools.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from visualization.formatters import format_for_visualization
from visualization.ad_groups import format_ad_group_comparison, format_ad_group_performance_time_series, format_ad_group_status_distribution

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

def register_ad_group_tools(mcp, google_ads_service, ad_group_service) -> None:
    """
    Register ad group-related MCP tools.

    Args:
        mcp: The MCP server instance
        google_ads_service: The Google Ads service instance
        ad_group_service: The ad group service instance
    """
    # Related: mcp.tools.keyword.get_keywords (Ad groups contain keywords)
    @mcp.tool()
    async def get_ad_groups(customer_id: str, campaign_id: str = None, status: str = None):
        """
        Get ad groups for a Google Ads account with optional filtering.

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            campaign_id: Optional campaign ID to filter by
            status: Optional status filter (ENABLED, PAUSED, REMOVED)

        Returns:
            Formatted list of ad groups
        """
        try:
            # Validate inputs
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            if campaign_id and not validate_string_length(campaign_id, min_length=1):
                input_errors.append(f"Invalid campaign_id: {campaign_id}.")

            if status and not validate_enum(status, ["ENABLED", "PAUSED", "REMOVED", "UNKNOWN"], case_sensitive=False):
                input_errors.append(f"Invalid status: {status}. Expected one of: ENABLED, PAUSED, REMOVED, UNKNOWN.")

            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_ad_groups: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "campaign_id": campaign_id, "status": status}
                ))

            # Remove dashes from customer ID if present
            clean_customer_id = customer_id.replace('-', '')

            logger.info(f"Getting ad groups for customer ID {clean_customer_id}")

            # Get ad groups using the AdGroupService
            ad_groups = await ad_group_service.get_ad_groups(
                customer_id=clean_customer_id,
                campaign_id=campaign_id,
                status_filter=status
            )

            if not ad_groups:
                return create_error_response(handle_exception(
                    ValueError("No ad groups found with the specified filters."),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "campaign_id": campaign_id, "status": status}
                ))

            # Format with dashes for display
            display_customer_id = format_customer_id(clean_customer_id)

            # Format the results as a text report
            report = [
                f"Google Ads Ad Groups",
                f"Account ID: {display_customer_id}",
                f"Campaign Filter: {campaign_id if campaign_id else 'All Campaigns'}",
                f"Status Filter: {status if status else 'All Statuses'}\n",
                f"{'Ad Group ID':<12} {'Ad Group Name':<30} {'Campaign':<20} {'Status':<10} {'Impressions':<12} {'Clicks':<8} {'Cost':<10}",
                "-" * 100
            ]

            # Add data rows
            for ad_group in sorted(ad_groups, key=lambda x: x.get("cost", 0), reverse=True):
                name = ad_group["name"]
                if len(name) > 27:
                    name = name[:24] + "..."

                campaign_name = ad_group.get("campaign_name", "Unknown")
                if len(campaign_name) > 17:
                    campaign_name = campaign_name[:14] + "..."

                report.append(
                    f"{ad_group['id']:<12} {name:<30} {campaign_name:<20} {ad_group['status']:<10} "
                    f"{int(ad_group.get('impressions', 0)):,d} {int(ad_group.get('clicks', 0)):,d} "
                    f"${ad_group.get('cost', 0):,.2f}"
                )

            return "\n".join(report)

        except Exception as e:
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "campaign_id": campaign_id, "status": status}
            )
            logger.error(f"Error getting ad groups: {str(e)}")
            return create_error_response(error_details)

    @mcp.tool()
    async def get_ad_groups_json(customer_id: str, campaign_id: str = None, status: str = None):
        """
        Get ad groups in JSON format for visualization.

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            campaign_id: Optional campaign ID to filter by
            status: Optional status filter (ENABLED, PAUSED, REMOVED)

        Returns:
            JSON data for ad group visualization
        """
        try:
            # Validate inputs
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            if campaign_id and not validate_string_length(campaign_id, min_length=1):
                input_errors.append(f"Invalid campaign_id: {campaign_id}.")

            if status and not validate_enum(status, ["ENABLED", "PAUSED", "REMOVED", "UNKNOWN"], case_sensitive=False):
                input_errors.append(f"Invalid status: {status}. Expected one of: ENABLED, PAUSED, REMOVED, UNKNOWN.")

            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_ad_groups_json: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "campaign_id": campaign_id, "status": status}
                ))

            # Remove dashes from customer ID if present
            clean_customer_id = customer_id.replace('-', '')

            logger.info(f"Getting ad groups JSON for customer ID {clean_customer_id}")

            # Get ad groups using the AdGroupService
            ad_groups = await ad_group_service.get_ad_groups(
                customer_id=clean_customer_id,
                campaign_id=campaign_id,
                status_filter=status
            )

            if not ad_groups:
                return create_error_response(handle_exception(
                    ValueError("No ad groups found with the specified filters."),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "campaign_id": campaign_id, "status": status}
                ))

            # Format for visualization
            visualization_data = format_for_visualization(
                ad_groups,
                chart_type="bar",
                metrics=["impressions", "clicks", "cost"]
            )

            return {
                "type": "success",
                "data": ad_groups,
                "visualization": visualization_data
            }

        except Exception as e:
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "campaign_id": campaign_id, "status": status}
            )
            logger.error(f"Error getting ad groups JSON: {str(e)}")
            return create_error_response(error_details)

    @mcp.tool()
    async def get_ad_group_performance(customer_id: str, ad_group_id: str, start_date: str = None, end_date: str = None):
        """
        Get performance metrics for a specific ad group.

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            ad_group_id: Ad group ID
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)

        Returns:
            Formatted performance report for the ad group
        """
        try:
            # Validate inputs
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            if not validate_string_length(ad_group_id, min_length=1):
                input_errors.append("Ad group ID is required.")

            if start_date and not validate_date_format(start_date):
                input_errors.append(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD.")

            if end_date and not validate_date_format(end_date):
                input_errors.append(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD.")

            # Check date order
            if start_date and end_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                if start_dt > end_dt:
                    input_errors.append(f"start_date ({start_date}) must be before end_date ({end_date}).")

            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_ad_group_performance: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "ad_group_id": ad_group_id, "start_date": start_date, "end_date": end_date}
                ))

            # Remove dashes from customer ID if present
            clean_customer_id = customer_id.replace('-', '')

            logger.info(f"Getting performance for ad group {ad_group_id}")

            # Get performance data using the AdGroupService
            performance = await ad_group_service.get_ad_group_performance(
                customer_id=clean_customer_id,
                ad_group_id=ad_group_id,
                start_date=start_date,
                end_date=end_date
            )

            # Format with dashes for display
            display_customer_id = format_customer_id(clean_customer_id)

            # Format the results as a text report
            report = [
                f"Google Ads Ad Group Performance Report",
                f"Account ID: {display_customer_id}",
                f"Ad Group ID: {ad_group_id}",
                f"Date Range: {performance['start_date']} to {performance['end_date']}\n",
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
                context={"customer_id": customer_id, "ad_group_id": ad_group_id, "start_date": start_date, "end_date": end_date}
            )
            logger.error(f"Error getting ad group performance: {str(e)}")
            return create_error_response(error_details)

    @mcp.tool()
    async def get_ad_group_performance_json(customer_id: str, ad_group_id: str, start_date: str = None, end_date: str = None):
        """
        Get performance metrics for a specific ad group in JSON format for visualization.

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            ad_group_id: Ad group ID
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)

        Returns:
            JSON data for ad group performance visualization
        """
        try:
            # Validate inputs
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            if not validate_string_length(ad_group_id, min_length=1):
                input_errors.append("Ad group ID is required.")

            if start_date and not validate_date_format(start_date):
                input_errors.append(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD.")

            if end_date and not validate_date_format(end_date):
                input_errors.append(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD.")

            # Check date order
            if start_date and end_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                if start_dt > end_dt:
                    input_errors.append(f"start_date ({start_date}) must be before end_date ({end_date}).")

            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_ad_group_performance_json: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "ad_group_id": ad_group_id, "start_date": start_date, "end_date": end_date}
                ))

            # Remove dashes from customer ID if present
            clean_customer_id = customer_id.replace('-', '')

            logger.info(f"Getting performance JSON for ad group {ad_group_id}")

            # Get performance data using the AdGroupService
            performance = await ad_group_service.get_ad_group_performance(
                customer_id=clean_customer_id,
                ad_group_id=ad_group_id,
                start_date=start_date,
                end_date=end_date
            )

            # Format for visualization
            visualization_data = format_for_visualization(
                performance['daily_stats'],
                chart_type="time_series",
                metrics=["impressions", "clicks", "cost", "conversions", "conversion_value"]
            )

            return {
                "type": "success",
                "data": performance,
                "visualization": visualization_data
            }

        except Exception as e:
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "ad_group_id": ad_group_id, "start_date": start_date, "end_date": end_date}
            )
            logger.error(f"Error getting ad group performance JSON: {str(e)}")
            return create_error_response(error_details)

    # Related: mcp.tools.keyword.add_keywords (After creating an ad group, you may want to add keywords)
    @mcp.tool()
    async def create_ad_group(customer_id: str, campaign_id: str, name: str, status: str = "ENABLED", cpc_bid_micros: int = None):
        """
        Create a new ad group within a campaign.

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            campaign_id: Campaign ID to create the ad group in
            name: Name of the ad group
            status: Ad group status (ENABLED, PAUSED, REMOVED)
            cpc_bid_micros: CPC bid amount in micros (1/1,000,000 of the account currency)

        Returns:
            Success message with the created ad group details
        """
        try:
            # Validate inputs
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            if not validate_string_length(campaign_id, min_length=1):
                input_errors.append("Campaign ID is required.")

            if not validate_string_length(name, min_length=1, max_length=255):
                input_errors.append("Ad group name is required and must be between 1-255 characters.")

            if not validate_enum(status, ["ENABLED", "PAUSED", "REMOVED"], case_sensitive=True):
                input_errors.append(f"Invalid status: {status}. Must be one of: ENABLED, PAUSED, REMOVED.")

            if cpc_bid_micros is not None and not validate_numeric_range(cpc_bid_micros, min_value=0):
                input_errors.append(f"Invalid CPC bid: {cpc_bid_micros}. Must be a non-negative integer.")

            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in create_ad_group: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "campaign_id": campaign_id, "name": name, "status": status}
                ))

            # Remove dashes from customer ID if present
            clean_customer_id = customer_id.replace('-', '')

            logger.info(f"Creating ad group '{name}' in campaign {campaign_id}")

            # Create ad group using the AdGroupService
            result = await ad_group_service.create_ad_group(
                customer_id=clean_customer_id,
                campaign_id=campaign_id,
                name=name,
                status=status,
                cpc_bid_micros=cpc_bid_micros
            )

            # Format the response
            response = [
                f"✅ Ad Group created successfully",
                f"Ad Group ID: {result['ad_group_id']}",
                f"Name: {name}",
                f"Campaign ID: {campaign_id}",
                f"Status: {status}"
            ]

            if cpc_bid_micros:
                cpc_bid_dollars = cpc_bid_micros / 1000000
                response.append(f"CPC Bid: ${cpc_bid_dollars:.2f}")

            return "\n".join(response)

        except Exception as e:
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "campaign_id": campaign_id, "name": name, "status": status}
            )
            logger.error(f"Error creating ad group: {str(e)}")
            return create_error_response(error_details)

    @mcp.tool()
    async def update_ad_group(customer_id: str, ad_group_id: str, name: str = None, status: str = None, cpc_bid_micros: int = None):
        """
        Update an existing ad group's attributes.

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            ad_group_id: Ad group ID to update
            name: New name for the ad group (optional)
            status: New status for the ad group (optional, one of: ENABLED, PAUSED, REMOVED)
            cpc_bid_micros: New CPC bid amount in micros (optional)

        Returns:
            Success message with the updated ad group details
        """
        try:
            # Validate inputs
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            if not validate_string_length(ad_group_id, min_length=1):
                input_errors.append("Ad group ID is required.")

            if name is not None and not validate_string_length(name, min_length=1, max_length=255):
                input_errors.append("Ad group name must be between 1-255 characters.")

            if status is not None and not validate_enum(status, ["ENABLED", "PAUSED", "REMOVED"], case_sensitive=True):
                input_errors.append(f"Invalid status: {status}. Must be one of: ENABLED, PAUSED, REMOVED.")

            if cpc_bid_micros is not None and not validate_numeric_range(cpc_bid_micros, min_value=0):
                input_errors.append(f"Invalid CPC bid: {cpc_bid_micros}. Must be a non-negative integer.")

            # Ensure at least one field is being updated
            if not any([name, status, cpc_bid_micros]):
                input_errors.append("At least one of name, status, or cpc_bid_micros must be provided")

            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in update_ad_group: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "ad_group_id": ad_group_id, "name": name, "status": status}
                ))

            # Remove dashes from customer ID if present
            clean_customer_id = customer_id.replace('-', '')

            logger.info(f"Updating ad group {ad_group_id}")

            # Update ad group using the AdGroupService
            result = await ad_group_service.update_ad_group(
                customer_id=clean_customer_id,
                ad_group_id=ad_group_id,
                name=name,
                status=status,
                cpc_bid_micros=cpc_bid_micros
            )

            # Format the response
            response = [
                f"✅ Ad Group updated successfully",
                f"Ad Group ID: {ad_group_id}"
            ]

            if name:
                response.append(f"New Name: {name}")
            if status:
                response.append(f"New Status: {status}")
            if cpc_bid_micros:
                cpc_bid_dollars = cpc_bid_micros / 1000000
                response.append(f"New CPC Bid: ${cpc_bid_dollars:.2f}")

            return "\n".join(response)

        except Exception as e:
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "ad_group_id": ad_group_id, "name": name, "status": status}
            )
            logger.error(f"Error updating ad group: {str(e)}")
            return create_error_response(error_details)


# Backwards compatibility stubs
async def get_ad_groups(*args, **kwargs):
    raise NotImplementedError("get_ad_groups is not implemented in this version")
