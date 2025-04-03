"""
Insights Service Module

This module provides services for generating automated insights from Google Ads data,
including anomaly detection, optimization suggestions, and opportunity discovery.
"""

import logging
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import asyncio

from google_ads.client import GoogleAdsService
from google_ads.keywords import KeywordService
from google_ads.search_terms import SearchTermService
from google_ads.budgets import BudgetService
from google_ads.ad_groups import AdGroupService

logger = logging.getLogger(__name__)

class InsightsService:
    """
    Service for generating insights from Google Ads data.
    
    This service provides methods for:
    - Detecting performance anomalies
    - Generating optimization suggestions
    - Discovering new opportunities
    """
    
    def __init__(self, google_ads_service: GoogleAdsService):
        """
        Initialize the InsightsService.
        
        Args:
            google_ads_service: The GoogleAdsService instance
        """
        self.google_ads_service = google_ads_service
        self.keyword_service = KeywordService(google_ads_service)
        self.search_term_service = SearchTermService(google_ads_service)
        self.budget_service = BudgetService(google_ads_service)
        self.ad_group_service = AdGroupService(google_ads_service)
        logger.info("InsightsService initialized")
    
    async def detect_performance_anomalies(
        self,
        customer_id: str,
        entity_type: str = "CAMPAIGN",
        entity_ids: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        comparison_period: str = "PREVIOUS_PERIOD",
        threshold: float = 2.0
    ) -> Dict[str, Any]:
        """
        Detect anomalies in performance metrics.
        
        Args:
            customer_id: Google Ads customer ID
            entity_type: Type of entity to analyze (CAMPAIGN, AD_GROUP, KEYWORD)
            entity_ids: Optional list of entity IDs to filter by
            metrics: List of metrics to analyze (defaults to impressions, clicks, cost, ctr, conversions)
            start_date: Start date for analysis (defaults to 7 days ago)
            end_date: End date for analysis (defaults to today)
            comparison_period: Period to compare against (PREVIOUS_PERIOD, SAME_PERIOD_LAST_YEAR)
            threshold: Z-score threshold for anomaly detection (default: 2.0)
            
        Returns:
            Dictionary containing detected anomalies
        """
        logger.info(f"Detecting performance anomalies for customer {customer_id}")
        
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            # Default to 7 days for anomaly detection
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            
        # Set default metrics if not provided
        if not metrics:
            metrics = ["impressions", "clicks", "cost", "ctr", "conversions"]
            
        # Get performance data for current period
        current_data = await self._get_performance_data(
            customer_id, entity_type, entity_ids, metrics, start_date, end_date
        )
        
        # Get comparison data
        comparison_data = await self._get_comparison_data(
            customer_id, entity_type, entity_ids, metrics, start_date, end_date, comparison_period
        )
        
        # Detect anomalies
        anomalies = self._analyze_for_anomalies(
            current_data, comparison_data, metrics, threshold
        )
        
        return {
            "anomalies": anomalies,
            "metadata": {
                "customer_id": customer_id,
                "entity_type": entity_type,
                "start_date": start_date,
                "end_date": end_date,
                "comparison_period": comparison_period,
                "threshold": threshold,
                "total_entities_analyzed": len(current_data) if current_data else 0,
                "anomalies_detected": len(anomalies),
                "metrics_analyzed": metrics
            }
        }
        
    async def _get_performance_data(
        self, 
        customer_id: str,
        entity_type: str,
        entity_ids: Optional[List[str]], 
        metrics: List[str],
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Get performance data for the specified entity type and time period.
        
        Args:
            customer_id: Google Ads customer ID
            entity_type: Type of entity (CAMPAIGN, AD_GROUP, KEYWORD)
            entity_ids: Optional list of entity IDs to filter by
            metrics: List of metrics to retrieve
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of entities with performance data
        """
        if entity_type == "CAMPAIGN":
            return await self.google_ads_service.get_campaigns(
                start_date=start_date,
                end_date=end_date,
                customer_id=customer_id,
                campaign_ids=entity_ids
            )
        elif entity_type == "AD_GROUP":
            return await self.ad_group_service.get_ad_groups(
                customer_id=customer_id,
                ad_group_ids=entity_ids,
                start_date=start_date,
                end_date=end_date
            )
        elif entity_type == "KEYWORD":
            return await self.keyword_service.get_keywords(
                customer_id=customer_id,
                keyword_ids=entity_ids,
                start_date=start_date,
                end_date=end_date
            )
        else:
            logger.warning(f"Unsupported entity type: {entity_type}")
            return []
            
    async def _get_comparison_data(
        self,
        customer_id: str,
        entity_type: str,
        entity_ids: Optional[List[str]],
        metrics: List[str],
        start_date: str,
        end_date: str,
        comparison_period: str
    ) -> List[Dict[str, Any]]:
        """
        Get comparison data for anomaly detection.
        
        Args:
            customer_id: Google Ads customer ID
            entity_type: Type of entity (CAMPAIGN, AD_GROUP, KEYWORD)
            entity_ids: Optional list of entity IDs to filter by
            metrics: List of metrics to retrieve
            start_date: Current period start date
            end_date: Current period end date
            comparison_period: Type of comparison period (PREVIOUS_PERIOD, SAME_PERIOD_LAST_YEAR)
            
        Returns:
            List of entities with comparison performance data
        """
        # Calculate comparison date range
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        date_range = (end_dt - start_dt).days + 1
        
        if comparison_period == "PREVIOUS_PERIOD":
            comparison_end = start_dt - timedelta(days=1)
            comparison_start = comparison_end - timedelta(days=date_range-1)
        elif comparison_period == "SAME_PERIOD_LAST_YEAR":
            comparison_start = start_dt - timedelta(days=365)
            comparison_end = end_dt - timedelta(days=365)
        else:
            logger.warning(f"Unsupported comparison period: {comparison_period}")
            return []
            
        comparison_start_str = comparison_start.strftime("%Y-%m-%d")
        comparison_end_str = comparison_end.strftime("%Y-%m-%d")
        
        return await self._get_performance_data(
            customer_id,
            entity_type,
            entity_ids,
            metrics,
            comparison_start_str,
            comparison_end_str
        )
    
    def _analyze_for_anomalies(
        self,
        current_data: List[Dict[str, Any]],
        comparison_data: List[Dict[str, Any]],
        metrics: List[str],
        threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Analyze performance data to detect anomalies.
        
        Args:
            current_data: Current period performance data
            comparison_data: Comparison period performance data
            metrics: List of metrics to analyze
            threshold: Z-score threshold for anomaly detection
            
        Returns:
            List of detected anomalies
        """
        if not current_data or not comparison_data or not metrics:
            return []
            
        anomalies = []
        
        # Create a dictionary map from ID to comparison data for faster lookups
        comparison_map = {item.get('id', ''): item for item in comparison_data}
        
        # Pre-calculate metric statistics once to avoid recalculation
        metric_stats = {}
        for metric in metrics:
            values = [item.get(metric, 0) for item in current_data if metric in item]
            if not values or len(values) < 2:
                continue
                
            mean = sum(values) / len(values)
            # Calculate standard deviation
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5 if variance > 0 else 1.0  # Avoid division by zero
            
            metric_stats[metric] = {
                'mean': mean,
                'std_dev': std_dev
            }
        
        # Analyze each entity
        for item in current_data:
            entity_id = item.get('id', '')
            if not entity_id:
                continue
                
            # Get comparison data for this entity using dictionary lookup
            comparison_item = comparison_map.get(entity_id)
            if not comparison_item:
                continue
                
            entity_anomalies = []
            
            for metric in metrics:
                # Skip if metric doesn't exist in either dataset
                if metric not in item or metric not in comparison_item:
                    continue
                    
                current_value = item.get(metric, 0)
                comparison_value = comparison_item.get(metric, 0)
                
                # Skip metrics with zero or very small values to avoid false positives
                if abs(current_value) < 1e-9 and abs(comparison_value) < 1e-9:
                    continue
                
                # Calculate change
                if comparison_value != 0:
                    change_pct = (current_value - comparison_value) / abs(comparison_value)
                else:
                    # If comparison value is zero, use a large value to indicate significant change
                    change_pct = 1.0 if current_value > 0 else 0.0
                
                # Calculate z-score if we have statistics for this metric
                if metric in metric_stats and metric_stats[metric]['std_dev'] > 0:
                    z_score = abs(current_value - metric_stats[metric]['mean']) / metric_stats[metric]['std_dev']
                else:
                    # Skip z-score analysis if we don't have valid statistics
                    z_score = 0
                
                # Detect anomalies: significant change AND unusual value
                # We now combine both criteria to avoid false positives
                is_anomaly = (abs(change_pct) > 0.2) and (z_score > threshold)
                
                if is_anomaly:
                    entity_anomalies.append({
                        'metric': metric,
                        'current_value': current_value,
                        'comparison_value': comparison_value,
                        'change_pct': change_pct,
                        'z_score': z_score,
                        'direction': 'increase' if current_value > comparison_value else 'decrease',
                        'severity': 'high' if z_score > threshold * 1.5 else 'medium'
                    })
            
            # Only add entities with actual anomalies
            if entity_anomalies:
                # Include essential entity data with the anomalies
                entity_data = {
                    'id': entity_id,
                    'name': item.get('name', 'Unknown'),
                    'type': item.get('type', 'Unknown'),
                    'status': item.get('status', 'Unknown'),
                    'anomalies': entity_anomalies
                }
                
                anomalies.append(entity_data)
        
        # Sort anomalies by severity, then by highest change percentage
        anomalies.sort(
            key=lambda x: (
                sum(1 for a in x['anomalies'] if a['severity'] == 'high'),
                max(abs(a['change_pct']) for a in x['anomalies']) if x['anomalies'] else 0
            ),
            reverse=True
        )
        
        return anomalies
    
    async def generate_optimization_suggestions(
        self,
        customer_id: str,
        entity_type: Optional[str] = None,
        entity_ids: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate optimization suggestions for the account, campaigns, or ad groups.
        
        Args:
            customer_id: Google Ads customer ID
            entity_type: Optional entity type (CAMPAIGN, AD_GROUP)
            entity_ids: Optional list of entity IDs to analyze
            start_date: Start date for analysis (defaults to 30 days ago)
            end_date: End date for analysis (defaults to today)
            
        Returns:
            Dictionary containing optimization suggestions
        """
        logger.info(f"Generating optimization suggestions for customer {customer_id}")
        
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            # Default to 30 days
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
        # Initialize suggestions dictionary
        suggestions = {
            "bid_management": [],
            "budget_allocation": [],
            "negative_keywords": [],
            "ad_copy": [],
            "account_structure": []
        }
        
        # Batch data retrieval - get all the data we need upfront
        data_cache = {}
        
        # 1. Get account-level data (needed regardless of entity_type)
        account_data = await self._batch_retrieve_account_data(
            customer_id, 
            start_date, 
            end_date
        )
        data_cache["account"] = account_data
        
        # 2. Get entity-specific data
        if entity_type == "CAMPAIGN" and entity_ids:
            # Analyze specific campaigns
            campaign_data = await self._analyze_campaigns_for_suggestions(
                customer_id, entity_ids, start_date, end_date
            )
            for category, campaign_suggestions in campaign_data.items():
                suggestions[category].extend(campaign_suggestions)
        elif entity_type == "AD_GROUP" and entity_ids:
            # Analyze specific ad groups
            ad_group_data = await self._analyze_ad_groups_for_suggestions(
                customer_id, entity_ids, start_date, end_date
            )
            for category, ad_group_suggestions in ad_group_data.items():
                suggestions[category].extend(ad_group_suggestions)
        else:
            # Analyze the entire account
            # Get campaign data in batch
            campaign_data = await self._batch_retrieve_campaign_data(
                customer_id, 
                start_date, 
                end_date
            )
            data_cache["campaigns"] = campaign_data
            
            # Use the cached data for analysis
            campaign_suggestions = self._analyze_campaign_data_for_suggestions(
                campaign_data, 
                account_data
            )
            
            for category, campaign_suggs in campaign_suggestions.items():
                suggestions[category].extend(campaign_suggs)
            
            # Get ad group data in batch
            ad_group_data = await self._batch_retrieve_ad_group_data(
                customer_id, 
                start_date, 
                end_date,
                campaign_data.get("campaigns", [])
            )
            data_cache["ad_groups"] = ad_group_data
            
            # Use the cached data for analysis
            ad_group_suggestions = self._analyze_ad_group_data_for_suggestions(
                ad_group_data, 
                campaign_data
            )
            
            for category, ad_group_suggs in ad_group_suggestions.items():
                suggestions[category].extend(ad_group_suggs)
            
            # Generate account-wide suggestions
            account_suggestions = self._generate_account_suggestions(
                account_data, 
                campaign_data, 
                ad_group_data
            )
            
            for category, account_suggs in account_suggestions.items():
                suggestions[category].extend(account_suggs)
        
        # Sort suggestions by impact
        for category in suggestions:
            suggestions[category] = sorted(
                suggestions[category],
                key=lambda x: x.get("impact_score", 0),
                reverse=True
            )
            
            # Limit to top 10 suggestions per category
            suggestions[category] = suggestions[category][:10]
        
        return {
            "suggestions": suggestions,
            "metadata": {
                "customer_id": customer_id,
                "entity_type": entity_type,
                "entity_ids": entity_ids,
                "start_date": start_date,
                "end_date": end_date,
                "total_suggestions": sum(len(suggestions[key]) for key in suggestions)
            }
        }
        
    async def _batch_retrieve_account_data(self, customer_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Retrieve all needed account-level data in a single batch of concurrent calls.
        
        Args:
            customer_id: Google Ads customer ID
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary containing account data
        """
        # Execute multiple API calls concurrently
        account_tasks = [
            self.google_ads_service.get_account_summary(customer_id),
            self.google_ads_service.get_account_performance(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date
            ),
            self.budget_service.get_budgets(customer_id=customer_id)
        ]
        
        # Get search terms data if applicable
        if self.search_term_service:
            account_tasks.append(
                self.search_term_service.get_search_terms(
                    customer_id=customer_id,
                    start_date=start_date,
                    end_date=end_date
                )
            )
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*account_tasks)
        
        # Organize results
        account_data = {
            "account_summary": results[0],
            "account_performance": results[1],
            "budgets": results[2],
            "search_terms": results[3] if len(results) > 3 else []
        }
        
        return account_data
        
    async def _batch_retrieve_campaign_data(self, customer_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Retrieve all needed campaign data in a single batch of concurrent calls.
        
        Args:
            customer_id: Google Ads customer ID
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary containing campaign data
        """
        # Execute multiple API calls concurrently
        campaign_tasks = [
            self.google_ads_service.get_campaigns(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date
            ),
            self.google_ads_service.get_campaign_performance_by_device(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date
            ),
            self.google_ads_service.get_campaign_performance_by_network(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date
            )
        ]
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*campaign_tasks)
        
        # Organize results
        campaign_data = {
            "campaigns": results[0],
            "device_performance": results[1],
            "network_performance": results[2]
        }
        
        return campaign_data
        
    async def _batch_retrieve_ad_group_data(
        self, 
        customer_id: str, 
        start_date: str, 
        end_date: str,
        campaigns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Retrieve all needed ad group data in a single batch of concurrent calls.
        
        Args:
            customer_id: Google Ads customer ID
            start_date: Start date for analysis
            end_date: End date for analysis
            campaigns: List of campaign data for filtering
            
        Returns:
            Dictionary containing ad group data
        """
        # Get campaign IDs for top campaigns only (limit to 10 for efficiency)
        # Sort campaigns by cost
        sorted_campaigns = sorted(
            campaigns,
            key=lambda x: x.get("cost_micros", 0),
            reverse=True
        )
        top_campaign_ids = [c.get("id") for c in sorted_campaigns[:10] if "id" in c]
        
        # Execute multiple API calls concurrently
        ad_group_tasks = [
            self.ad_group_service.get_ad_groups(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date,
                campaign_ids=top_campaign_ids  # Filter to top campaigns only
            ),
            self.keyword_service.get_keywords(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date,
                campaign_ids=top_campaign_ids,  # Filter to top campaigns only
                status_filter="ENABLED"  # Only get active keywords
            )
        ]
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*ad_group_tasks)
        
        # Organize results
        ad_group_data = {
            "ad_groups": results[0],
            "keywords": results[1]
        }
        
        return ad_group_data
        
    def _analyze_campaign_data_for_suggestions(
        self, 
        campaign_data: Dict[str, Any],
        account_data: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Analyze campaign data for optimization suggestions.
        
        Args:
            campaign_data: Campaign data from batch retrieval
            account_data: Account data from batch retrieval
            
        Returns:
            Dictionary of suggestions by category
        """
        suggestions = {
            "bid_management": [],
            "budget_allocation": [],
            "negative_keywords": [],
            "ad_copy": [],
            "account_structure": []
        }
        
        campaigns = campaign_data.get("campaigns", [])
        budgets = account_data.get("budgets", [])
        
        # Create a lookup map for budget data for efficient access
        budget_map = {budget.get('id', ''): budget for budget in budgets}
        
        # 1. Budget allocation suggestions
        for campaign in campaigns:
            campaign_id = campaign.get('id', '')
            campaign_name = campaign.get('name', 'Unknown')
            budget_id = campaign.get('budget_id', '')
            campaign_status = campaign.get('status', '')
            
            # Skip non-active campaigns
            if campaign_status != 'ENABLED':
                continue
                
            # Skip campaigns with no budget
            if not budget_id or budget_id not in budget_map:
                continue
                
            budget = budget_map[budget_id]
            budget_amount = budget.get('amount_micros', 0) / 1000000  # Convert to dollars
            
            # Check budget utilization
            budget_utilization = campaign.get('budget_utilization', 0)
            
            # Campaigns with high budget utilization could benefit from budget increase
            if budget_utilization > 0.9:
                suggestions["budget_allocation"].append({
                    "type": "increase_budget",
                    "entity_type": "CAMPAIGN",
                    "entity_id": campaign_id,
                    "entity_name": campaign_name,
                    "current_value": budget_amount,
                    "suggested_value": budget_amount * 1.2,  # 20% increase
                    "impact_score": 0.8 + (budget_utilization - 0.9) * 2,  # Score 0.8-1.0
                    "reason": f"Campaign is achieving {budget_utilization*100:.1f}% budget utilization.",
                    "recommendation": f"Consider increasing the budget by 20% to capture additional traffic."
                })
            
            # Campaigns with very low budget utilization might need optimization or budget reallocation
            elif budget_utilization < 0.5 and budget_amount > 10:
                suggestions["budget_allocation"].append({
                    "type": "decrease_budget",
                    "entity_type": "CAMPAIGN",
                    "entity_id": campaign_id,
                    "entity_name": campaign_name,
                    "current_value": budget_amount,
                    "suggested_value": budget_amount * 0.8,  # 20% decrease
                    "impact_score": 0.5 + (0.5 - budget_utilization),  # Score 0.5-1.0
                    "reason": f"Campaign is only using {budget_utilization*100:.1f}% of its budget.",
                    "recommendation": f"Consider decreasing the budget and reallocating to higher-performing campaigns."
                })
        
        # Add other campaign analysis for bid management, etc.
        
        return suggestions
    
    def _analyze_ad_group_data_for_suggestions(
        self, 
        ad_group_data: Dict[str, Any],
        campaign_data: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Analyze ad group data for optimization suggestions.
        
        Args:
            ad_group_data: Ad group data from batch retrieval
            campaign_data: Campaign data from batch retrieval
            
        Returns:
            Dictionary of suggestions by category
        """
        suggestions = {
            "bid_management": [],
            "budget_allocation": [],
            "negative_keywords": [],
            "ad_copy": [],
            "account_structure": []
        }
        
        ad_groups = ad_group_data.get("ad_groups", [])
        keywords = ad_group_data.get("keywords", [])
        campaigns = campaign_data.get("campaigns", [])
        
        # Create lookup maps for efficient access
        campaign_map = {campaign.get('id', ''): campaign for campaign in campaigns}
        keyword_by_ad_group = {}
        
        # Group keywords by ad group for more efficient processing
        for keyword in keywords:
            ad_group_id = keyword.get('ad_group_id', '')
            if ad_group_id:
                if ad_group_id not in keyword_by_ad_group:
                    keyword_by_ad_group[ad_group_id] = []
                keyword_by_ad_group[ad_group_id].append(keyword)
        
        # Analyze ad groups for optimization suggestions
        for ad_group in ad_groups:
            ad_group_id = ad_group.get('id', '')
            ad_group_name = ad_group.get('name', 'Unknown')
            campaign_id = ad_group.get('campaign_id', '')
            ad_group_status = ad_group.get('status', '')
            
            # Skip non-active ad groups
            if ad_group_status != 'ENABLED':
                continue
            
            # Get campaign data
            campaign = campaign_map.get(campaign_id, {})
            campaign_name = campaign.get('name', 'Unknown')
            
            # Get ad group performance metrics
            impressions = ad_group.get('impressions', 0)
            clicks = ad_group.get('clicks', 0)
            conversions = ad_group.get('conversions', 0)
            cost_micros = ad_group.get('cost_micros', 0)
            cost = cost_micros / 1000000  # Convert to dollars
            
            # Calculate derived metrics
            ctr = clicks / impressions if impressions > 0 else 0
            conversion_rate = conversions / clicks if clicks > 0 else 0
            cpa = cost / conversions if conversions > 0 else 0
            
            # Ad groups with high cost but no conversions
            if cost > 100 and conversions < 1:
                suggestions["bid_management"].append({
                    "type": "reduce_bids",
                    "entity_type": "AD_GROUP",
                    "entity_id": ad_group_id,
                    "entity_name": ad_group_name,
                    "parent_name": campaign_name,
                    "current_value": None,
                    "suggested_value": None,
                    "impact_score": min(1.0, cost / 200),  # Score based on cost (max 1.0)
                    "reason": f"Ad group has spent ${cost:.2f} with no conversions.",
                    "recommendation": "Consider reducing bids or pausing this ad group."
                })
        
        # Add other ad group analysis
        
        return suggestions
    
    def _generate_account_suggestions(
        self,
        account_data: Dict[str, Any],
        campaign_data: Dict[str, Any],
        ad_group_data: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate account-wide suggestions based on all data.
        
        Args:
            account_data: Account data from batch retrieval
            campaign_data: Campaign data from batch retrieval
            ad_group_data: Ad group data from batch retrieval
            
        Returns:
            Dictionary of suggestions by category
        """
        suggestions = {
            "bid_management": [],
            "budget_allocation": [],
            "negative_keywords": [],
            "ad_copy": [],
            "account_structure": []
        }
        
        # Account-wide budget analysis
        account_perf = account_data.get("account_performance", {})
        campaigns = campaign_data.get("campaigns", [])
        search_terms = account_data.get("search_terms", [])
        
        # Find candidates for negative keywords
        if search_terms:
            negative_candidates = []
            
            for term in search_terms:
                impressions = term.get('impressions', 0)
                clicks = term.get('clicks', 0)
                conversions = term.get('conversions', 0)
                cost_micros = term.get('cost_micros', 0)
                cost = cost_micros / 1000000  # Convert to dollars
                
                # High-impression, low-CTR terms
                if impressions > 100 and clicks == 0:
                    negative_candidates.append({
                        "term": term.get('search_term', ''),
                        "impressions": impressions,
                        "clicks": clicks,
                        "cost": cost,
                        "reason": "High impressions, no clicks",
                        "impact_score": min(1.0, impressions / 1000)  # Score based on impressions (max 1.0)
                    })
                # High-cost, no-conversion terms
                elif cost > 20 and conversions == 0:
                    negative_candidates.append({
                        "term": term.get('search_term', ''),
                        "impressions": impressions,
                        "clicks": clicks,
                        "cost": cost,
                        "reason": "High cost, no conversions",
                        "impact_score": min(1.0, cost / 50)  # Score based on cost (max 1.0)
                    })
            
            # Sort by impact score and add top candidates
            negative_candidates.sort(key=lambda x: x['impact_score'], reverse=True)
            for candidate in negative_candidates[:5]:  # Limit to top 5
                suggestions["negative_keywords"].append({
                    "type": "add_negative_keyword",
                    "entity_type": "ACCOUNT",
                    "entity_id": "",
                    "entity_name": "Account-wide",
                    "term": candidate['term'],
                    "impressions": candidate['impressions'],
                    "cost": candidate['cost'],
                    "impact_score": candidate['impact_score'],
                    "reason": candidate['reason'],
                    "recommendation": f"Add '{candidate['term']}' as a negative keyword."
                })
        
        # Add other account-wide analysis
        
        return suggestions
    
    async def discover_opportunities(
        self,
        customer_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Discover growth opportunities in the account.
        
        Args:
            customer_id: Google Ads customer ID
            start_date: Start date for analysis (defaults to 30 days ago)
            end_date: End date for analysis (defaults to today)
            
        Returns:
            Dictionary containing identified opportunities
        """
        logger.info(f"Discovering opportunities for customer {customer_id}")
        
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            # Default to 30 days for opportunity discovery
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
        # Initialize opportunities dictionary
        opportunities = {
            "keyword_expansion": [],
            "ad_variation": [],
            "structure": [],
            "audience": []
        }
        
        # Discover keyword expansion opportunities
        keyword_opps = await self._discover_keyword_opportunities(
            customer_id, start_date, end_date
        )
        opportunities["keyword_expansion"] = keyword_opps
        
        # Discover ad variation opportunities
        ad_opps = await self._discover_ad_variation_opportunities(
            customer_id, start_date, end_date
        )
        opportunities["ad_variation"] = ad_opps
        
        # Discover account structure opportunities
        structure_opps = await self._discover_structure_opportunities(
            customer_id, start_date, end_date
        )
        opportunities["structure"] = structure_opps
        
        return {
            "opportunities": opportunities,
            "metadata": {
                "customer_id": customer_id,
                "start_date": start_date,
                "end_date": end_date,
                "total_opportunities": sum(len(opportunities[key]) for key in opportunities)
            }
        }
    
    async def _discover_keyword_opportunities(
        self,
        customer_id: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Discover keyword expansion opportunities.
        
        Args:
            customer_id: Google Ads customer ID
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            List of keyword expansion opportunities
        """
        opportunities = []
        
        # Get existing keywords
        existing_keywords = await self.keyword_service.get_keywords(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get search terms
        search_terms = await self.search_term_service.get_search_terms(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Create a set of existing keyword texts
        existing_keyword_texts = set()
        for kw in existing_keywords:
            text = kw.get('text', '').lower()
            if text:
                existing_keyword_texts.add(text)
        
        # Find high-performing search terms that aren't already keywords
        for term in search_terms:
            query = term.get('query', '').lower()
            impressions = term.get('impressions', 0)
            clicks = term.get('clicks', 0)
            cost = term.get('cost', 0)
            conversions = term.get('conversions', 0)
            
            # Skip short or irrelevant queries
            if len(query) < 3 or all(c.isdigit() for c in query):
                continue
                
            # Check if this query is already a keyword
            if query in existing_keyword_texts:
                continue
                
            # Calculate performance metrics
            ctr = clicks / impressions if impressions > 0 else 0
            conversion_rate = conversions / clicks if clicks > 0 else 0
            
            # High-performing search terms
            if (conversions > 0 and clicks >= 5) or (ctr > 0.03 and clicks >= 10):
                campaign_id = term.get('campaign_id', '')
                campaign_name = term.get('campaign_name', 'Unknown')
                ad_group_id = term.get('ad_group_id', '')
                ad_group_name = term.get('ad_group_name', 'Unknown')
                
                opportunities.append({
                    "type": "ADD_KEYWORD_FROM_SEARCH_TERM",
                    "search_term": query,
                    "suggested_match_type": "EXACT",
                    "campaign_id": campaign_id,
                    "campaign_name": campaign_name,
                    "ad_group_id": ad_group_id,
                    "ad_group_name": ad_group_name,
                    "impressions": impressions,
                    "clicks": clicks,
                    "conversions": conversions,
                    "ctr": ctr,
                    "conversion_rate": conversion_rate,
                    "opportunity": f"Add '{query}' as a keyword in ad group '{ad_group_name}'",
                    "impact": "HIGH" if conversions > 0 else "MEDIUM",
                    "action": f"Add '{query}' as an exact match keyword to better control bidding and relevance"
                })
        
        # Sort opportunities by impact and conversions
        return sorted(
            opportunities,
            key=lambda x: (0 if x["impact"] == "HIGH" else 1, -x["conversions"]),
        )
    
    async def _discover_ad_variation_opportunities(
        self,
        customer_id: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Discover ad variation opportunities.
        
        Args:
            customer_id: Google Ads customer ID
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            List of ad variation opportunities
        """
        # This is a simplified placeholder implementation
        # In a real implementation, we would analyze ad performance data
        # to identify opportunities for new ad variations
        
        opportunities = []
        
        # Get ad group data
        ad_groups = await self.ad_group_service.get_ad_groups(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Filter for ad groups with significant traffic but limited ad variations
        for ad_group in ad_groups:
            ad_group_id = ad_group.get('id', '')
            ad_group_name = ad_group.get('name', 'Unknown')
            campaign_id = ad_group.get('campaign_id', '')
            campaign_name = ad_group.get('campaign_name', 'Unknown')
            impressions = ad_group.get('impressions', 0)
            
            # Only suggest for ad groups with significant traffic
            if impressions < 1000:
                continue
                
            # In a real implementation, we would check the number of active ads
            # and suggest new variations for ad groups with only 1-2 ads
            # This is a simplified placeholder
            opportunities.append({
                "type": "CREATE_AD_VARIATION",
                "entity_type": "AD_GROUP",
                "entity_id": ad_group_id,
                "entity_name": ad_group_name,
                "campaign_id": campaign_id,
                "campaign_name": campaign_name,
                "impressions": impressions,
                "opportunity": f"Create additional ad variations for ad group '{ad_group_name}'",
                "impact": "MEDIUM",
                "action": "Add at least one more responsive search ad to test different headlines and descriptions"
            })
        
        return opportunities[:5]  # Limit to top 5 opportunities
    
    async def _discover_structure_opportunities(
        self,
        customer_id: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        Discover account structure opportunities.
        
        Args:
            customer_id: Google Ads customer ID
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            List of account structure opportunities
        """
        # This is a simplified placeholder implementation
        # In a real implementation, we would analyze account structure
        # to identify opportunities for restructuring
        
        opportunities = []
        
        # Get ad group data
        ad_groups = await self.ad_group_service.get_ad_groups(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Map of campaign IDs to lists of ad groups
        campaign_ad_groups = {}
        
        for ad_group in ad_groups:
            campaign_id = ad_group.get('campaign_id', '')
            if campaign_id:
                if campaign_id not in campaign_ad_groups:
                    campaign_ad_groups[campaign_id] = []
                    
                campaign_ad_groups[campaign_id].append(ad_group)
        
        # Check for campaigns with large ad groups that might benefit from splitting
        for campaign_id, ad_group_list in campaign_ad_groups.items():
            if len(ad_group_list) == 0:
                continue
                
            campaign_name = ad_group_list[0].get('campaign_name', 'Unknown')
            
            # Look for ad groups with lots of keywords (simplified in this placeholder)
            for ad_group in ad_group_list:
                ad_group_id = ad_group.get('id', '')
                ad_group_name = ad_group.get('name', 'Unknown')
                
                # In a real implementation, we would check keyword count and themes
                # This is a simplified placeholder
                if ad_group.get('impressions', 0) > 5000:
                    opportunities.append({
                        "type": "SPLIT_LARGE_AD_GROUP",
                        "entity_type": "AD_GROUP",
                        "entity_id": ad_group_id,
                        "entity_name": ad_group_name,
                        "campaign_id": campaign_id,
                        "campaign_name": campaign_name,
                        "opportunity": f"Consider splitting large ad group '{ad_group_name}' into more specific themes",
                        "impact": "MEDIUM",
                        "action": "Review keywords in this ad group and consider reorganizing into more tightly themed ad groups"
                    })
        
        return opportunities 