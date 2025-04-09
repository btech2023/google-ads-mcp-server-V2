"""
MCP Tools Package

This package contains all MCP tools and registration functions.
"""

import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Import registration functions as they become available
from .health import register_health_tools
# Other imports will be uncommented as modules are created
# from .account import register_account_tools
from .campaign import register_campaign_tools
from .ad_group import register_ad_group_tools
from .keyword import register_keyword_tools
from .search_term import register_search_term_tools
from .budget import register_budget_tools
from .dashboard import register_dashboard_tools
from .insights import register_insights_tools

# For backward compatibility (add as needed)
# These are no longer needed as the tools are now just methods within their respective register_* functions
# from .budget import get_budgets, get_budgets_json

def register_tools(mcp, google_ads_service) -> None:
    """
    Register MCP tools.
    
    Args:
        mcp: The MCP server instance
        google_ads_service: The Google Ads service instance
    """
    logger.info("Registering MCP tools")
    
    # Initialize services
    from google_ads.campaigns import CampaignService
    from google_ads.ad_groups import AdGroupService
    from google_ads.keywords import KeywordService
    from google_ads.search_terms import SearchTermService
    from google_ads.budgets import BudgetService
    from google_ads.dashboards import DashboardService
    from google_ads.insights import InsightsService
    
    # Create service instances
    campaign_service = CampaignService(google_ads_service)
    ad_group_service = AdGroupService(google_ads_service)
    keyword_service = KeywordService(google_ads_service)
    search_term_service = SearchTermService(google_ads_service)
    budget_service = BudgetService(google_ads_service)
    dashboard_service = DashboardService(google_ads_service)
    insights_service = InsightsService(google_ads_service)
    
    # Register health tools
    register_health_tools(mcp, google_ads_service)
    
    # Other registrations will be uncommented as modules are created
    # register_account_tools(mcp, google_ads_service)
    register_campaign_tools(mcp, google_ads_service, campaign_service)
    register_ad_group_tools(mcp, google_ads_service, ad_group_service)
    register_keyword_tools(mcp, google_ads_service, keyword_service)
    register_search_term_tools(mcp, google_ads_service, search_term_service)
    register_budget_tools(mcp, google_ads_service, budget_service)
    register_dashboard_tools(mcp, google_ads_service, dashboard_service)
    register_insights_tools(mcp, google_ads_service, insights_service)
    
    logger.info("MCP tools registered successfully") 