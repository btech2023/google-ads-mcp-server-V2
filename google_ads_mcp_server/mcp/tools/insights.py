"""
Insights Tools Module

This module contains insights-related MCP tools for anomaly detection, optimization suggestions, 
opportunity discovery, and integrated account insights.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from utils.logging import get_logger
from utils.validation import (
    validate_customer_id, 
    validate_date_format,
    validate_date_range,
    validate_enum,
    validate_numeric_range,
    validate_string_length
)
from utils.error_handler import (
    create_error_response, 
    handle_exception,
    CATEGORY_VALIDATION,
    CATEGORY_API_ERROR,
    SEVERITY_ERROR
)
from utils.formatting import format_customer_id, clean_customer_id

from visualization.formatters import format_for_visualization
from visualization.insights import (
    format_anomalies_visualization,
    format_optimization_suggestions_visualization,
    format_opportunities_visualization,
    format_insights_visualization
)

# Replace standard logger with utils-provided logger
logger = get_logger(__name__)

def register_insights_tools(mcp, google_ads_service, insights_service) -> None:
    """
    Register insights-related MCP tools.
    
    Args:
        mcp: The MCP server instance
        google_ads_service: The Google Ads service instance
        insights_service: The insights service instance
    """
    # Related: mcp.tools.campaign.get_campaign_performance (Anomalies are detected in campaign performance)
    @mcp.tool()
    async def get_performance_anomalies(customer_id: str, entity_type: str = "CAMPAIGN", entity_ids: str = None, 
                                       metrics: str = None, start_date: str = None, end_date: str = None,
                                       comparison_period: str = "PREVIOUS_PERIOD", threshold: float = 2.0):
        """
        Detect significant changes in performance metrics.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            entity_type: Type of entity to analyze (CAMPAIGN, AD_GROUP, KEYWORD)
            entity_ids: Optional comma-separated list of entity IDs to analyze
            metrics: Optional comma-separated list of metrics to analyze (e.g., "clicks,impressions,cost")
            start_date: Start date in YYYY-MM-DD format (defaults to 7 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            comparison_period: Period to compare against (PREVIOUS_PERIOD, SAME_PERIOD_LAST_YEAR)
            threshold: Z-score threshold for anomaly detection (lower values detect more anomalies)
            
        Returns:
            Formatted list of detected anomalies
        """
        try:
            # Validate inputs
            input_errors = []

            # Validate customer_id
            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")
                
            # Validate entity_type
            if not validate_enum(entity_type, ["CAMPAIGN", "AD_GROUP", "KEYWORD"]):
                input_errors.append(f"Invalid entity_type: {entity_type}. Expected one of: CAMPAIGN, AD_GROUP, KEYWORD.")
                
            # Validate comparison_period
            if not validate_enum(comparison_period, ["PREVIOUS_PERIOD", "SAME_PERIOD_LAST_YEAR"]):
                input_errors.append(f"Invalid comparison_period: {comparison_period}. Expected one of: PREVIOUS_PERIOD, SAME_PERIOD_LAST_YEAR.")
                
            # Validate threshold
            if not validate_numeric_range(threshold, min_value=0):
                input_errors.append(f"Invalid threshold: {threshold}. Must be a positive number.")
                
            # Validate dates if provided
            if start_date and not validate_date_format(start_date):
                input_errors.append(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD.")
                
            if end_date and not validate_date_format(end_date):
                input_errors.append(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD.")
                
            if start_date and end_date and not validate_date_range(start_date, end_date):
                input_errors.append(f"Invalid date range: start_date {start_date} must be before or equal to end_date {end_date}.")
                
            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_performance_anomalies: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg), 
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "entity_type": entity_type, "metrics": metrics}
                ))
                
            # Remove dashes from customer ID using utility function
            clean_cid = clean_customer_id(customer_id)
            logger.info(f"Detecting performance anomalies for customer ID {clean_cid}")
            
            # Process entity_ids if provided
            entity_id_list = None
            if entity_ids:
                if not validate_string_length(entity_ids, min_length=1):
                    error_msg = f"Invalid entity_ids: {entity_ids}. Must be a non-empty string."
                    logger.warning(f"Validation error: {error_msg}")
                    return create_error_response(handle_exception(
                        ValueError(error_msg),
                        category=CATEGORY_VALIDATION,
                        context={"customer_id": customer_id, "entity_type": entity_type}
                    ))
                entity_id_list = [eid.strip() for eid in entity_ids.split(",")]
                
            # Process metrics if provided
            metrics_list = None
            if metrics:
                if not validate_string_length(metrics, min_length=1):
                    error_msg = f"Invalid metrics: {metrics}. Must be a non-empty string."
                    logger.warning(f"Validation error: {error_msg}")
                    return create_error_response(handle_exception(
                        ValueError(error_msg),
                        category=CATEGORY_VALIDATION,
                        context={"customer_id": customer_id, "entity_type": entity_type}
                    ))
                metrics_list = [m.strip() for m in metrics.split(",")]
                
            # Get performance anomalies using the InsightsService
            anomalies_data = await insights_service.detect_performance_anomalies(
                customer_id=clean_cid,
                entity_type=entity_type,
                entity_ids=entity_id_list,
                metrics=metrics_list,
                start_date=start_date,
                end_date=end_date,
                comparison_period=comparison_period,
                threshold=threshold
            )
            
            if not anomalies_data or not anomalies_data.get("anomalies"):
                error_msg = "No significant performance anomalies detected with the specified parameters."
                logger.info(f"No anomalies detected for customer {clean_cid}: {error_msg}")
                return error_msg
            
            # Format with dashes for display using utility function
            display_customer_id = format_customer_id(clean_cid)
            
            # Format the results as a text report
            metadata = anomalies_data.get("metadata", {})
            anomalies = anomalies_data.get("anomalies", [])
            
            report = [
                f"Google Ads Performance Anomalies",
                f"Account ID: {display_customer_id}",
                f"Entity Type: {entity_type}",
                f"Date Range: {start_date or 'Last 7 days'} to {end_date or 'Today'}",
                f"Comparison Period: {comparison_period}",
                f"Total Anomalies Detected: {len(anomalies)}\n",
                f"{'Entity Name':<30} {'Metric':<15} {'Current':<12} {'Previous':<12} {'Change':<12} {'Severity':<8}",
                "-" * 95
            ]
            
            # Add data rows
            for anomaly in sorted(anomalies, key=lambda x: abs(x.get("z_score", 0)), reverse=True):
                entity_name = anomaly.get("entity_name", "Unknown")
                if len(entity_name) > 27:
                    entity_name = entity_name[:24] + "..."
                    
                metric = anomaly.get("metric", "")
                current = anomaly.get("value", 0)
                previous = anomaly.get("expected", 0)
                
                # Calculate change percentage
                if previous != 0:
                    change_pct = (current - previous) / abs(previous) * 100
                    change_str = f"{'+' if change_pct >= 0 else ''}{change_pct:.1f}%"
                else:
                    change_str = "N/A"
                
                # Determine severity based on z-score
                z_score = abs(anomaly.get("z_score", 0))
                if z_score > 3.0:
                    severity = "HIGH"
                elif z_score > 2.0:
                    severity = "MEDIUM"
                else:
                    severity = "LOW"
                
                # Format values based on metric type
                if metric in ["cost", "cpc", "cpm"]:
                    current_str = f"${current:.2f}"
                    previous_str = f"${previous:.2f}"
                elif metric in ["ctr", "conversion_rate"]:
                    current_str = f"{current:.2f}%"
                    previous_str = f"{previous:.2f}%"
                else:
                    current_str = f"{current:,}"
                    previous_str = f"{previous:,}"
                
                report.append(
                    f"{entity_name:<30} {metric:<15} {current_str:<12} {previous_str:<12} {change_str:<12} {severity:<8}"
                )
                
            return "\n".join(report)
            
        except Exception as e:
            error_details = handle_exception(
                e,
                context={
                    "customer_id": customer_id, 
                    "entity_type": entity_type, 
                    "entity_ids": entity_ids, 
                    "metrics": metrics,
                    "start_date": start_date,
                    "end_date": end_date,
                    "comparison_period": comparison_period,
                    "threshold": threshold
                }
            )
            logger.error(f"Error detecting performance anomalies: {str(e)}")
            return create_error_response(error_details)
    
    # Related: mcp.tools.campaign.get_campaign_performance_json (Anomalies are detected in campaign performance)
    @mcp.tool()
    async def get_performance_anomalies_json(customer_id: str, entity_type: str = "CAMPAIGN", entity_ids: str = None, 
                                            metrics: str = None, start_date: str = None, end_date: str = None,
                                            comparison_period: str = "PREVIOUS_PERIOD", threshold: float = 2.0):
        """
        Detect significant changes in performance metrics in JSON format for visualization.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            entity_type: Type of entity to analyze (CAMPAIGN, AD_GROUP, KEYWORD)
            entity_ids: Optional comma-separated list of entity IDs to analyze
            metrics: Optional comma-separated list of metrics to analyze (e.g., "clicks,impressions,cost")
            start_date: Start date in YYYY-MM-DD format (defaults to 7 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            comparison_period: Period to compare against (PREVIOUS_PERIOD, SAME_PERIOD_LAST_YEAR)
            threshold: Z-score threshold for anomaly detection (lower values detect more anomalies)
            
        Returns:
            JSON data for performance anomalies visualization
        """
        try:
            # Validate inputs
            input_errors = []

            # Validate customer_id
            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")
                
            # Validate entity_type
            if not validate_enum(entity_type, ["CAMPAIGN", "AD_GROUP", "KEYWORD"]):
                input_errors.append(f"Invalid entity_type: {entity_type}. Expected one of: CAMPAIGN, AD_GROUP, KEYWORD.")
                
            # Validate comparison_period
            if not validate_enum(comparison_period, ["PREVIOUS_PERIOD", "SAME_PERIOD_LAST_YEAR"]):
                input_errors.append(f"Invalid comparison_period: {comparison_period}. Expected one of: PREVIOUS_PERIOD, SAME_PERIOD_LAST_YEAR.")
                
            # Validate threshold
            if not validate_numeric_range(threshold, min_value=0):
                input_errors.append(f"Invalid threshold: {threshold}. Must be a positive number.")
                
            # Validate dates if provided
            if start_date and not validate_date_format(start_date):
                input_errors.append(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD.")
                
            if end_date and not validate_date_format(end_date):
                input_errors.append(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD.")
                
            if start_date and end_date and not validate_date_range(start_date, end_date):
                input_errors.append(f"Invalid date range: start_date {start_date} must be before or equal to end_date {end_date}.")
                
            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_performance_anomalies_json: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg), 
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "entity_type": entity_type, "metrics": metrics}
                ))
                
            # Remove dashes from customer ID using utility function
            clean_cid = clean_customer_id(customer_id)
            logger.info(f"Detecting performance anomalies JSON for customer ID {clean_cid}")
            
            # Process entity_ids if provided
            entity_id_list = None
            if entity_ids:
                if not validate_string_length(entity_ids, min_length=1):
                    error_msg = f"Invalid entity_ids: {entity_ids}. Must be a non-empty string."
                    logger.warning(f"Validation error: {error_msg}")
                    return create_error_response(handle_exception(
                        ValueError(error_msg),
                        category=CATEGORY_VALIDATION,
                        context={"customer_id": customer_id, "entity_type": entity_type}
                    ))
                entity_id_list = [eid.strip() for eid in entity_ids.split(",")]
                
            # Process metrics if provided
            metrics_list = None
            if metrics:
                if not validate_string_length(metrics, min_length=1):
                    error_msg = f"Invalid metrics: {metrics}. Must be a non-empty string."
                    logger.warning(f"Validation error: {error_msg}")
                    return create_error_response(handle_exception(
                        ValueError(error_msg),
                        category=CATEGORY_VALIDATION,
                        context={"customer_id": customer_id, "entity_type": entity_type}
                    ))
                metrics_list = [m.strip() for m in metrics.split(",")]
                
            # Get performance anomalies using the InsightsService
            anomalies_data = await insights_service.detect_performance_anomalies(
                customer_id=clean_cid,
                entity_type=entity_type,
                entity_ids=entity_id_list,
                metrics=metrics_list,
                start_date=start_date,
                end_date=end_date,
                comparison_period=comparison_period,
                threshold=threshold
            )
            
            if not anomalies_data or not anomalies_data.get("anomalies"):
                error_msg = "No significant performance anomalies detected with the specified parameters."
                logger.info(f"No anomalies detected for customer {clean_cid}: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "entity_type": entity_type}
                ))
            
            # Format for visualization
            visualization_data = format_anomalies_visualization(anomalies_data)
            
            return {
                "type": "success",
                "data": anomalies_data,
                "visualization": visualization_data
            }
            
        except Exception as e:
            error_details = handle_exception(
                e,
                context={
                    "customer_id": customer_id, 
                    "entity_type": entity_type, 
                    "entity_ids": entity_ids, 
                    "metrics": metrics,
                    "start_date": start_date,
                    "end_date": end_date,
                    "comparison_period": comparison_period,
                    "threshold": threshold
                }
            )
            logger.error(f"Error detecting performance anomalies JSON: {str(e)}")
            return create_error_response(error_details)
    
    # Related: mcp.tools.budget.get_budgets (Optimization suggestions often include budget adjustments)
    @mcp.tool()
    async def get_optimization_suggestions(customer_id: str, entity_type: str = None, entity_ids: str = None, 
                                          start_date: str = None, end_date: str = None):
        """
        Generate actionable optimization suggestions for an account.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            entity_type: Optional entity type to focus on (CAMPAIGN, AD_GROUP)
            entity_ids: Optional comma-separated list of entity IDs to analyze
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Formatted list of optimization suggestions
        """
        try:
            # Validate inputs
            input_errors = []

            # Validate customer_id
            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")
                
            # Validate entity_type if provided
            if entity_type and not validate_enum(entity_type, ["CAMPAIGN", "AD_GROUP"]):
                input_errors.append(f"Invalid entity_type: {entity_type}. Expected one of: CAMPAIGN, AD_GROUP.")
                
            # Validate dates if provided
            if start_date and not validate_date_format(start_date):
                input_errors.append(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD.")
                
            if end_date and not validate_date_format(end_date):
                input_errors.append(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD.")
                
            if start_date and end_date and not validate_date_range(start_date, end_date):
                input_errors.append(f"Invalid date range: start_date {start_date} must be before or equal to end_date {end_date}.")
                
            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_optimization_suggestions: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg), 
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "entity_type": entity_type, "entity_ids": entity_ids}
                ))
                
            # Remove dashes from customer ID using utility function
            clean_cid = clean_customer_id(customer_id)
            logger.info(f"Generating optimization suggestions for customer ID {clean_cid}")
            
            # Process entity_ids if provided
            entity_id_list = None
            if entity_ids:
                if not validate_string_length(entity_ids, min_length=1):
                    error_msg = f"Invalid entity_ids: {entity_ids}. Must be a non-empty string."
                    logger.warning(f"Validation error: {error_msg}")
                    return create_error_response(handle_exception(
                        ValueError(error_msg),
                        category=CATEGORY_VALIDATION,
                        context={"customer_id": customer_id, "entity_type": entity_type}
                    ))
                entity_id_list = [eid.strip() for eid in entity_ids.split(",")]
                
            # Get optimization suggestions using the InsightsService
            suggestions_data = await insights_service.generate_optimization_suggestions(
                customer_id=clean_cid,
                entity_type=entity_type,
                entity_ids=entity_id_list,
                start_date=start_date,
                end_date=end_date
            )
            
            if not suggestions_data or not any(suggestions_data.get(key, []) for key in suggestions_data if key != "metadata"):
                error_msg = "No optimization suggestions found with the specified parameters."
                logger.info(f"No optimization suggestions for customer {clean_cid}: {error_msg}")
                return error_msg
            
            # Format with dashes for display using utility function
            display_customer_id = format_customer_id(clean_cid)
            
            # Format the results as a text report
            metadata = suggestions_data.get("metadata", {})
            
            report = [
                f"Google Ads Optimization Suggestions",
                f"Account ID: {display_customer_id}",
                f"Date Range: {start_date or 'Last 30 days'} to {end_date or 'Today'}",
                f"Total Suggestions: {metadata.get('total_suggestions', 0)}\n"
            ]
            
            # Add suggestion categories
            categories = [
                ("bid_management", "Bid Management Suggestions"),
                ("budget_allocation", "Budget Allocation Suggestions"),
                ("negative_keywords", "Negative Keyword Suggestions"),
                ("ad_copy", "Ad Copy Suggestions"),
                ("account_structure", "Account Structure Suggestions")
            ]
            
            for category_key, category_name in categories:
                suggestions = suggestions_data.get(category_key, [])
                if suggestions:
                    report.append(f"\n{category_name} ({len(suggestions)})")
                    report.append("-" * 50)
                    
                    for suggestion in suggestions:
                        # Extract relevant fields based on category
                        description = suggestion.get("description", "")
                        entity_name = suggestion.get("entity_name", "")
                        impact = suggestion.get("impact", "MEDIUM")
                        
                        # Format entity-specific details
                        if entity_name:
                            entity_info = f" ({entity_name})"
                        else:
                            entity_info = ""
                            
                        # Add impact indicator
                        if impact == "HIGH":
                            impact_indicator = "ðŸ”´"
                        elif impact == "MEDIUM":
                            impact_indicator = "ðŸŸ "
                        else:
                            impact_indicator = "ðŸŸ¢"
                            
                        report.append(f"{impact_indicator} {description}{entity_info}")
            
            return "\n".join(report)
            
        except Exception as e:
            error_details = handle_exception(
                e,
                context={
                    "customer_id": customer_id, 
                    "entity_type": entity_type, 
                    "entity_ids": entity_ids,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            logger.error(f"Error generating optimization suggestions: {str(e)}")
            return create_error_response(error_details)
    
    # Related: mcp.tools.budget.get_budgets_json (Optimization suggestions often include budget adjustments)
    @mcp.tool()
    async def get_optimization_suggestions_json(customer_id: str, entity_type: str = None, entity_ids: str = None, 
                                               start_date: str = None, end_date: str = None):
        """
        Generate actionable optimization suggestions in JSON format for visualization.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            entity_type: Optional entity type to focus on (CAMPAIGN, AD_GROUP)
            entity_ids: Optional comma-separated list of entity IDs to analyze
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            JSON data for optimization suggestions visualization
        """
        try:
            # Validate inputs
            input_errors = []

            # Validate customer_id
            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")
                
            # Validate entity_type if provided
            if entity_type and not validate_enum(entity_type, ["CAMPAIGN", "AD_GROUP"]):
                input_errors.append(f"Invalid entity_type: {entity_type}. Expected one of: CAMPAIGN, AD_GROUP.")
                
            # Validate dates if provided
            if start_date and not validate_date_format(start_date):
                input_errors.append(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD.")
                
            if end_date and not validate_date_format(end_date):
                input_errors.append(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD.")
                
            if start_date and end_date and not validate_date_range(start_date, end_date):
                input_errors.append(f"Invalid date range: start_date {start_date} must be before or equal to end_date {end_date}.")
                
            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_optimization_suggestions_json: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg), 
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "entity_type": entity_type, "entity_ids": entity_ids}
                ))
                
            # Remove dashes from customer ID using utility function
            clean_cid = clean_customer_id(customer_id)
            logger.info(f"Generating optimization suggestions JSON for customer ID {clean_cid}")
            
            # Process entity_ids if provided
            entity_id_list = None
            if entity_ids:
                if not validate_string_length(entity_ids, min_length=1):
                    error_msg = f"Invalid entity_ids: {entity_ids}. Must be a non-empty string."
                    logger.warning(f"Validation error: {error_msg}")
                    return create_error_response(handle_exception(
                        ValueError(error_msg),
                        category=CATEGORY_VALIDATION,
                        context={"customer_id": customer_id, "entity_type": entity_type}
                    ))
                entity_id_list = [eid.strip() for eid in entity_ids.split(",")]
                
            # Get optimization suggestions using the InsightsService
            suggestions_data = await insights_service.generate_optimization_suggestions(
                customer_id=clean_cid,
                entity_type=entity_type,
                entity_ids=entity_id_list,
                start_date=start_date,
                end_date=end_date
            )
            
            if not suggestions_data or not any(suggestions_data.get(key, []) for key in suggestions_data if key != "metadata"):
                error_msg = "No optimization suggestions found with the specified parameters."
                logger.info(f"No optimization suggestions for customer {clean_cid}: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "entity_type": entity_type}
                ))
            
            # Format for visualization
            visualization_data = format_optimization_suggestions_visualization(suggestions_data)
            
            return {
                "type": "success",
                "data": suggestions_data,
                "visualization": visualization_data
            }
            
        except Exception as e:
            error_details = handle_exception(
                e,
                context={
                    "customer_id": customer_id, 
                    "entity_type": entity_type, 
                    "entity_ids": entity_ids,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            logger.error(f"Error generating optimization suggestions JSON: {str(e)}")
            return create_error_response(error_details)
    
    # Related: mcp.tools.keyword.get_keywords (Opportunities often include keyword suggestions)
    @mcp.tool()
    async def get_opportunities(customer_id: str, opportunity_type: str = None, start_date: str = None, end_date: str = None):
        """
        Discover growth opportunities in a Google Ads account.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            opportunity_type: Optional opportunity type filter (keyword_expansion, bid_adjustment, etc.)
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Formatted list of discovered opportunities
        """
        try:
            # Validate inputs
            input_errors = []

            # Validate customer_id
            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")
                
            # Validate opportunity_type if provided
            valid_opportunity_types = ["keyword_expansion", "bid_adjustment", "budget_increase", 
                                       "audience_expansion", "ad_variation", "structure"]
            if opportunity_type and not validate_enum(opportunity_type, valid_opportunity_types):
                input_errors.append(f"Invalid opportunity_type: {opportunity_type}. Expected one of: {', '.join(valid_opportunity_types)}.")
                
            # Validate dates if provided
            if start_date and not validate_date_format(start_date):
                input_errors.append(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD.")
                
            if end_date and not validate_date_format(end_date):
                input_errors.append(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD.")
                
            if start_date and end_date and not validate_date_range(start_date, end_date):
                input_errors.append(f"Invalid date range: start_date {start_date} must be before or equal to end_date {end_date}.")
                
            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_opportunities: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg), 
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "opportunity_type": opportunity_type}
                ))
                
            # Remove dashes from customer ID using utility function
            clean_cid = clean_customer_id(customer_id)
            logger.info(f"Discovering opportunities for customer ID {clean_cid}")
            
            # Get opportunities using the InsightsService
            opportunities_data = await insights_service.discover_opportunities(
                customer_id=clean_cid,
                opportunity_type=opportunity_type,
                start_date=start_date,
                end_date=end_date
            )
            
            if not opportunities_data or not opportunities_data.get("opportunities"):
                error_msg = "No growth opportunities found with the specified parameters."
                logger.info(f"No opportunities found for customer {clean_cid}: {error_msg}")
                return error_msg
            
            # Format with dashes for display using utility function
            display_customer_id = format_customer_id(clean_cid)
            
            # Format the results as a text report
            metadata = opportunities_data.get("metadata", {})
            opportunities = opportunities_data.get("opportunities", {})
            
            report = [
                f"Google Ads Growth Opportunities",
                f"Account ID: {display_customer_id}",
                f"Date Range: {start_date or 'Last 30 days'} to {end_date or 'Today'}",
                f"Total Opportunities: {metadata.get('total_opportunities', 0)}\n"
            ]
            
            # Add opportunity categories
            categories = [
                ("keyword_expansion", "Keyword Expansion Opportunities"),
                ("bid_adjustment", "Bid Adjustment Opportunities"),
                ("budget_increase", "Budget Increase Opportunities"),
                ("audience_expansion", "Audience Expansion Opportunities"),
                ("ad_variation", "Ad Variation Opportunities"),
                ("structure", "Structure Improvement Opportunities")
            ]
            
            for category_key, category_name in categories:
                category_opportunities = opportunities.get(category_key, [])
                if category_opportunities:
                    report.append(f"\n{category_name} ({len(category_opportunities)})")
                    report.append("-" * 50)
                    
                    for opportunity in category_opportunities:
                        # Extract relevant fields
                        description = opportunity.get("description", "")
                        impact = opportunity.get("impact", "MEDIUM")
                        entity_name = opportunity.get("entity_name", "")
                        
                        # Format entity-specific details
                        if entity_name:
                            entity_info = f" for {entity_name}"
                        else:
                            entity_info = ""
                            
                        # Add impact indicator
                        if impact == "HIGH":
                            impact_indicator = "â­�â­�â­�"
                        elif impact == "MEDIUM":
                            impact_indicator = "â­�â­�"
                        else:
                            impact_indicator = "â­�"
                            
                        report.append(f"{impact_indicator} {description}{entity_info}")
            
            return "\n".join(report)
            
        except Exception as e:
            error_details = handle_exception(
                e,
                context={
                    "customer_id": customer_id, 
                    "opportunity_type": opportunity_type,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            logger.error(f"Error discovering opportunities: {str(e)}")
            return create_error_response(error_details)
    
    # Related: mcp.tools.keyword.get_keywords_json (Opportunities often include keyword suggestions)
    @mcp.tool()
    async def get_opportunities_json(customer_id: str, opportunity_type: str = None, start_date: str = None, end_date: str = None):
        """
        Discover growth opportunities in JSON format for visualization.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            opportunity_type: Optional opportunity type filter (keyword_expansion, bid_adjustment, etc.)
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            JSON data for opportunities visualization
        """
        try:
            # Validate inputs
            input_errors = []

            # Validate customer_id
            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")
                
            # Validate opportunity_type if provided
            valid_opportunity_types = ["keyword_expansion", "bid_adjustment", "budget_increase", 
                                       "audience_expansion", "ad_variation", "structure"]
            if opportunity_type and not validate_enum(opportunity_type, valid_opportunity_types):
                input_errors.append(f"Invalid opportunity_type: {opportunity_type}. Expected one of: {', '.join(valid_opportunity_types)}.")
                
            # Validate dates if provided
            if start_date and not validate_date_format(start_date):
                input_errors.append(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD.")
                
            if end_date and not validate_date_format(end_date):
                input_errors.append(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD.")
                
            if start_date and end_date and not validate_date_range(start_date, end_date):
                input_errors.append(f"Invalid date range: start_date {start_date} must be before or equal to end_date {end_date}.")
                
            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_opportunities_json: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg), 
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "opportunity_type": opportunity_type}
                ))
                
            # Remove dashes from customer ID using utility function
            clean_cid = clean_customer_id(customer_id)
            logger.info(f"Discovering opportunities JSON for customer ID {clean_cid}")
            
            # Get opportunities using the InsightsService
            opportunities_data = await insights_service.discover_opportunities(
                customer_id=clean_cid,
                opportunity_type=opportunity_type,
                start_date=start_date,
                end_date=end_date
            )
            
            if not opportunities_data or not opportunities_data.get("opportunities"):
                error_msg = "No growth opportunities found with the specified parameters."
                logger.info(f"No opportunities found for customer {clean_cid}: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "opportunity_type": opportunity_type}
                ))
            
            # Format for visualization
            visualization_data = format_opportunities_visualization(opportunities_data)
            
            return {
                "type": "success",
                "data": opportunities_data,
                "visualization": visualization_data
            }
            
        except Exception as e:
            error_details = handle_exception(
                e,
                context={
                    "customer_id": customer_id, 
                    "opportunity_type": opportunity_type,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            logger.error(f"Error discovering opportunities JSON: {str(e)}")
            return create_error_response(error_details)
    
    # Related: mcp.tools.dashboard.get_account_dashboard_json (Integrated insights provide a comprehensive view)
    @mcp.tool()
    async def get_account_insights_json(customer_id: str, start_date: str = None, end_date: str = None):
        """
        Get comprehensive account insights combining anomalies, suggestions, and opportunities.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            JSON data for comprehensive account insights visualization
        """
        try:
            # Validate inputs
            input_errors = []

            # Validate customer_id
            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")
                
            # Validate dates if provided
            if start_date and not validate_date_format(start_date):
                input_errors.append(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD.")
                
            if end_date and not validate_date_format(end_date):
                input_errors.append(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD.")
                
            if start_date and end_date and not validate_date_range(start_date, end_date):
                input_errors.append(f"Invalid date range: start_date {start_date} must be before or equal to end_date {end_date}.")
                
            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_account_insights_json: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg), 
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id}
                ))
                
            # Remove dashes from customer ID using utility function
            clean_cid = clean_customer_id(customer_id)
            logger.info(f"Generating comprehensive account insights for customer ID {clean_cid}")
            
            # Get all insights concurrently for efficiency
            import asyncio
            
            try:
                # Get all insights concurrently for efficiency
                anomalies_task = insights_service.detect_performance_anomalies(
                    customer_id=clean_cid,
                    start_date=start_date,
                    end_date=end_date
                )
                
                suggestions_task = insights_service.generate_optimization_suggestions(
                    customer_id=clean_cid,
                    start_date=start_date,
                    end_date=end_date
                )
                
                opportunities_task = insights_service.discover_opportunities(
                    customer_id=clean_cid,
                    start_date=start_date,
                    end_date=end_date
                )
                
                # Wait for all tasks to complete
                anomalies_data, suggestions_data, opportunities_data = await asyncio.gather(
                    anomalies_task, suggestions_task, opportunities_task
                )
                
                # Check if we have data
                if (not anomalies_data or not anomalies_data.get("anomalies")) and \
                   (not suggestions_data or not any(suggestions_data.get(key, []) for key in suggestions_data if key != "metadata")) and \
                   (not opportunities_data or not opportunities_data.get("opportunities")):
                    error_msg = "No insights found with the specified parameters."
                    logger.info(f"No insights found for customer {clean_cid}: {error_msg}")
                    return create_error_response(handle_exception(
                        ValueError(error_msg),
                        category=CATEGORY_VALIDATION,
                        context={"customer_id": customer_id}
                    ))
                
                # Format for visualization
                visualization_data = format_insights_visualization(
                    anomalies_data=anomalies_data,
                    suggestions_data=suggestions_data,
                    opportunities_data=opportunities_data
                )
                
                # Return combined data
                return {
                    "type": "success",
                    "data": {
                        "anomalies": anomalies_data,
                        "suggestions": suggestions_data,
                        "opportunities": opportunities_data,
                        "customer_id": clean_cid,
                        "date_range": {
                            "start_date": start_date,
                            "end_date": end_date
                        }
                    },
                    "visualization": visualization_data
                }
            
            except asyncio.CancelledError:
                error_msg = "Insight requests were cancelled"
                logger.warning(f"Cancelled insight requests for customer {clean_cid}: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_API_ERROR,
                    context={"customer_id": customer_id}
                ))
                
        except Exception as e:
            error_details = handle_exception(
                e,
                context={
                    "customer_id": customer_id,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            logger.error(f"Error generating account insights: {str(e)}")
            return create_error_response(error_details) 