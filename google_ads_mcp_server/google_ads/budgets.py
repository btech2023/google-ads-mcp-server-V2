"""
Budget Management Module

This module provides functionality for managing Google Ads campaign budgets.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

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
        self.ga_service = google_ads_service.client.get_service("GoogleAdsService")
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
            List of campaign budget data
        """
        logger.info(f"Getting campaign budgets for customer ID {customer_id}")
        
        # Get data from the Google Ads service
        budgets = await self.google_ads_service.get_campaign_budgets(
            customer_id=customer_id,
            status_filter=status_filter,
            budget_ids=budget_ids
        )
        
        logger.info(f"Retrieved {len(budgets)} campaign budgets")
        return budgets
    
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
            Dictionary with the result of the operation
        """
        logger.info(f"Updating campaign budget {budget_id} for customer ID {customer_id}")
        
        # Validate that at least one update field is provided
        if not any([amount_micros, name, delivery_method]):
            error_msg = "At least one of amount_micros, name, or delivery_method must be provided"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        try:
            # First get the current budget to ensure it exists
            current_budgets = await self.get_budgets(customer_id, budget_ids=[budget_id])
            
            if not current_budgets:
                error_msg = f"Budget with ID {budget_id} not found"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
            
            current_budget = current_budgets[0]
            
            # Prepare update fields
            update_data = {}
            
            if amount_micros is not None:
                update_data["amount_micros"] = amount_micros
                
            if name is not None:
                update_data["name"] = name
                
            if delivery_method is not None:
                update_data["delivery_method"] = delivery_method
                
            # Make the actual API call to update the budget
            # Only amount_micros is currently supported by the API
            if amount_micros is not None:
                try:
                    updated_budget = await self.google_ads_service.update_campaign_budget(
                        budget_id=budget_id,
                        amount_micros=amount_micros,
                        customer_id=customer_id
                    )
                    
                    logger.info(f"Successfully updated budget {budget_id} amount to {amount_micros} micros")
                    
                    return {
                        "success": True,
                        "message": "Budget update successful",
                        "budget_id": budget_id,
                        "resource_name": updated_budget.get("resource_name"),
                        "amount_micros": amount_micros,
                        "amount_dollars": amount_micros / 1000000
                    }
                except Exception as e:
                    error_msg = f"Error calling budget update API: {str(e)}"
                    logger.error(error_msg)
                    return {"success": False, "error": error_msg}
            else:
                # If only name or delivery_method were requested (not currently supported)
                logger.warning("Only budget amount updates are currently supported via the API")
                return {
                    "success": False,
                    "error": "Only amount_micros updates are currently supported",
                    "budget_id": budget_id,
                    "requested_changes": update_data,
                }
            
        except Exception as e:
            error_msg = f"Error updating budget: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
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
            List of results for each budget update
        """
        logger.info(f"Batch updating {len(budget_updates)} campaign budgets for customer ID {customer_id}")
        
        if not budget_updates:
            logger.warning("No updates provided for batch update")
            return []
        
        # Validate each update
        valid_updates = []
        invalid_update_results = [] # Store results for invalid inputs immediately
        
        for update in budget_updates:
            budget_id = update.get("budget_id")
            amount_micros = update.get("amount_micros")
            
            if not budget_id:
                error_msg = f"Missing budget_id in update: {update}"
                logger.error(error_msg)
                invalid_update_results.append({
                    "success": False,
                    "error": "Missing budget_id",
                    "budget_id": None, # Or extract if possible from update dict
                    "status": "INVALID_INPUT"
                })
                continue
                
            if amount_micros is None:
                error_msg = f"Missing amount_micros in update for budget {budget_id}"
                logger.error(error_msg)
                invalid_update_results.append({
                    "success": False,
                    "error": "Missing amount_micros",
                    "budget_id": budget_id,
                    "status": "INVALID_INPUT"
                })
                continue
                
            # Add to valid updates
            valid_updates.append({
                "budget_id": budget_id,
                "amount_micros": amount_micros
            })
        
        # Initialize final results list with any invalid update results
        final_results = invalid_update_results
        
        if not valid_updates:
            # If only invalid updates were provided, return those results
            if final_results:
                logger.error("No valid updates to process, returning only invalid update errors.")
                return final_results
            else:
                # Should not happen if initial budget_updates list was not empty, but handle defensively
                error_msg = "No valid updates to process"
                logger.error(error_msg)
                return [{"success": False, "error": error_msg}]
        
        try:
            # Call the batch update method - THIS SHOULD RETURN A LIST
            api_results = await self.google_ads_service.update_campaign_budgets_batch(
                updates=valid_updates,
                customer_id=customer_id
            )
            
            # Ensure api_results is a list before extending
            if not isinstance(api_results, list):
                error_msg = f"Batch update API call returned unexpected type: {type(api_results)}"
                logger.error(error_msg)
                # Add a general error result for the valid updates
                final_results.append({"success": False, "error": error_msg, "status": "API_ERROR"})
            else:
                logger.info(f"Successfully processed batch update for {len(valid_updates)} budgets via API.")
                # Add the API results (which should be a list) to the final results
                final_results.extend(api_results)
            
            return final_results
            
        except Exception as e:
            error_msg = f"Error in batch budget update API call: {str(e)}"
            logger.error(error_msg)
            # Add a general error result for the valid updates that failed due to the exception
            final_results.append({"success": False, "error": error_msg, "status": "API_EXCEPTION"})
            return final_results
    
    async def analyze_budget_performance(self, customer_id: str, budget_ids: Optional[List[str]] = None,
                                        days_to_analyze: int = 30) -> List[Dict[str, Any]]:
        """
        Analyze campaign budget performance and provide insights.
        
        Args:
            customer_id: Google Ads customer ID
            budget_ids: Optional list of specific budget IDs to analyze
            days_to_analyze: Number of days to look back for analysis
            
        Returns:
            List of budget analysis data with insights
        """
        logger.info(f"Analyzing budget performance for customer ID {customer_id}")
        
        # Calculate date range for analysis
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_to_analyze)
        
        # Get budgets to analyze
        budgets = await self.get_budgets(
            customer_id=customer_id,
            status_filter="ENABLED",  # Only analyze active budgets
            budget_ids=budget_ids
        )
        
        if not budgets:
            logger.info("No budgets found for analysis")
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
        
        logger.info(f"Completed budget analysis for {len(analysis_results)} budgets")
        return analysis_results 