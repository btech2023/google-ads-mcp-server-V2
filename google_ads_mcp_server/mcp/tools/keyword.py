"""
Keyword Tools Module

This module contains keyword-related MCP tools.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from visualization.formatters import format_for_visualization
from visualization.keywords import format_keyword_comparison_table, format_keyword_status_distribution, format_keyword_performance_metrics

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

def register_keyword_tools(mcp, google_ads_service, keyword_service) -> None:
    """
    Register keyword-related MCP tools.

    Args:
        mcp: The MCP server instance
        google_ads_service: The Google Ads service instance
        keyword_service: The keyword service instance
    """
    # Related: mcp.tools.ad_group.get_ad_groups (Keywords belong to ad groups)
    @mcp.tool()
    async def get_keywords(customer_id: str, ad_group_id: str = None, status: str = None, start_date: str = None, end_date: str = None):
        """
        Get keywords for a Google Ads account with optional filtering.

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            ad_group_id: Optional ad group ID to filter by
            status: Optional status filter (ENABLED, PAUSED, REMOVED)
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)

        Returns:
            Formatted list of keywords
        """
        try:
            # Validate inputs
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            if ad_group_id and not validate_string_length(ad_group_id, min_length=1):
                input_errors.append(f"Invalid ad_group_id: {ad_group_id}.")

            if status and not validate_enum(status, ["ENABLED", "PAUSED", "REMOVED", "UNKNOWN"], case_sensitive=False):
                input_errors.append(f"Invalid status: {status}. Expected one of: ENABLED, PAUSED, REMOVED, UNKNOWN.")

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
                logger.warning(f"Validation error in get_keywords: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "ad_group_id": ad_group_id, "status": status, "start_date": start_date, "end_date": end_date}
                ))

            # Remove dashes from customer ID if present
            clean_customer_id = customer_id.replace('-', '')

            logger.info(f"Getting keywords for customer ID {clean_customer_id}")

            # Get keywords using the KeywordService
            keywords = await keyword_service.get_keywords(
                customer_id=clean_customer_id,
                ad_group_id=ad_group_id,
                status_filter=status,
                start_date=start_date,
                end_date=end_date
            )

            if not keywords:
                return create_error_response(handle_exception(
                    ValueError("No keywords found with the specified filters."),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "ad_group_id": ad_group_id, "status": status}
                ))

            # Format with dashes for display
            display_customer_id = format_customer_id(clean_customer_id)

            # Format the results as a text report
            report = [
                f"Google Ads Keywords",
                f"Account ID: {display_customer_id}",
                f"Ad Group Filter: {ad_group_id if ad_group_id else 'All Ad Groups'}",
                f"Status Filter: {status if status else 'All'}",
                f"Date Range: {start_date or 'Last 30 days'} to {end_date or 'Today'}\n",
                f"{'Keyword':<35} {'Match Type':<12} {'Status':<10} {'Ad Group':<25} {'Impressions':<12} {'Clicks':<8} {'CTR':<6} {'Avg CPC':<10} {'Cost':<10} {'Conv.':<8}",
                "-" * 140
            ]

            # Add data rows
            for kw in sorted(keywords, key=lambda x: (x.get("ad_group_name", ""), x.get("text", "")), reverse=False):
                keyword_text = kw.get("text", "")
                if len(keyword_text) > 32:
                    keyword_text = keyword_text[:29] + "..."

                ad_group_name = kw.get("ad_group_name", "")
                if len(ad_group_name) > 22:
                    ad_group_name = ad_group_name[:19] + "..."

                report.append(
                    f"{keyword_text:<35} {kw.get('match_type', ''):<12} {kw.get('status', ''):<10} "
                    f"{ad_group_name:<25} {int(kw.get('impressions', 0)):,d} {int(kw.get('clicks', 0)):,d} "
                    f"{kw.get('ctr', 0):.2f}% ${kw.get('cpc', 0):,.2f} ${kw.get('cost', 0):,.2f} "
                    f"{kw.get('conversions', 0):.1f}"
                )

            return "\n".join(report)

        except Exception as e:
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "ad_group_id": ad_group_id, "status": status, "start_date": start_date, "end_date": end_date}
            )
            logger.error(f"Error getting keywords: {str(e)}")
            return create_error_response(error_details)

    # Related: mcp.tools.ad_group.get_ad_groups_json (Keywords belong to ad groups)
    @mcp.tool()
    async def get_keywords_json(customer_id: str, ad_group_id: str = None, status: str = None, start_date: str = None, end_date: str = None):
        """
        Get keywords in JSON format for visualization.

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            ad_group_id: Optional ad group ID to filter by
            status: Optional status filter (ENABLED, PAUSED, REMOVED)
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)

        Returns:
            JSON data for keyword visualization
        """
        try:
            # Validate inputs
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            if ad_group_id and not validate_string_length(ad_group_id, min_length=1):
                input_errors.append(f"Invalid ad_group_id: {ad_group_id}.")

            if status and not validate_enum(status, ["ENABLED", "PAUSED", "REMOVED", "UNKNOWN"], case_sensitive=False):
                input_errors.append(f"Invalid status: {status}. Expected one of: ENABLED, PAUSED, REMOVED, UNKNOWN.")

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
                logger.warning(f"Validation error in get_keywords_json: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "ad_group_id": ad_group_id, "status": status, "start_date": start_date, "end_date": end_date}
                ))

            # Remove dashes from customer ID if present
            clean_customer_id = customer_id.replace('-', '')

            logger.info(f"Getting keywords JSON for customer ID {clean_customer_id}")

            # Get keywords using the KeywordService
            keywords = await keyword_service.get_keywords(
                customer_id=clean_customer_id,
                ad_group_id=ad_group_id,
                status_filter=status,
                start_date=start_date,
                end_date=end_date
            )

            if not keywords:
                return create_error_response(handle_exception(
                    ValueError("No keywords found with the specified filters."),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "ad_group_id": ad_group_id, "status": status}
                ))

            # Format data for visualization
            performance_data = format_keyword_performance_metrics(keywords)
            status_distribution = format_keyword_status_distribution(keywords)
            keyword_table = format_keyword_comparison_table(keywords)

            return {
                "type": "success",
                "data": keywords,
                "visualizations": [
                    performance_data,
                    status_distribution,
                    keyword_table
                ],
                "total_keywords": len(keywords)
            }

        except Exception as e:
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "ad_group_id": ad_group_id, "status": status, "start_date": start_date, "end_date": end_date}
            )
            logger.error(f"Error getting keywords JSON: {str(e)}")
            return create_error_response(error_details)

    # Related: mcp.tools.search_term.get_search_terms_report (Keywords trigger Search Terms)
    @mcp.tool()
    async def add_keywords(customer_id: str, ad_group_id: str, keyword_text: str, match_type: str = "BROAD", status: str = "ENABLED", cpc_bid_micros: int = None):
        """
        Add a new keyword to an ad group.

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            ad_group_id: Ad group ID to add keywords to
            keyword_text: The keyword text to add
            match_type: Keyword match type (BROAD, PHRASE, EXACT)
            status: Keyword status (ENABLED, PAUSED)
            cpc_bid_micros: Optional CPC bid in micros (1/1,000,000 of account currency)

        Returns:
            Success message with the created keyword details
        """
        try:
            # Validate inputs
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            if not validate_string_length(ad_group_id, min_length=1):
                input_errors.append("Ad group ID is required.")

            if not validate_string_length(keyword_text, min_length=1):
                input_errors.append("Keyword text is required.")

            if not validate_enum(match_type, ["BROAD", "PHRASE", "EXACT"], case_sensitive=True):
                input_errors.append(f"Invalid match_type: {match_type}. Must be one of: BROAD, PHRASE, EXACT.")

            if not validate_enum(status, ["ENABLED", "PAUSED"], case_sensitive=True):
                input_errors.append(f"Invalid status: {status}. Must be one of: ENABLED, PAUSED.")

            if cpc_bid_micros is not None and not validate_numeric_range(cpc_bid_micros, min_value=0):
                input_errors.append(f"Invalid CPC bid: {cpc_bid_micros}. Must be a non-negative integer.")

            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in add_keywords: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "ad_group_id": ad_group_id, "keyword_text": keyword_text, "match_type": match_type, "status": status}
                ))

            # Remove dashes from customer ID if present
            clean_customer_id = customer_id.replace('-', '')

            logger.info(f"Adding keyword '{keyword_text}' to ad group {ad_group_id}")

            # Format the keyword for the service
            keyword = {
                "text": keyword_text,
                "match_type": match_type,
                "status": status
            }

            if cpc_bid_micros:
                keyword["cpc_bid_micros"] = cpc_bid_micros

            # Add the keyword using the KeywordService
            result = await keyword_service.add_keywords(
                customer_id=clean_customer_id,
                ad_group_id=ad_group_id,
                keywords=[keyword]
            )

            # Format the response
            cpc_bid_dollars = cpc_bid_micros / 1000000 if cpc_bid_micros else None

            response = [
                f"✅ Keyword added successfully",
                f"Keyword: {keyword_text}",
                f"Match Type: {match_type}",
                f"Ad Group ID: {ad_group_id}",
                f"Status: {status}"
            ]

            if cpc_bid_dollars:
                response.append(f"CPC Bid: ${cpc_bid_dollars:.2f}")

            if "keyword_id" in result:
                response.append(f"Keyword ID: {result['keyword_id']}")

            return "\n".join(response)

        except Exception as e:
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "ad_group_id": ad_group_id, "keyword_text": keyword_text, "match_type": match_type, "status": status}
            )
            logger.error(f"Error adding keyword: {str(e)}")
            return create_error_response(error_details)

    @mcp.tool()
    async def update_keyword(customer_id: str, keyword_id: str, status: str = None, cpc_bid_micros: int = None):
        """
        Update an existing keyword's status or bid.

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            keyword_id: Keyword criterion ID to update
            status: Optional new status (ENABLED, PAUSED, REMOVED)
            cpc_bid_micros: Optional new CPC bid in micros (1/1,000,000 of account currency)

        Returns:
            Success message with the updated keyword details
        """
        try:
            # Validate inputs
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            if not validate_string_length(keyword_id, min_length=1):
                input_errors.append("Keyword ID is required.")

            if status is not None and not validate_enum(status, ["ENABLED", "PAUSED", "REMOVED"], case_sensitive=True):
                input_errors.append(f"Invalid status: {status}. Must be one of: ENABLED, PAUSED, REMOVED.")

            if cpc_bid_micros is not None and not validate_numeric_range(cpc_bid_micros, min_value=0):
                input_errors.append(f"Invalid CPC bid: {cpc_bid_micros}. Must be a non-negative integer.")

            # Ensure at least one update field is provided
            if status is None and cpc_bid_micros is None:
                input_errors.append("You must provide at least one field to update (status or cpc_bid_micros).")

            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in update_keyword: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "keyword_id": keyword_id, "status": status, "cpc_bid_micros": cpc_bid_micros}
                ))

            # Remove dashes from customer ID if present
            clean_customer_id = customer_id.replace('-', '')

            logger.info(f"Updating keyword {keyword_id} for customer ID {clean_customer_id}")

            # Prepare update fields
            update_fields = {}
            if status:
                update_fields["status"] = status
            if cpc_bid_micros is not None:
                update_fields["cpc_bid_micros"] = cpc_bid_micros

            # Update the keyword using the KeywordService
            result = await keyword_service.update_keywords(
                customer_id=clean_customer_id,
                keyword_updates=[{"id": keyword_id, **update_fields}]
            )

            # Format the response
            cpc_bid_dollars = cpc_bid_micros / 1000000 if cpc_bid_micros else None

            response = [
                f"✅ Keyword updated successfully",
                f"Keyword ID: {keyword_id}"
            ]

            if status:
                response.append(f"New Status: {status}")

            if cpc_bid_dollars:
                response.append(f"New CPC Bid: ${cpc_bid_dollars:.2f}")

            return "\n".join(response)

        except Exception as e:
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "keyword_id": keyword_id, "status": status, "cpc_bid_micros": cpc_bid_micros}
            )
            logger.error(f"Error updating keyword: {str(e)}")
            return create_error_response(error_details)

    @mcp.tool()
    async def remove_keywords(customer_id: str, keyword_ids: str):
        """
        Remove keywords (set status to REMOVED).

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            keyword_ids: Comma-separated list of keyword criterion IDs to remove

        Returns:
            Success message with the removed keyword IDs
        """
        try:
            # Validate inputs
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            if not validate_string_length(keyword_ids, min_length=1):
                input_errors.append("Keyword IDs list is required.")

            # Parse keyword IDs
            keyword_id_list = [kid.strip() for kid in keyword_ids.split(",")]

            if not keyword_id_list:
                input_errors.append("No valid keyword IDs provided.")

            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in remove_keywords: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "keyword_ids": keyword_ids}
                ))

            # Remove dashes from customer ID if present
            clean_customer_id = customer_id.replace('-', '')

            logger.info(f"Removing {len(keyword_id_list)} keywords for customer ID {clean_customer_id}")

            # Remove keywords using the KeywordService
            result = await keyword_service.remove_keywords(
                customer_id=clean_customer_id,
                keyword_ids=keyword_id_list
            )

            # Format the response
            response = [
                f"✅ Keywords removed successfully",
                f"Removed {len(keyword_id_list)} keywords: {keyword_ids}"
            ]

            return "\n".join(response)

        except Exception as e:
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "keyword_ids": keyword_ids}
            )
            logger.error(f"Error removing keywords: {str(e)}")
            return create_error_response(error_details)
