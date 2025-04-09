"""
Budget Tools Module

This module contains budget-related MCP tools.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from utils.logging import get_logger
from utils.validation import (
    validate_customer_id, 
    validate_string_length,
    validate_numeric_range,
    validate_enum
)
from utils.error_handler import (
    create_error_response, 
    handle_exception,
    CATEGORY_VALIDATION,
    SEVERITY_ERROR
)
from utils.formatting import format_customer_id, clean_customer_id

from visualization.budgets import format_budget_for_visualization

# Replace standard logger with utils-provided logger
logger = get_logger(__name__)

def register_budget_tools(mcp, google_ads_service, budget_service) -> None:
    """
    Register budget-related MCP tools.
    
    Args:
        mcp: The MCP server instance
        google_ads_service: The Google Ads service instance
        budget_service: The budget service instance
    """
    @mcp.tool()
    async def get_budgets(customer_id: str, status: str = None, budget_ids: str = None):
        """
        Get campaign budgets for a Google Ads account with optional filtering.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            status: Optional status filter (ENABLED, REMOVED, etc.)
            budget_ids: Optional comma-separated list of budget IDs to retrieve
            
        Returns:
            Formatted list of campaign budgets and their utilization
        """
        try:
            # Validate inputs
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")
                
            # Validate status if provided
            valid_statuses = ["ENABLED", "REMOVED", "UNKNOWN", "PAUSED"] # Add other valid statuses if needed
            if status and not validate_enum(status, valid_statuses, case_sensitive=False):
                input_errors.append(f"Invalid status: {status}. Expected one of: {', '.join(valid_statuses)}.")
                
            # Validate budget_ids if provided
            budget_id_list = None
            if budget_ids:
                if not validate_string_length(budget_ids, min_length=1):
                    input_errors.append(f"Invalid budget_ids: {budget_ids}. Must be a non-empty comma-separated string.")
                else:
                    budget_id_list_val = [id.strip() for id in budget_ids.split(",") if id.strip()]
                    if not budget_id_list_val:
                        input_errors.append(f"Invalid budget_ids format: {budget_ids}. Must contain at least one valid budget ID.")
                    elif len(budget_id_list_val) != len(budget_ids.split(",")):
                        input_errors.append(f"Invalid budget_ids format: {budget_ids}. Ensure IDs are separated by commas without extra empty entries.")
                    else:
                        budget_id_list = budget_id_list_val # Use validated list
                        
            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_budgets: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg), 
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "status": status, "budget_ids": budget_ids}
                ))

            # Clean customer ID using utility function
            clean_cid = clean_customer_id(customer_id)
                
            logger.info(f"Getting campaign budgets for customer ID {clean_cid}")
            
            # Get budgets using the BudgetService
            budgets = await budget_service.get_budgets(
                customer_id=clean_cid,
                status_filter=status,
                budget_ids=budget_id_list # Pass the validated list
            )
            
            # Standardize handling for empty results
            if not budgets:
                error_msg = "No campaign budgets found with the specified filters."
                logger.info(f"No budgets found for {clean_cid} with filters: status={status}, budget_ids={budget_ids}")
                return error_msg # Return message, not error
            
            # Format display customer ID using utility function
            display_customer_id = format_customer_id(clean_cid)
            
            # Format the results as a text report
            report = [
                f"Google Ads Campaign Budgets",
                f"Account ID: {display_customer_id}",
                f"Status Filter: {status.upper() if status else 'All Statuses'}\n",
                f"{'Budget ID':<12} {'Budget Name':<30} {'Amount':<12} {'Period':<10} {'Status':<10} {'Utilization':<12} {'Campaigns':<8}",
                "-" * 100
            ]
            
            # Add data rows
            for budget in sorted(budgets, key=lambda x: x.get("amount", 0), reverse=True):
                name = budget["name"]
                if len(name) > 27:
                    name = name[:24] + "..."
                    
                # Format utilization as percentage
                utilization = f"{budget.get('utilization_percent', 0):.1f}%" if budget.get('utilization_percent') is not None else "N/A"
                
                # Count associated campaigns
                campaign_count = len(budget.get("associated_campaigns", []))
                    
                # Safely format amount
                amount_str = f"${budget.get('amount', 0):,.2f}" if budget.get('amount') is not None else "N/A"
                    
                report.append(
                    f"{budget.get('id', 'N/A'):<12} {name:<30} "
                    f"{amount_str:<12} {budget.get('period', 'UNKNOWN'):<10} "
                    f"{budget.get('status', 'UNKNOWN'):<10} {utilization:<12} {campaign_count:<8}"
                )
                
            # Add budget details for each budget
            report.append("\nBudget Details:")
            for i, budget in enumerate(budgets, 1):
                amount_str = f"${budget.get('amount', 0):,.2f}" if budget.get('amount') is not None else "N/A"
                spend_str = f"${budget.get('current_spend', 0):,.2f}" if budget.get('current_spend') is not None else "N/A"
                util_str = f"{budget.get('utilization_percent', 0):.1f}%" if budget.get('utilization_percent') is not None else "N/A"
                rec_budget_str = f"${budget.get('recommended_budget_amount', 0):,.2f}" if budget.get('recommended_budget_amount') is not None else "N/A"

                report.append(f"\n{i}. Budget: {budget.get('name', 'Unknown')} (ID: {budget.get('id', 'N/A')})")
                report.append(f"   Amount: {amount_str} - Period: {budget.get('period', 'UNKNOWN')}")
                report.append(f"   Current Spend: {spend_str} - Utilization: {util_str}")
                report.append(f"   Status: {budget.get('status', 'UNKNOWN')} - Delivery Method: {budget.get('delivery_method', 'UNKNOWN')}")
                
                if budget.get('has_recommended_budget'):
                    report.append(f"   Recommended Budget: {rec_budget_str}")
                
                # List associated campaigns
                campaigns = budget.get("associated_campaigns", [])
                if campaigns:
                    report.append(f"   Associated Campaigns ({len(campaigns)}):")
                    for campaign in campaigns:
                        cost_str = f"${campaign.get('cost', 0):,.2f}" if campaign.get('cost') is not None else "N/A"
                        report.append(f"   - {campaign.get('name', 'Unknown')} (ID: {campaign.get('id', 'N/A')}) - Status: {campaign.get('status', 'UNKNOWN')}")
                        report.append(f"     Cost: {cost_str}")
                else:
                    report.append("   No associated campaigns")
                
            return "\n".join(report)
            
        except Exception as e:
            # Standardize exception handling
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "status": status, "budget_ids": budget_ids}
            )
            logger.error(f"Error getting campaign budgets: {str(e)}")
            return create_error_response(error_details)
    
    @mcp.tool()
    async def get_budgets_json(customer_id: str, status: str = None, budget_ids: str = None):
        """
        Get campaign budgets in JSON format for visualization.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            status: Optional status filter (ENABLED, REMOVED, etc.)
            budget_ids: Optional comma-separated list of budget IDs to retrieve
            
        Returns:
            JSON data for budget visualization
        """
        try:
            # Validate inputs (same as get_budgets)
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")
                
            valid_statuses = ["ENABLED", "REMOVED", "UNKNOWN", "PAUSED"]
            if status and not validate_enum(status, valid_statuses, case_sensitive=False):
                input_errors.append(f"Invalid status: {status}. Expected one of: {', '.join(valid_statuses)}.")
                
            budget_id_list = None
            if budget_ids:
                if not validate_string_length(budget_ids, min_length=1):
                    input_errors.append(f"Invalid budget_ids: {budget_ids}. Must be a non-empty comma-separated string.")
                else:
                    budget_id_list_val = [id.strip() for id in budget_ids.split(",") if id.strip()]
                    if not budget_id_list_val:
                        input_errors.append(f"Invalid budget_ids format: {budget_ids}. Must contain at least one valid budget ID.")
                    elif len(budget_id_list_val) != len(budget_ids.split(",")):
                        input_errors.append(f"Invalid budget_ids format: {budget_ids}. Ensure IDs are separated by commas without extra empty entries.")
                    else:
                        budget_id_list = budget_id_list_val
                        
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in get_budgets_json: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg), 
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "status": status, "budget_ids": budget_ids}
                ))

            # Clean customer ID using utility function
            clean_cid = clean_customer_id(customer_id)
                
            logger.info(f"Getting campaign budgets JSON for customer ID {clean_cid}")
            
            # Get budgets using the BudgetService
            budgets = await budget_service.get_budgets(
                customer_id=clean_cid,
                status_filter=status,
                budget_ids=budget_id_list
            )
            
            # Standardize handling for empty results
            if not budgets:
                error_msg = "No campaign budgets found with the specified filters."
                logger.info(f"No budgets found for {clean_cid} with filters: status={status}, budget_ids={budget_ids}")
                return create_error_response(handle_exception(
                    ValueError(error_msg),
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "status": status, "budget_ids": budget_ids}
                ))
            
            # Use the specialized budget visualization formatter
            visualization_data = format_budget_for_visualization(budgets)
            
            return {
                "type": "success",
                "data": budgets,
                "visualization": visualization_data
            }
            
        except Exception as e:
            # Standardize exception handling
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "status": status, "budget_ids": budget_ids}
            )
            logger.error(f"Error getting campaign budgets JSON: {str(e)}")
            return create_error_response(error_details)
    
    @mcp.tool()
    async def analyze_budgets(customer_id: str, budget_ids: str = None, days_to_analyze: int = 30):
        """
        Analyze campaign budget performance and provide insights.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            budget_ids: Optional comma-separated list of budget IDs to analyze
            days_to_analyze: Number of days to look back for analysis (default: 30)
            
        Returns:
            Formatted analysis of budget performance with insights and recommendations
        """
        try:
            # Validate inputs
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")

            # Validate days_to_analyze
            if not validate_numeric_range(days_to_analyze, min_value=1, max_value=365):
                input_errors.append(f"Invalid days_to_analyze: {days_to_analyze}. Must be between 1 and 365.")

            # Validate budget_ids if provided
            budget_id_list = None
            if budget_ids:
                if not validate_string_length(budget_ids, min_length=1):
                    input_errors.append(f"Invalid budget_ids: {budget_ids}. Must be a non-empty comma-separated string.")
                else:
                    budget_id_list_val = [id.strip() for id in budget_ids.split(",") if id.strip()]
                    if not budget_id_list_val:
                        input_errors.append(f"Invalid budget_ids format: {budget_ids}. Must contain at least one valid budget ID.")
                    elif len(budget_id_list_val) != len(budget_ids.split(",")):
                        input_errors.append(f"Invalid budget_ids format: {budget_ids}. Ensure IDs are separated by commas without extra empty entries.")
                    else:
                        budget_id_list = budget_id_list_val

            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in analyze_budgets: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg), 
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "budget_ids": budget_ids, "days_to_analyze": days_to_analyze}
                ))
                
            # Clean customer ID using utility function
            clean_cid = clean_customer_id(customer_id)
                
            logger.info(f"Analyzing campaign budgets for customer ID {clean_cid}")
            
            # Get budget analysis from the BudgetService
            analysis_results = await budget_service.analyze_budget_performance(
                customer_id=clean_cid,
                budget_ids=budget_id_list,
                days_to_analyze=days_to_analyze
            )
            
            # Standardize handling for empty results
            if not analysis_results:
                error_msg = "No campaign budgets found for analysis with the specified filters."
                logger.info(f"No budgets to analyze for {clean_cid} with filters: budget_ids={budget_ids}")
                return error_msg # Return message, not error
            
            # Format display customer ID using utility function
            display_customer_id = format_customer_id(clean_cid)
            
            # Format the results as a text report
            report = [
                f"Google Ads Campaign Budget Analysis",
                f"Account ID: {display_customer_id}",
                f"Analysis Period: Last {days_to_analyze} days\n",
                f"Found {len(analysis_results)} budget(s) for analysis"
            ]
            
            # Add analysis for each budget
            for i, analysis in enumerate(analysis_results, 1):
                amount_str = f"${analysis.get('budget_amount', 0):,.2f}" if analysis.get('budget_amount') is not None else "N/A"
                spend_str = f"${analysis.get('current_spend', 0):,.2f}" if analysis.get('current_spend') is not None else "N/A"
                util_str = f"{analysis.get('utilization_percent', 0):.1f}%" if analysis.get('utilization_percent') is not None else "N/A"

                report.append(f"\n{i}. Budget: {analysis.get('budget_name', 'Unknown')} (ID: {analysis.get('budget_id', 'N/A')})")
                report.append(f"   Amount: {amount_str} - Period: {analysis.get('period', 'UNKNOWN')}")
                report.append(f"   Current Spend: {spend_str} - Utilization: {util_str}")
                report.append(f"   Delivery Method: {analysis.get('delivery_method', 'UNKNOWN')} - Associated Campaigns: {analysis.get('campaign_count', 0)}")
                
                # Add daily metrics if present
                if "daily_metrics" in analysis:
                    daily = analysis["daily_metrics"]
                    avg_spend_str = f"${daily.get('average_daily_spend', 0):,.2f}" if daily.get('average_daily_spend') is not None else "N/A"
                    daily_budget_str = f"${daily.get('daily_budget_target', 0):,.2f}" if daily.get('daily_budget_target') is not None else "N/A"
                    daily_util_str = f"{daily.get('daily_utilization', 0):.1f}%" if daily.get('daily_utilization') is not None else "N/A"
                    report.append(f"   Average Daily Spend: {avg_spend_str} - Daily Budget: {daily_budget_str}")
                    report.append(f"   Daily Utilization: {daily_util_str}")
                
                # Add campaign insights if present
                if "campaign_insights" in analysis and analysis.get("campaign_count", 0) > 0:
                    c_insights = analysis["campaign_insights"]
                    highest_spend_str = f"${c_insights.get('highest_spend_amount', 0):,.2f}" if c_insights.get('highest_spend_amount') is not None else "N/A"
                    lowest_spend_str = f"${c_insights.get('lowest_spend_amount', 0):,.2f}" if c_insights.get('lowest_spend_amount') is not None else "N/A"
                    report.append(f"   Highest Spend Campaign: {c_insights.get('highest_spend', 'N/A')} ({highest_spend_str})")
                    report.append(f"   Lowest Spend Campaign: {c_insights.get('lowest_spend', 'N/A')} ({lowest_spend_str})")
                
                # Add insights
                if analysis.get("insights"):
                    report.append("\n   Insights:")
                    for insight in analysis["insights"]: report.append(f"   - {insight}")
                
                # Add recommendations
                if analysis.get("recommendations"):
                    report.append("\n   Recommendations:")
                    for recommendation in analysis["recommendations"]: report.append(f"   - {recommendation}")
                
            return "\n".join(report)
            
        except Exception as e:
            # Standardize exception handling
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "budget_ids": budget_ids, "days_to_analyze": days_to_analyze}
            )
            logger.error(f"Error analyzing campaign budgets: {str(e)}")
            return create_error_response(error_details)
    
    @mcp.tool()
    async def update_budget(customer_id: str, budget_id: str, amount: float = None, 
                           name: str = None, delivery_method: str = None):
        """
        Update a campaign budget's properties.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            budget_id: ID of the budget to update
            amount: New budget amount in the account's currency (optional)
            name: New budget name (optional)
            delivery_method: New delivery method (STANDARD or ACCELERATED) (optional)
            
        Returns:
            Formatted result of the budget update operation or error response
        """
        try:
            # Validate inputs
            input_errors = []

            if not validate_customer_id(customer_id):
                input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")
                
            if not validate_string_length(budget_id, min_length=1):
                input_errors.append(f"Budget ID is required.")
                
            # Validate amount if provided
            if amount is not None and not validate_numeric_range(amount, min_value=0.01): # Budgets typically must be > 0
                input_errors.append(f"Invalid amount: {amount}. Must be a positive number (e.g., > 0.01).")
                
            # Validate name if provided
            if name is not None and not validate_string_length(name, min_length=1, max_length=255): # Assuming max length
                input_errors.append(f"Invalid name: {name}. Must be a non-empty string (max 255 chars).")
                
            # Validate delivery_method if provided
            valid_delivery_methods = ["STANDARD", "ACCELERATED"]
            if delivery_method is not None and not validate_enum(delivery_method, valid_delivery_methods, case_sensitive=True):
                input_errors.append(f"Invalid delivery_method: {delivery_method}. Must be one of: {', '.join(valid_delivery_methods)}.")
                
            # Ensure at least one field to update is provided
            if amount is None and name is None and delivery_method is None:
                input_errors.append("At least one of amount, name, or delivery_method must be provided for update.")
                
            # Return error if validation failed
            if input_errors:
                error_msg = "; ".join(input_errors)
                logger.warning(f"Validation error in update_budget: {error_msg}")
                return create_error_response(handle_exception(
                    ValueError(error_msg), 
                    category=CATEGORY_VALIDATION,
                    context={"customer_id": customer_id, "budget_id": budget_id, "amount": amount, "name": name, "delivery_method": delivery_method}
                ))

            # Clean customer ID using utility function
            clean_cid = clean_customer_id(customer_id)
                
            logger.info(f"Updating campaign budget {budget_id} for customer ID {clean_cid}")
            
            # Convert amount to micros if provided
            amount_micros = None
            if amount is not None:
                amount_micros = int(round(amount * 1_000_000)) # Use round for better precision
            
            # Update the budget using BudgetService
            result = await budget_service.update_budget(
                customer_id=clean_cid,
                budget_id=budget_id,
                amount_micros=amount_micros,
                name=name,
                delivery_method=delivery_method
            )
            
            # Standardize error response from service
            if not result.get("success", False):
                error_message = result.get('error', 'Unknown error updating budget')
                logger.error(f"Failed to update budget {budget_id}: {error_message}")
                return create_error_response(handle_exception(
                    ValueError(error_message), # Consider a more specific exception type if possible
                    category=CATEGORY_API_ERROR, # Assuming API error
                    context={"customer_id": customer_id, "budget_id": budget_id, "update_params": {"amount":amount, "name":name, "delivery_method":delivery_method}}
                ))
            
            # Format the successful result as a report
            report = [
                f"Google Ads Campaign Budget Update",
                f"Budget ID: {budget_id}",
                f"Status: {result.get('message', 'Success')}"
            ]
            
            # Show updated budget amount if available and different
            if result.get('amount_micros') is not None:
                updated_amount_dollars = result.get('amount_dollars', result.get('amount_micros', 0) / 1000000)
                # Only show if it was actually updated (amount was provided)
                if amount is not None:
                     report.append(f"\nUpdated Budget Amount: ${updated_amount_dollars:,.2f}")
            
            # Show updated name if available and different
            if result.get('name') is not None and name is not None and result.get('name') == name:
                 report.append(f"Updated Budget Name: {result.get('name')}")
                 
            # Show updated delivery method if available and different
            if result.get('delivery_method') is not None and delivery_method is not None and result.get('delivery_method') == delivery_method:
                 report.append(f"Updated Delivery Method: {result.get('delivery_method')}")
                 
            # Show the resource name if available
            if result.get('resource_name'):
                report.append(f"Resource: {result.get('resource_name')}")
            
            # Note: Removed sections for 'requested_changes' and 'current_budget' 
            # as they are less relevant for a successful update confirmation.
            # The focus should be on confirming the *applied* changes.
            
            return "\n".join(report)
            
        except Exception as e:
            # Standardize exception handling
            error_details = handle_exception(
                e,
                context={"customer_id": customer_id, "budget_id": budget_id, "amount": amount, "name": name, "delivery_method": delivery_method}
            )
            logger.error(f"Error updating campaign budget: {str(e)}")
            return create_error_response(error_details) 