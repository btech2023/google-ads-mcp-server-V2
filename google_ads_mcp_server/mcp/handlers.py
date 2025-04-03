"""
MCP Handlers Module

This module contains handlers for MCP request processing and registration.
"""

import logging
from typing import Optional
from fastapi import FastAPI

from mcp.resources import MCPResources
from mcp.tools import register_tools
from server import mcp

logger = logging.getLogger(__name__)

def register_mcp_handlers(app: FastAPI) -> None:
    """
    Register MCP handlers with the FastAPI application.
    
    Args:
        app: The FastAPI application instance
    """
    logger.info("Registering MCP handlers")
    
    # Get Google Ads service from app state
    google_ads_service = app.state.google_ads_service
    
    # Register MCP resources
    mcp_resources = MCPResources(google_ads_service)
    register_resource_handlers(mcp_resources)
    
    # Register MCP tools
    register_tools(mcp, google_ads_service)
    
    logger.info("MCP handlers registered successfully")

def register_resource_handlers(mcp_resources: MCPResources) -> None:
    """
    Register resource handlers with the MCP server.
    
    Args:
        mcp_resources: The MCPResources instance
    """
    @mcp.resource_reader("google-ads")
    async def read_resource(uri, headers: Optional[dict] = None):
        """
        Read Google Ads resources.
        
        Args:
            uri: The resource URI
            headers: Optional request headers
            
        Returns:
            The resource data
        """
        logger.info(f"Reading Google Ads resource: {uri}")
        return await mcp_resources.read_resource(uri)
