"""
MCP Resources Module

This module contains the MCPResources class for handling MCP resource requests.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MCPResources:
    """Class for handling MCP resource requests."""
    
    def __init__(self, google_ads_service):
        """
        Initialize the MCP resources handler.
        
        Args:
            google_ads_service: The Google Ads service instance
        """
        self.google_ads_service = google_ads_service
        logger.info("MCPResources initialized")
    
    async def read_resource(self, uri) -> Dict[str, Any]:
        """
        Read a resource from the Google Ads API.
        
        Args:
            uri: The resource URI
            
        Returns:
            The resource data
            
        Raises:
            ValueError: If the URI scheme or resource type is unsupported
        """
        logger.info(f"Reading resource: {uri}")
        
        # Parse the URI
        parts = uri.path.strip("/").split("/")
        query_params = {}
        
        # Extract query parameters
        for key, value in uri.query.items():
            query_params[key] = value
        
        # Check scheme
        if uri.scheme != "google-ads":
            raise ValueError(f"Unsupported URI scheme: {uri.scheme}")
        
        # Handle different resource types
        if not parts:
            raise ValueError("Resource path is empty")
            
        resource_type = parts[0]
        
        if resource_type == "campaigns":
            return await self._handle_campaign_resource(parts, query_params)
        elif resource_type == "ad_groups":
            return await self._handle_ad_group_resource(parts, query_params)
        elif resource_type == "keywords":
            return await self._handle_keyword_resource(parts, query_params)
        elif resource_type == "performance":
            return await self._handle_performance_resource(parts, query_params)
        elif resource_type == "accounts":
            return await self._handle_account_resource(parts, query_params)
        else:
            raise ValueError(f"Unsupported resource type: {resource_type}")
    
    async def _handle_campaign_resource(self, parts, query_params):
        """
        Handle campaign resource requests.
        
        Args:
            parts: Path parts from the URI
            query_params: Query parameters from the URI
            
        Returns:
            Campaign data
        """
        customer_id = query_params.get("customer_id")
        start_date = query_params.get("start_date")
        end_date = query_params.get("end_date")
        
        if len(parts) == 1:
            # List of all campaigns
            logger.info(f"Getting all campaigns for customer ID {customer_id or 'default'}")
            campaigns = await self.google_ads_service.get_campaigns(start_date, end_date, customer_id)
            return {"campaigns": campaigns}
        elif len(parts) == 2:
            # Single campaign
            campaign_id = parts[1]
            logger.info(f"Getting campaign {campaign_id} for customer ID {customer_id or 'default'}")
            # For now, just filter the list (future: implement get_campaign method)
            campaigns = await self.google_ads_service.get_campaigns(start_date, end_date, customer_id)
            campaign = next((c for c in campaigns if str(c["id"]) == campaign_id), None)
            return {"campaign": campaign} if campaign else {"error": "Campaign not found"}
        else:
            raise ValueError(f"Invalid campaign resource path: {'/'.join(parts)}")
    
    async def _handle_ad_group_resource(self, parts, query_params):
        """
        Handle ad group resource requests.
        
        Args:
            parts: Path parts from the URI
            query_params: Query parameters from the URI
            
        Returns:
            Ad group data
        """
        # Placeholder for now
        return {"message": "Ad group resource handling not yet implemented"}
    
    async def _handle_keyword_resource(self, parts, query_params):
        """
        Handle keyword resource requests.
        
        Args:
            parts: Path parts from the URI
            query_params: Query parameters from the URI
            
        Returns:
            Keyword data
        """
        # Placeholder for now
        return {"message": "Keyword resource handling not yet implemented"}
    
    async def _handle_performance_resource(self, parts, query_params):
        """
        Handle performance resource requests.
        
        Args:
            parts: Path parts from the URI
            query_params: Query parameters from the URI
            
        Returns:
            Performance data
        """
        # Placeholder for now
        return {"message": "Performance resource handling not yet implemented"}
    
    async def _handle_account_resource(self, parts, query_params):
        """
        Handle account resource requests.
        
        Args:
            parts: Path parts from the URI
            query_params: Query parameters from the URI
            
        Returns:
            Account data
        """
        if len(parts) == 1:
            # List of all accounts
            logger.info("Getting all accessible accounts")
            accounts = await self.google_ads_service.list_accessible_accounts()
            return {"accounts": accounts}
        elif len(parts) == 2 and parts[1] == "summary":
            # Account summary
            customer_id = query_params.get("customer_id")
            start_date = query_params.get("start_date")
            end_date = query_params.get("end_date")
            logger.info(f"Getting summary for customer ID {customer_id or 'default'}")
            summary = await self.google_ads_service.get_account_summary(start_date, end_date, customer_id)
            return {"summary": summary}
        elif len(parts) == 2 and parts[1] == "hierarchy":
            # Account hierarchy
            customer_id = query_params.get("customer_id")
            logger.info(f"Getting hierarchy for customer ID {customer_id or 'default'}")
            hierarchy = await self.google_ads_service.get_account_hierarchy(customer_id)
            return {"hierarchy": hierarchy}
        else:
            raise ValueError(f"Invalid account resource path: {'/'.join(parts)}")
