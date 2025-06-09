"""
Search Term Tools Module

This module contains search term-related MCP tools.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from google_ads_mcp_server.utils.logging import get_logger
from google_ads_mcp_server.utils.validation import (
    validate_customer_id,
    validate_date_format,
    validate_date_range,
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
from visualization.search_terms import format_search_term_table, format_search_term_word_cloud, format_search_term_analysis

# Replace standard logger with utils-provided logger
logger = get_logger(__name__)

def register_search_term_tools(mcp, google_ads_service, search_term_service) -> None:
    """
    Register search term-related MCP tools.

    Args:
        mcp: The MCP server instance
        google_ads_service: The Google Ads service instance
        search_term_service: The search term service instance
    """
    # Related: mcp.tools.keyword.get_keywords (Search terms are triggered by keywords)
    @mcp.tool()
    async def get_search_terms_report(customer_id: str, campaign_id: str = None, ad_group_id: str = None, start_date: str = None, end_date: str = None):
        """
        View search terms that triggered your ads.

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            campaign_id: Optional campaign ID to filter by
            ad_group_id: Optional ad group ID to filter by
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)

        Returns:
            Formatted search terms report
        """
        try:
            # Validate inputs
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            if campaign_id and not validate_string_length(campaign_id, min_length=1):
                input_errors.append(f"Invalid campaign_id: {campaign_id}. Must be a non-empty string.")

            if ad_group_id and not validate_string_length(ad_group_id, min_length=1):
                input_errors.append(f"Invalid ad_group_id: {ad_group_id}. Must be a non-empty string.")

            if start_date and not validate_date_format(start_date):
                input_errors.append(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD.")

            if end_date and not validate_date_format(end_date):
                input_errors.append(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD.")

            # Check date order
            if start_date and end_date and not validate_date_range(start_date, end_date):
                input_errors.append(f"start_date ({start_date}) must be before or equal to end_date ({end_date}).")

            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_search_terms_report: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "campaign_id": campaign_id, "ad_group_id": ad_group_id, "start_date": start_date, "end_date": end_date}
                ))

            # Clean customer ID using utility function
            clean_cid = clean_customer_id(customer_id)

            logger.info(f"Getting search terms report for customer ID {clean_cid}")

            # Get search terms using the SearchTermService
            search_terms = await search_term_service.get_search_terms(
                customer_id=clean_cid,
                campaign_id=campaign_id,
                ad_group_id=ad_group_id,
                start_date=start_date,
                end_date=end_date
            )

            # Standardize error handling for empty results
            if not search_terms:
                error_msg = "No search terms found with the specified filters."
                logger.info(f"No search terms found for {clean_cid} with filters: campaign={campaign_id}, ad_group={ad_group_id}")
                # Return a user-friendly message for empty results, not an error object
                return error_msg

            # Format display customer ID using utility function
            display_customer_id = format_customer_id(clean_cid)

            # Format the results as a text report
            report = [
                f"Google Ads Search Terms Report",
                f"Account ID: {display_customer_id}",
                f"Campaign Filter: {campaign_id if campaign_id else 'All Campaigns'}",
                f"Ad Group Filter: {ad_group_id if ad_group_id else 'All Ad Groups'}",
                f"Date Range: {start_date or 'Last 30 days'} to {end_date or 'Today'}\n",
                f"{'Search Term':<30} {'Matched Keyword':<25} {'Match Type':<12} {'Impr.':<10} {'Clicks':<8} {'CTR':<6} {'Avg CPC':<10} {'Cost':<10} {'Conv.':<8}",
                "-" * 125
            ]

            # Add data rows
            for term in sorted(search_terms, key=lambda x: x.get("cost", 0), reverse=True):
                search_term = term.get("query", "")
                if len(search_term) > 27:
                    search_term = search_term[:24] + "..."

                keyword = term.get("keyword_text", "")
                if len(keyword) > 22:
                    keyword = keyword[:19] + "..."

                # Safely format numbers and currency
                impressions_str = f"{int(term.get('impressions', 0)):,d}" if term.get('impressions') is not None else "0"
                clicks_str = f"{int(term.get('clicks', 0)):,d}" if term.get('clicks') is not None else "0"
                ctr_str = f"{term.get('ctr', 0):.2f}%" if term.get('ctr') is not None else "0.00%"
                cpc_str = f"${term.get('cpc', 0):,.2f}" if term.get('cpc') is not None else "$0.00"
                cost_str = f"${term.get('cost', 0):,.2f}" if term.get('cost') is not None else "$0.00"
                conv_str = f"{term.get('conversions', 0):.1f}" if term.get('conversions') is not None else "0.0"

                report.append(
                    f"{search_term:<30} {keyword:<25} {term.get('match_type', ''):<12} "
                    f"{impressions_str:<10} {clicks_str:<8} {ctr_str:<6} {cpc_str:<10} {cost_str:<10} {conv_str:<8}"
                )

            return "\n".join(report)

        except Exception as e:
            # Standardize exception handling
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "campaign_id": campaign_id, "ad_group_id": ad_group_id, "start_date": start_date, "end_date": end_date}
            )
            logger.error(f"Error getting search terms report: {str(e)}")
            return create_error_response(error_details)

    # Related: mcp.tools.keyword.get_keywords_json (Search terms are triggered by keywords)
    @mcp.tool()
    async def get_search_terms_report_json(customer_id: str, campaign_id: str = None, ad_group_id: str = None, start_date: str = None, end_date: str = None):
        """
        Get search terms in JSON format for visualization.

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            campaign_id: Optional campaign ID to filter by
            ad_group_id: Optional ad group ID to filter by
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)

        Returns:
            JSON data for search terms visualization
        """
        try:
            # Validate inputs (same as get_search_terms_report)
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            if campaign_id and not validate_string_length(campaign_id, min_length=1):
                input_errors.append(f"Invalid campaign_id: {campaign_id}.")

            if ad_group_id and not validate_string_length(ad_group_id, min_length=1):
                input_errors.append(f"Invalid ad_group_id: {ad_group_id}.")

            if start_date and not validate_date_format(start_date):
                input_errors.append(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD.")

            if end_date and not validate_date_format(end_date):
                input_errors.append(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD.")

            if start_date and end_date and not validate_date_range(start_date, end_date):
                input_errors.append(f"start_date ({start_date}) must be before or equal to end_date ({end_date}).")

            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_search_terms_report_json: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "campaign_id": campaign_id, "ad_group_id": ad_group_id, "start_date": start_date, "end_date": end_date}
                ))

            # Clean customer ID using utility function
            clean_cid = clean_customer_id(customer_id)

            logger.info(f"Getting search terms report JSON for customer ID {clean_cid}")

            # Get search terms using the SearchTermService
            search_terms = await search_term_service.get_search_terms(
                customer_id=clean_cid,
                campaign_id=campaign_id,
                ad_group_id=ad_group_id,
                start_date=start_date,
                end_date=end_date
            )

            # Standardize error handling for empty results
            if not search_terms:
                error_msg = "No search terms found with the specified filters."
                logger.info(f"No search terms found for {clean_cid} with filters: campaign={campaign_id}, ad_group={ad_group_id}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "campaign_id": campaign_id, "ad_group_id": ad_group_id}
                ))

            # Format for visualization (using more specific visualization functions)
            visualization_table = format_search_term_table(search_terms, title="Search Terms Report")
            visualization_cloud = format_search_term_word_cloud(search_terms, title="Search Term Word Cloud")

            return {
                "type": "success",
                "data": search_terms,
                # Provide multiple visualization options
                "visualizations": [
                    visualization_table,
                    visualization_cloud
                ],
                "total_search_terms": len(search_terms)
            }

        except Exception as e:
            # Standardize exception handling
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "campaign_id": campaign_id, "ad_group_id": ad_group_id, "start_date": start_date, "end_date": end_date}
            )
            logger.error(f"Error getting search terms report JSON: {str(e)}")
            return create_error_response(error_details)

    # Related: mcp.tools.keyword.add_keywords (Search term analysis can help with keyword additions)
    @mcp.tool()
    async def analyze_search_terms(customer_id: str, campaign_id: str = None, ad_group_id: str = None, start_date: str = None, end_date: str = None):
        """
        Get insights about your search terms performance.

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            campaign_id: Optional campaign ID to filter by
            ad_group_id: Optional ad group ID to filter by
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)

        Returns:
            Formatted analysis of search terms with insights and recommendations
        """
        try:
            # Validate inputs (same as get_search_terms_report)
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            if campaign_id and not validate_string_length(campaign_id, min_length=1):
                input_errors.append(f"Invalid campaign_id: {campaign_id}.")

            if ad_group_id and not validate_string_length(ad_group_id, min_length=1):
                input_errors.append(f"Invalid ad_group_id: {ad_group_id}.")

            if start_date and not validate_date_format(start_date):
                input_errors.append(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD.")

            if end_date and not validate_date_format(end_date):
                input_errors.append(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD.")

            if start_date and end_date and not validate_date_range(start_date, end_date):
                input_errors.append(f"start_date ({start_date}) must be before or equal to end_date ({end_date}).")

            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in analyze_search_terms: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "campaign_id": campaign_id, "ad_group_id": ad_group_id, "start_date": start_date, "end_date": end_date}
                ))

            # Clean customer ID using utility function
            clean_cid = clean_customer_id(customer_id)

            logger.info(f"Analyzing search terms for customer ID {clean_cid}")

            # Get search terms using the SearchTermService
            search_terms = await search_term_service.get_search_terms(
                customer_id=clean_cid,
                campaign_id=campaign_id,
                ad_group_id=ad_group_id,
                start_date=start_date,
                end_date=end_date
            )

            # Standardize handling for empty results
            if not search_terms:
                error_msg = "No search terms found with the specified filters."
                logger.info(f"No search terms to analyze for {clean_cid} with filters: campaign={campaign_id}, ad_group={ad_group_id}")
                return error_msg # Return message, not error

            # Format display customer ID using utility function
            display_customer_id = format_customer_id(clean_cid)

            # Analyze search terms (simple analysis)
            # Top performing search terms by conversions
            top_by_conv = sorted([t for t in search_terms if t.get("conversions", 0) > 0], key=lambda x: x.get("conversions", 0), reverse=True)[:5]

            # Expensive search terms with no conversions (wasted spend)
            # Define threshold for "expensive" based on average cost or a fixed value
            avg_cost = sum(t.get("cost", 0) for t in search_terms) / len(search_terms) if search_terms else 0
            wasted_spend = [t for t in search_terms if t.get("cost", 0) > max(10, avg_cost / 2) and t.get("conversions", 0) == 0]
            wasted_spend = sorted(wasted_spend, key=lambda x: x.get("cost", 0), reverse=True)[:5]

            # High CTR search terms (consider a minimum impression threshold)
            high_ctr = [t for t in search_terms if t.get("impressions", 0) > 50 and t.get("ctr", 0) > 5.0]
            high_ctr = sorted(high_ctr, key=lambda x: x.get("ctr", 0), reverse=True)[:5]

            # Format the results as a text report
            report = [
                f"Google Ads Search Terms Analysis",
                f"Account ID: {display_customer_id}",
                f"Campaign Filter: {campaign_id if campaign_id else 'All Campaigns'}",
                f"Ad Group Filter: {ad_group_id if ad_group_id else 'All Ad Groups'}",
                f"Date Range: {start_date or 'Last 30 days'} to {end_date or 'Today'}",
                f"Total Search Terms Analyzed: {len(search_terms)}\n",

                f"Top Performing Search Terms by Conversions:",
                "-" * 80
            ]

            if top_by_conv:
                for term in top_by_conv:
                    cost_str = f"${term.get('cost', 0):,.2f}" if term.get('cost') is not None else "$0.00"
                    ctr_str = f"{term.get('ctr', 0):.2f}%" if term.get('ctr') is not None else "0.00%"
                    conv_str = f"{term.get('conversions', 0):.1f}" if term.get('conversions') is not None else "0.0"
                    report.append(f"• {term.get('query', '')} - {conv_str} conv, {cost_str} cost, {ctr_str} CTR")
            else:
                report.append("• No converting search terms found")

            report.append("\nPotentially Wasted Spend (No Conversions):")
            report.append("-" * 80)

            if wasted_spend:
                for term in wasted_spend:
                    cost_str = f"${term.get('cost', 0):,.2f}" if term.get('cost') is not None else "$0.00"
                    clicks_str = f"{int(term.get('clicks', 0))}" if term.get('clicks') is not None else "0"
                    ctr_str = f"{term.get('ctr', 0):.2f}%" if term.get('ctr') is not None else "0.00%"
                    report.append(f"• {term.get('query', '')} - {cost_str} cost, {clicks_str} clicks, {ctr_str} CTR")
            else:
                report.append("• No non-converting search terms with significant spend found")

            report.append("\nHigh CTR Search Terms:")
            report.append("-" * 80)

            if high_ctr:
                for term in high_ctr:
                    ctr_str = f"{term.get('ctr', 0):.2f}%" if term.get('ctr') is not None else "0.00%"
                    impr_str = f"{int(term.get('impressions', 0))}" if term.get('impressions') is not None else "0"
                    clicks_str = f"{int(term.get('clicks', 0))}" if term.get('clicks') is not None else "0"
                    report.append(f"• {term.get('query', '')} - {ctr_str} CTR, {impr_str} impr, {clicks_str} clicks")
            else:
                report.append("• No search terms with high CTR found")

            report.append("\nRecommendations:")
            report.append("-" * 80)

            recommendations = []

            # Add converting search terms as keywords
            if top_by_conv:
                recommendations.append("Consider adding these top converting search terms as exact match keywords:")
                for term in top_by_conv[:3]: recommendations.append(f"• \"{term.get('query', '')}\"")

            # Negative keywords for wasted spend
            if wasted_spend:
                recommendations.append("\nConsider adding these expensive non-converting terms as negative keywords:")
                for term in wasted_spend[:3]: recommendations.append(f"• \"{term.get('query', '')}\"")

            # Budget adjustments based on performance
            # Example: Suggest increasing budget if top performers have low impression share
            # This requires `impression_share` metric, which might not be available by default
            # Placeholder logic:
            if top_by_conv:
                 recommendations.append("\nReview impression share for top converting terms and consider budget increases if necessary.")

            if not recommendations:
                recommendations.append("• No specific recommendations based on current data")

            report.extend(recommendations)

            return "\n".join(report)

        except Exception as e:
            # Standardize exception handling
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "campaign_id": campaign_id, "ad_group_id": ad_group_id, "start_date": start_date, "end_date": end_date}
            )
            logger.error(f"Error analyzing search terms: {str(e)}")
            return create_error_response(error_details)

    # Related: mcp.tools.keyword.analyze_search_terms (Same functionality but for JSON visualization)
    @mcp.tool()
    async def analyze_search_terms_json(customer_id: str, campaign_id: str = None, ad_group_id: str = None, start_date: str = None, end_date: str = None):
        """
        Get insights about your search terms performance in JSON format for visualization.

        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            campaign_id: Optional campaign ID to filter by
            ad_group_id: Optional ad group ID to filter by
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)

        Returns:
            JSON data for search terms analysis visualization
        """
        try:
            # Validate inputs (same as analyze_search_terms)
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            if campaign_id and not validate_string_length(campaign_id, min_length=1):
                input_errors.append(f"Invalid campaign_id: {campaign_id}.")

            if ad_group_id and not validate_string_length(ad_group_id, min_length=1):
                input_errors.append(f"Invalid ad_group_id: {ad_group_id}.")

            if start_date and not validate_date_format(start_date):
                input_errors.append(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD.")

            if end_date and not validate_date_format(end_date):
                input_errors.append(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD.")

            if start_date and end_date and not validate_date_range(start_date, end_date):
                input_errors.append(f"start_date ({start_date}) must be before or equal to end_date ({end_date}).")

            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in analyze_search_terms_json: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "campaign_id": campaign_id, "ad_group_id": ad_group_id, "start_date": start_date, "end_date": end_date}
                ))

            # Clean customer ID using utility function
            clean_cid = clean_customer_id(customer_id)

            logger.info(f"Analyzing search terms JSON for customer ID {clean_cid}")

            # Get search terms using the SearchTermService
            search_terms = await search_term_service.get_search_terms(
                customer_id=clean_cid,
                campaign_id=campaign_id,
                ad_group_id=ad_group_id,
                start_date=start_date,
                end_date=end_date
            )

            # Standardize handling for empty results
            if not search_terms:
                error_msg = "No search terms found with the specified filters."
                logger.info(f"No search terms to analyze for {clean_cid} with filters: campaign={campaign_id}, ad_group={ad_group_id}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "campaign_id": campaign_id, "ad_group_id": ad_group_id}
                ))

            # Analyze search terms (simple analysis - same logic as text version)
            top_by_conv = sorted([t for t in search_terms if t.get("conversions", 0) > 0], key=lambda x: x.get("conversions", 0), reverse=True)[:10]
            avg_cost = sum(t.get("cost", 0) for t in search_terms) / len(search_terms) if search_terms else 0
            wasted_spend = [t for t in search_terms if t.get("cost", 0) > max(10, avg_cost / 2) and t.get("conversions", 0) == 0]
            wasted_spend = sorted(wasted_spend, key=lambda x: x.get("cost", 0), reverse=True)[:10]
            high_ctr = [t for t in search_terms if t.get("impressions", 0) > 50 and t.get("ctr", 0) > 5.0]
            high_ctr = sorted(high_ctr, key=lambda x: x.get("ctr", 0), reverse=True)[:10]

            # Prepare data for visualization using the dedicated visualization formatter
            analysis_visualization = format_search_term_analysis(
                top_converting=top_by_conv,
                wasted_spend=wasted_spend,
                high_ctr=high_ctr
            )

            # Format recommendations for data structure
            recommendations = []
            if top_by_conv: recommendations.append({"title": "Add as keywords", "description": "Consider adding top converting terms as exact match keywords", "terms": [term.get("query", "") for term in top_by_conv[:5]]})
            if wasted_spend: recommendations.append({"title": "Add as negative keywords", "description": "Consider adding expensive non-converting terms as negative keywords", "terms": [term.get("query", "") for term in wasted_spend[:5]]})
            if top_by_conv: recommendations.append({"title": "Review Budget", "description": "Review impression share for top converting terms and consider budget increases", "terms": []}) # Placeholder
            if not recommendations: recommendations.append({"title": "No Specific Actions", "description": "Monitor performance or refine filters for more specific insights.", "terms": []})

            return {
                "type": "success",
                "data": {
                    "total_search_terms": len(search_terms),
                    "top_converting": top_by_conv,
                    "wasted_spend": wasted_spend,
                    "high_ctr": high_ctr,
                    "recommendations": recommendations
                },
                "visualization": analysis_visualization # Use the combined analysis visualization
            }

        except Exception as e:
             # Standardize exception handling
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "campaign_id": campaign_id, "ad_group_id": ad_group_id, "start_date": start_date, "end_date": end_date}
            )
            logger.error(f"Error analyzing search terms JSON: {str(e)}")
            return create_error_response(error_details)
