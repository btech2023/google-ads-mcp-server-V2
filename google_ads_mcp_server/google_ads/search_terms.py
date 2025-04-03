"""
Search Term Analysis Module

This module provides functionality for analyzing Google Ads search terms.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SearchTermService:
    """Service for analyzing Google Ads search terms."""
    
    def __init__(self, google_ads_service):
        """
        Initialize the Search Term service.
        
        Args:
            google_ads_service: The Google Ads service instance
        """
        self.google_ads_service = google_ads_service
        self.ga_service = google_ads_service.client.get_service("GoogleAdsService")
        logger.info("SearchTermService initialized")
    
    async def get_search_terms(self, customer_id: str, campaign_id: Optional[str] = None,
                              ad_group_id: Optional[str] = None,
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get search terms report for a customer, optionally filtered by campaign_id and ad_group_id.
        
        Args:
            customer_id: Google Ads customer ID
            campaign_id: Optional campaign ID to filter by
            ad_group_id: Optional ad group ID to filter by
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            List of search term data with metrics
        """
        logger.info(f"Getting search terms for customer ID {customer_id}")
        
        # Calculate default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Get data from the Google Ads service
        search_terms = await self.google_ads_service.get_search_terms_report(
            start_date=start_date,
            end_date=end_date,
            campaign_id=campaign_id,
            ad_group_id=ad_group_id,
            customer_id=customer_id
        )
            
        logger.info(f"Retrieved {len(search_terms)} search terms")
        return search_terms
    
    async def analyze_search_terms(self, customer_id: str, campaign_id: Optional[str] = None,
                                  ad_group_id: Optional[str] = None,
                                  start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze search terms and provide insights.
        
        Args:
            customer_id: Google Ads customer ID
            campaign_id: Optional campaign ID to filter by
            ad_group_id: Optional ad group ID to filter by
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Dictionary with search term analysis and insights
        """
        logger.info(f"Analyzing search terms for customer ID {customer_id}")
        
        # Get search terms data
        search_terms = await self.get_search_terms(
            customer_id=customer_id,
            campaign_id=campaign_id,
            ad_group_id=ad_group_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not search_terms:
            return {
                "total_search_terms": 0,
                "total_impressions": 0,
                "total_clicks": 0,
                "total_cost": 0,
                "total_conversions": 0,
                "average_cpc": 0,
                "average_ctr": 0,
                "average_conversion_rate": 0,
                "top_performing_terms": [],
                "low_performing_terms": [],
                "potential_negative_keywords": []
            }
        
        # Calculate totals
        total_impressions = sum(term["impressions"] for term in search_terms)
        total_clicks = sum(term["clicks"] for term in search_terms)
        total_cost = sum(term["cost"] for term in search_terms)
        total_conversions = sum(term["conversions"] for term in search_terms)
        
        # Calculate averages
        average_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        average_cpc = (total_cost / total_clicks) if total_clicks > 0 else 0
        average_conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        
        # Sort search terms by different metrics
        by_clicks = sorted(search_terms, key=lambda x: x["clicks"], reverse=True)
        by_cost = sorted(search_terms, key=lambda x: x["cost"], reverse=True)
        by_conversions = sorted(search_terms, key=lambda x: x["conversions"], reverse=True)
        by_ctr = sorted(search_terms, key=lambda x: x["ctr"], reverse=True)
        
        # Identify top performing terms (high conversions or high CTR)
        top_performing = []
        for term in by_conversions[:10]:  # Top 10 by conversions
            if term["conversions"] > 0:
                top_performing.append(term)
                
        if len(top_performing) < 5:  # Add more from top CTR if needed
            for term in by_ctr[:10]:
                if term not in top_performing and term["ctr"] > average_ctr * 1.5:
                    top_performing.append(term)
                    if len(top_performing) >= 5:
                        break
        
        # Identify low performing terms (high cost, low conversions)
        low_performing = []
        for term in by_cost[:20]:  # From top 20 by cost
            if term["conversions"] == 0 and term["cost"] > average_cpc * 3:
                low_performing.append(term)
                if len(low_performing) >= 5:
                    break
        
        # Identify potential negative keywords (zero conversions, lots of impressions)
        potential_negatives = []
        for term in search_terms:
            if (term["conversions"] == 0 and 
                term["impressions"] > 100 and 
                term["clicks"] > 10 and 
                term["ctr"] < average_ctr * 0.5):
                potential_negatives.append(term)
                if len(potential_negatives) >= 5:
                    break
        
        return {
            "total_search_terms": len(search_terms),
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_cost": total_cost,
            "total_conversions": total_conversions,
            "average_cpc": average_cpc,
            "average_ctr": average_ctr,
            "average_conversion_rate": average_conversion_rate,
            "top_performing_terms": top_performing[:5],
            "low_performing_terms": low_performing[:5],
            "potential_negative_keywords": potential_negatives[:5]
        } 