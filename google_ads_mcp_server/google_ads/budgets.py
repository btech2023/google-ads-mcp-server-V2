"""
Budget Management Module

This module provides functionality for managing Google Ads campaign budgets.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Import utility functions
from google_ads_mcp_server.utils.validation import (
    validate_customer_id,
    validate_not_none,
    validate_positive_integer,
    validate_list_not_empty,
    # Assuming a function exists or can be added for budget ID format if needed
    # validate_budget_id_format 
)
from google_ads_mcp_server.utils.error_handler import (
    handle_exception,
    create_error_response,
    ErrorDetails,
    CATEGORY_BUSINESS_LOGIC, # Or potentially CATEGORY_API_ERROR if calls fail
    SEVERITY_ERROR,
    SEVERITY_WARNING
)
from google_ads_mcp_server.utils.formatting import clean_customer_id

logger = logging.getLogger(__name__)

class BudgetService:
    """Service for managing Google Ads campaign budgets."""
    
    def __init__(self, google_ads_service):
        """
        Initialize the Budget service.
        
        Args:
            google_ads_service: The Google Ads service instance
        """
        self.google_ads_service = google_ads_service
        # Assuming google_ads_service has the client attribute
        # self.ga_service = google_ads_service.client.get_service("GoogleAdsService") 
        logger.info("BudgetService initialized")
    
    async def get_budgets(self, customer_id: str, status_filter: Optional[str] = None, 
                          budget_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get campaign budgets for a customer with optional filtering.
        
        Args:
            customer_id: Google Ads customer ID
            status_filter: Optional filter for budget status (ENABLED, REMOVED, etc.)
            budget_ids: Optional list of specific budget IDs to retrieve
            
        Returns:
            List of campaign budget data or raises an exception on error.
        """
        # --- Validation ---
        if not validate_customer_id(customer_id):
            raise ValueError(f"Invalid customer ID format: {customer_id}")
        # Add validation for status_filter if it's an enum
        # Add validation for budget_ids format if needed

        cleaned_customer_id = clean_customer_id(customer_id)
        logger.info(f"Getting campaign budgets for customer ID {cleaned_customer_id}")
        
        try:
            # Assuming self.google_ads_service.get_campaign_budgets handles API errors
            budgets = await self.google_ads_service.get_campaign_budgets(
                customer_id=cleaned_customer_id,
                status_filter=status_filter,
                budget_ids=budget_ids
            )
            logger.info(f"Retrieved {len(budgets)} campaign budgets for customer {cleaned_customer_id}")
            return budgets
        except Exception as e:
            # --- Error Handling ---
            error_details = handle_exception(
                e, 
                context={"customer_id": cleaned_customer_id, "method": "get_budgets"},
                category=CATEGORY_BUSINESS_LOGIC # Or CATEGORY_API_ERROR depending on where the exception originated
            )
            logger.error(f"Error getting budgets: {error_details.message}")
            # Decide whether to return an error structure or raise exception
            # Raising is often better for service layers unless a specific return format is required
            raise ValueError(error_details.message) from e # Or a custom exception
    
    async def update_budget(self, customer_id: str, budget_id: str, amount_micros: Optional[int] = None,
                           name: Optional[str] = None, delivery_method: Optional[str] = None) -> Dict[str, Any]:
        """
        Update a campaign budget's properties.
        
        Args:
            customer_id: Google Ads customer ID
            budget_id: ID of the budget to update
            amount_micros: New budget amount in micros (optional)
            name: New budget name (optional)
            delivery_method: New delivery method (STANDARD or ACCELERATED) (optional)
            
        Returns:
            Dictionary with the result of the operation (success or error details)
        """
        context = {
            "customer_id": customer_id, 
            "budget_id": budget_id, 
            "method": "update_budget",
            "update_params": {"amount_micros": amount_micros, "name": name, "delivery_method": delivery_method}
        }

        try:
            # --- Validation ---
            if not validate_customer_id(customer_id):
                 raise ValueError(f"Invalid customer ID format: {customer_id}")
            # Add validation for budget_id format if needed
            # Add validation for delivery_method if it's an enum
            if amount_micros is not None and not validate_positive_integer(amount_micros):
                raise ValueError("amount_micros must be a positive integer")
            if not any([amount_micros is not None, name is not None, delivery_method is not None]):
                raise ValueError("At least one of amount_micros, name, or delivery_method must be provided")

            cleaned_customer_id = clean_customer_id(customer_id)
            context["customer_id"] = cleaned_customer_id # Update context

            logger.info(f"Attempting to update campaign budget {budget_id} for customer ID {cleaned_customer_id}")

            # Prepare update fields - Note: Name and delivery_method might not be supported by underlying call
            update_data = {}
            if amount_micros is not None:
                update_data["amount_micros"] = amount_micros
            if name is not None:
                 logger.warning(f"Budget name update requested for {budget_id} but may not be supported.")
                 # update_data["name"] = name # Include if API supports it
            if delivery_method is not None:
                 logger.warning(f"Budget delivery method update requested for {budget_id} but may not be supported.")
                 # update_data["delivery_method"] = delivery_method # Include if API supports it
                 
            # Make the actual API call to update the budget
            # Assuming only amount_micros is currently supported by the underlying service call
            if amount_micros is not None:
                # Assuming self.google_ads_service.update_campaign_budget handles API errors
                updated_budget_info = await self.google_ads_service.update_campaign_budget(
                    budget_id=budget_id,
                    amount_micros=amount_micros,
                    customer_id=cleaned_customer_id
                )
                
                logger.info(f"Successfully updated budget {budget_id} amount to {amount_micros} micros")
                
                # Return success structure
                return {
                    "success": True,
                    "message": "Budget update successful",
                    "budget_id": budget_id,
                    "resource_name": updated_budget_info.get("resource_name"), # Assuming return structure
                    "amount_micros": amount_micros
                    # "amount_dollars": amount_micros / 1000000 # Can add if needed
                }
            else:
                # If only name or delivery_method were requested (not currently supported)
                logger.warning("Only budget amount updates are currently supported via the API")
                # Return a specific warning/error structure
                error_details = ErrorDetails(
                    message="Only amount_micros updates are currently supported",
                    category=CATEGORY_BUSINESS_LOGIC,
                    severity=SEVERITY_WARNING,
                    context=context
                )
                return create_error_response(error_details, success_key="success") # Use success_key if needed

        except Exception as e:
            # --- Error Handling ---
            # Handle known validation errors specifically if desired
            if isinstance(e, ValueError):
                 error_details = handle_exception(e, context=context, severity=SEVERITY_WARNING, category=CATEGORY_BUSINESS_LOGIC)
            else:
                # Handle potential API errors or other unexpected issues
                error_details = handle_exception(e, context=context) # Default severity is ERROR

            logger.error(f"Error updating budget {budget_id}: {error_details.message}")
            return create_error_response(error_details, success_key="success")
    
    async def update_budgets_batch(self, customer_id: str, 
                                 budget_updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Update multiple campaign budgets in a single batch operation.
        
        Args:
            customer_id: Google Ads customer ID
            budget_updates: List of budget updates, each containing:
                - budget_id: ID of the budget to update
                - amount_micros: New budget amount in micros
            
        Returns:
            List of results for each budget update (success or error details)
        """
        base_context = {"customer_id": customer_id, "method": "update_budgets_batch"}
        
        # --- Validation ---
        if not validate_customer_id(customer_id):
            # Cannot proceed without valid customer_id, return a single error
            error = ErrorDetails(
                message=f"Invalid customer ID format: {customer_id}", 
                severity=SEVERITY_ERROR, 
                category=CATEGORY_BUSINESS_LOGIC,
                context=base_context
            )
            logger.error(error.message)
            return [create_error_response(error, success_key="success")]
            
        if not validate_list_not_empty(budget_updates):
             logger.warning("No updates provided for batch budget update.")
             return []

        cleaned_customer_id = clean_customer_id(customer_id)
        base_context["customer_id"] = cleaned_customer_id # Update context

        logger.info(f"Batch updating {len(budget_updates)} campaign budgets for customer ID {cleaned_customer_id}")
        
        valid_updates = []
        results = [] # Store results for all operations (valid and invalid inputs)
        
        for update in budget_updates:
            budget_id = update.get("budget_id")
            amount_micros = update.get("amount_micros")
            item_context = {**base_context, "item_update": update} # Context for this specific item

            # Validate individual item
            item_valid = True
            error_message = None
            
            if not validate_not_none(budget_id, "budget_id"):
                 error_message = "Missing budget_id"
                 item_valid = False
            # Add budget_id format validation if needed here
            elif not validate_not_none(amount_micros, "amount_micros"):
                 error_message = "Missing amount_micros"
                 item_valid = False
            elif not validate_positive_integer(amount_micros):
                 error_message = "amount_micros must be a positive integer"
                 item_valid = False

            if item_valid:
                valid_updates.append({
                    "budget_id": budget_id,
                    "amount_micros": amount_micros
                    # Include original index if needed for matching results later
                })
            else:
                # --- Error Handling for invalid input ---
                error = ErrorDetails(
                    message=error_message, 
                    severity=SEVERITY_WARNING, 
                    category=CATEGORY_BUSINESS_LOGIC,
                    context=item_context
                )
                logger.error(f"Invalid budget update item: {error.message} - {update}")
                results.append(create_error_response(error, success_key="success", extra_data={"budget_id": budget_id}))
        
        # Process valid updates if any exist
        if valid_updates:
            try:
                # Assuming self.google_ads_service.update_campaign_budgets_batch handles API errors
                # and returns a list of results corresponding to valid_updates
                api_results = await self.google_ads_service.update_campaign_budgets_batch(
                    updates=valid_updates,
                    customer_id=cleaned_customer_id
                )
                
                # Ensure api_results is a list matching valid_updates length
                if not isinstance(api_results, list) or len(api_results) != len(valid_updates):
                     raise TypeError(f"Batch update API call returned unexpected result format or length.")

                logger.info(f"Successfully processed batch update API call for {len(valid_updates)} budgets.")
                # Combine API results with the already collected invalid input results
                results.extend(api_results) 
            
            except Exception as e:
                # --- Error Handling for API call ---
                error_details = handle_exception(
                    e, 
                    context={**base_context, "valid_update_count": len(valid_updates)},
                    # Determine category based on exception type (e.g., APIError vs others)
                )
                logger.error(f"Error in batch budget update API call: {error_details.message}")
                # Add a general error result for all items attempted in this batch
                general_error_response = create_error_response(error_details, success_key="success")
                # Apply this error to all items that were part of the failed batch
                failed_batch_results = [
                    {**general_error_response, "budget_id": item["budget_id"]} for item in valid_updates
                ]
                results.extend(failed_batch_results)
        else:
             logger.warning("No valid budget updates to process after initial validation.")

        return results # Return combined results
    
    async def analyze_budget_performance(self, customer_id: str, budget_ids: Optional[List[str]] = None,
                                        days_to_analyze: int = 30) -> List[Dict[str, Any]]:
        """
        Analyze campaign budget performance and provide insights.
        
        Args:
            customer_id: Google Ads customer ID
            budget_ids: Optional list of specific budget IDs to analyze
            days_to_analyze: Number of days to look back for analysis (must be positive)
            
        Returns:
            List of budget analysis data with insights or raises an exception on error.
        """
        context = {"customer_id": customer_id, "budget_ids": budget_ids, "days_to_analyze": days_to_analyze, "method": "analyze_budget_performance"}

        try:
            # --- Validation ---
            if not validate_customer_id(customer_id):
                raise ValueError(f"Invalid customer ID format: {customer_id}")
            if not validate_positive_integer(days_to_analyze):
                 raise ValueError("days_to_analyze must be a positive integer")
            # Add validation for budget_ids format if needed

            cleaned_customer_id = clean_customer_id(customer_id)
            context["customer_id"] = cleaned_customer_id # Update context

            logger.info(f"Analyzing budget performance for customer ID {cleaned_customer_id} over {days_to_analyze} days")
            
            # Calculate date range for analysis (keep internal)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_to_analyze)
            
            # Get budgets to analyze (using the already validated/error-handled get_budgets)
            # This call might raise ValueError if it fails
            budgets = await self.get_budgets(
                customer_id=cleaned_customer_id,
                status_filter="ENABLED",  # Only analyze active budgets
                budget_ids=budget_ids
            )
            
            if not budgets:
                logger.info(f"No active budgets found for analysis for customer {cleaned_customer_id}")
                return []
            
            # Prepare analysis results
            analysis_results = []
            
            for budget in budgets:
                # Skip budgets with no associated campaigns
                if not budget.get("associated_campaigns"):
                    continue
                    
                # Get budget metrics
                budget_amount = budget.get("amount", 0)
                current_spend = budget.get("current_spend", 0)
                utilization = budget.get("utilization_percent", 0)
                
                # Initialize analysis data
                analysis = {
                    "budget_id": budget["id"],
                    "budget_name": budget["name"],
                    "budget_amount": budget_amount,
                    "current_spend": current_spend,
                    "utilization_percent": utilization,
                    "period": budget.get("period", "UNKNOWN"),
                    "delivery_method": budget.get("delivery_method", "UNKNOWN"),
                    "campaign_count": len(budget.get("associated_campaigns", [])),
                    "insights": [],
                    "recommendations": []
                }
                
                # Generate insights based on utilization
                if utilization > 95:
                    analysis["insights"].append("Budget is nearly or fully depleted")
                    if budget.get("has_recommended_budget") and budget.get("recommended_budget_amount", 0) > budget_amount:
                        analysis["recommendations"].append(f"Consider increasing the budget to the recommended amount of ${budget.get('recommended_budget_amount', 0):,.2f}")
                    else:
                        analysis["recommendations"].append("Consider increasing the budget amount")
                        
                elif utilization > 85:
                    analysis["insights"].append("Budget utilization is high")
                    analysis["recommendations"].append("Monitor closely to ensure budget lasts throughout the period")
                    
                elif utilization < 30:
                    analysis["insights"].append("Budget utilization is low")
                    if budget.get("delivery_method") == "STANDARD":
                        analysis["recommendations"].append("Consider reallocating budget to higher-performing campaigns or reducing the budget amount")
                
                # Daily budget specific insights (most common case)
                if budget.get("period") == "DAILY":
                    daily_target = budget_amount / days_to_analyze
                    daily_spend = current_spend / days_to_analyze
                    
                    analysis["daily_metrics"] = {
                        "average_daily_spend": daily_spend,
                        "daily_budget_target": daily_target,
                        "daily_utilization": (daily_spend / daily_target * 100) if daily_target > 0 else 0
                    }
                    
                    if daily_spend > daily_target * 1.2:
                        analysis["insights"].append("Average daily spend exceeds the daily budget target by more than 20%")
                    elif daily_spend < daily_target * 0.5:
                        analysis["insights"].append("Average daily spend is less than 50% of the daily budget target")
                
                # Add campaign-specific insights
                campaigns = budget.get("associated_campaigns", [])
                
                # Find highest and lowest performing campaigns
                if campaigns:
                    sorted_campaigns = sorted(campaigns, key=lambda x: x.get("cost", 0), reverse=True)
                    analysis["campaign_insights"] = {
                        "highest_spend": sorted_campaigns[0]["name"],
                        "highest_spend_amount": sorted_campaigns[0].get("cost", 0),
                        "lowest_spend": sorted_campaigns[-1]["name"],
                        "lowest_spend_amount": sorted_campaigns[-1].get("cost", 0),
                    }
                    
                    # Check for budget distribution issues
                    if len(campaigns) > 1 and sorted_campaigns[0].get("cost", 0) > current_spend * 0.8:
                        analysis["insights"].append(f"Budget is heavily concentrated in a single campaign ({sorted_campaigns[0]['name']})")
                        analysis["recommendations"].append("Consider reviewing campaign performance and potentially redistributing budget")
                
                analysis_results.append(analysis)
            
            logger.info(f"Completed budget analysis for {len(analysis_results)} budgets for customer {cleaned_customer_id}")
            return analysis_results

        except Exception as e:
             # --- Error Handling ---
             # Handle known validation errors specifically
             if isinstance(e, ValueError):
                  error_details = handle_exception(e, context=context, severity=SEVERITY_WARNING, category=CATEGORY_BUSINESS_LOGIC)
                  logger.warning(f"Validation error during budget analysis: {error_details.message}")
                  raise e # Re-raise validation errors
             else:
                # Handle other unexpected errors during analysis
                error_details = handle_exception(e, context=context)
                logger.error(f"Error analyzing budget performance: {error_details.message}")
                # Decide whether to return partial results, an error structure, or raise
                raise RuntimeError(error_details.message) from e # Or a custom exception 