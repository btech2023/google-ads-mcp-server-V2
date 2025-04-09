"""
MCP Tools Module

This module contains functions for registering and handling MCP tools.

NOTE: This file is being migrated to a modular structure.
New modules are being created in the google_ads_mcp_server/mcp/tools/ directory.
Please use the imports from google_ads_mcp_server.mcp.tools package in new code.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from google_ads.campaigns import CampaignService
from google_ads.ad_groups import AdGroupService
from google_ads.keywords import KeywordService
from google_ads.search_terms import SearchTermService
from google_ads.budgets import BudgetService
from google_ads.dashboards import DashboardService
from google_ads.insights import InsightsService
from visualization.formatters import format_for_visualization
from visualization.budgets import format_budget_for_visualization
from visualization.dashboards import create_account_dashboard_visualization, create_campaign_dashboard_visualization
from visualization.comparisons import format_comparison_visualization
from visualization.breakdowns import format_breakdown_visualization
from visualization.insights import format_anomalies_visualization, format_optimization_suggestions_visualization, format_opportunities_visualization, format_insights_visualization

logger = logging.getLogger(__name__)

# Re-export key functions and registration functions from the new module structure
from google_ads_mcp_server.mcp.tools import register_tools as new_register_tools
from google_ads_mcp_server.mcp.tools import get_budgets, get_budgets_json

# Define wrapper function to redirect to the new modular structure
def register_tools(mcp, google_ads_service) -> None:
    """
    Register MCP tools.
    
    This function is now a wrapper that forwards to the new modular implementation.
    
    Args:
        mcp: The MCP server instance
        google_ads_service: The Google Ads service instance
    """
    logger.info("Using modular tools implementation")
    new_register_tools(mcp, google_ads_service)
    
# Keep the original function implementations for backward compatibility
# These will be removed when the migration is complete
# ... existing code follows ...
