"""
Keyword Management Module

This module provides functionality for managing Google Ads keywords.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class KeywordService:
    """Service for managing Google Ads keywords."""
    
    def __init__(self, google_ads_service):
        """
        Initialize the Keyword service.
        
        Args:
            google_ads_service: The Google Ads service instance
        """
        self.google_ads_service = google_ads_service
        self.ga_service = google_ads_service.client.get_service("GoogleAdsService")
        logger.info("KeywordService initialized")
    
    async def get_keywords(self, customer_id: str, ad_group_id: Optional[str] = None, 
                          status_filter: Optional[str] = None, 
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get keywords for a customer, optionally filtered by ad_group_id and status.
        
        Args:
            customer_id: Google Ads customer ID
            ad_group_id: Optional ad group ID to filter by
            status_filter: Optional filter for keyword status (ENABLED, PAUSED, REMOVED)
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            List of keyword data with metrics
        """
        logger.info(f"Getting keywords for customer ID {customer_id}")
        
        # Calculate default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Get data from the Google Ads service
        keywords = await self.google_ads_service.get_keywords(
            start_date=start_date,
            end_date=end_date,
            ad_group_id=ad_group_id,
            status_filter=status_filter,
            customer_id=customer_id
        )
            
        logger.info(f"Retrieved {len(keywords)} keywords")
        return keywords
    
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
    
    async def add_keywords(self, customer_id: str, ad_group_id: str, keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add keywords to an ad group.
        
        Args:
            customer_id: Google Ads customer ID
            ad_group_id: Ad group ID to add keywords to
            keywords: List of keyword specs, each containing:
                - text: Keyword text
                - match_type: Match type (EXACT, PHRASE, BROAD)
                - status: Status (ENABLED, PAUSED)
                - cpc_bid_micros: Optional CPC bid in micros
            
        Returns:
            Dictionary with creation results
        """
        logger.info(f"Adding {len(keywords)} keywords to ad group {ad_group_id}")
        
        # Add keywords using the GoogleAdsService
        result = await self.google_ads_service.add_keywords(
            customer_id=customer_id,
            ad_group_id=ad_group_id,
            keywords=keywords
        )
        
        return result
    
    async def update_keywords(self, customer_id: str, keyword_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update existing keywords.
        
        Args:
            customer_id: Google Ads customer ID
            keyword_updates: List of keyword update specs, each containing:
                - id: Keyword criterion ID
                - status: Optional new status (ENABLED, PAUSED, REMOVED)
                - cpc_bid_micros: Optional new CPC bid in micros
            
        Returns:
            Dictionary with update results
        """
        logger.info(f"Updating {len(keyword_updates)} keywords for customer ID {customer_id}")
        
        # Update keywords using the GoogleAdsService
        result = await self.google_ads_service.update_keywords(
            customer_id=customer_id,
            keyword_updates=keyword_updates
        )
        
        return result
    
    async def remove_keywords(self, customer_id: str, keyword_ids: List[str]) -> Dict[str, Any]:
        """
        Remove keywords (set status to REMOVED).
        
        Args:
            customer_id: Google Ads customer ID
            keyword_ids: List of keyword criterion IDs to remove
            
        Returns:
            Dictionary with removal results
        """
        logger.info(f"Removing {len(keyword_ids)} keywords for customer ID {customer_id}")
        
        # Remove keywords using the GoogleAdsService
        result = await self.google_ads_service.remove_keywords(
            customer_id=customer_id,
            keyword_ids=keyword_ids
        )
        
        return result
