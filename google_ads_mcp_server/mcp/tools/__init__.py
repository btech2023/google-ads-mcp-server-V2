"""MCP Tools Package

This package contains all MCP tools and registration functions."""
# flake8: noqa

import logging
import json
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Placeholders for dependency injection in tests
budget_service: Optional[Any] = None

from .health import register_health_tools
from .campaign import register_campaign_tools
from .ad_group import register_ad_group_tools
from .keyword import (
    register_keyword_tools,
    get_keywords,
    get_keywords_json,
    add_keywords,
    update_keyword,
    remove_keywords,
    get_search_terms_report,
    get_search_terms_report_json,
    analyze_search_terms,
    analyze_search_terms_json,
)
from .search_term import register_search_term_tools
from .budget import register_budget_tools
from .dashboard import register_dashboard_tools
from .insights import register_insights_tools

__all__ = [
    "register_tools",
    "get_budgets",
    "get_budgets_json",
    "analyze_budgets",
    "update_budget",
    "get_keywords",
    "get_keywords_json",
    "add_keywords",
    "update_keyword",
    "remove_keywords",
    "get_search_terms_report",
    "get_search_terms_report_json",
    "analyze_search_terms",
    "analyze_search_terms_json",
]


def get_budgets(budget_ids_str: str | None = None, status: str | None = None) -> str:
    """Simplified budget report used in unit tests."""
    ids = [int(i) for i in budget_ids_str.split(",")] if budget_ids_str else None
    budgets = budget_service.get_budgets(budget_ids=ids, status=status)
    if not budgets:
        return "No budgets found matching the criteria."
    lines = ["Budget Report"]
    for b in budgets:
        amount = b.get("amount_micros", 0) / 1_000_000
        lines.append(
            f"ID: {b['id']} Name: {b['name']} Amount: {amount:.2f} Utilization: {b.get('utilization', 0)*100:.1f}%"
        )
    return "\n".join(lines)


def get_budgets_json(budget_ids_str: str | None = None, status: str | None = None) -> str:
    """Return budgets and visualization data as JSON."""
    ids = [int(i) for i in budget_ids_str.split(",")] if budget_ids_str else None
    budgets = budget_service.get_budgets(budget_ids=ids, status=status)
    from google_ads_mcp_server.visualization.budgets import format_budget_for_visualization

    viz = format_budget_for_visualization(budgets)
    return json.dumps({"budgets": budgets, "visualization": viz})


def analyze_budgets(budget_ids_str: str | None = None) -> str:
    """Return a simple textual analysis of budgets."""
    ids = [int(i) for i in budget_ids_str.split(",")] if budget_ids_str else None
    budgets = budget_service.get_budgets(budget_ids=ids, status=None)
    analysis = budget_service.analyze_budget_performance(budgets)

    lines = ["Budget Analysis Report"]
    for item in analysis:
        lines.append(f"Budget: {item['budget_name']} (ID: {item['budget_id']})")
        lines.append(f"Utilization: {item['utilization']*100:.1f}%")
        for insight in item.get("insights", []):
            lines.append(f"- {insight}")
        for rec in item.get("recommendations", []):
            lines.append(f"- {rec}")
    return "\n".join(lines)


def update_budget(budget_id: int, update_json: str) -> str:
    """Apply updates to a budget."""
    try:
        updates = json.loads(update_json)
    except json.JSONDecodeError:
        return "Error: Invalid JSON provided for updates."
    return budget_service.update_budget(budget_id, updates)


def register_tools(mcp, google_ads_service) -> None:
    """Register all MCP tools."""
    logger.info("Registering MCP tools")

    from google_ads.campaigns import CampaignService
    from google_ads.ad_groups import AdGroupService
    from google_ads.keywords import KeywordService
    from google_ads.search_terms import SearchTermService
    from google_ads.budgets import BudgetService
    from google_ads.dashboards import DashboardService
    from google_ads.insights import InsightsService

    campaign_service = CampaignService(google_ads_service)
    ad_group_service = AdGroupService(google_ads_service)
    keyword_service = KeywordService(google_ads_service)
    search_term_service = SearchTermService(google_ads_service)
    global budget_service
    budget_service = BudgetService(google_ads_service)
    dashboard_service = DashboardService(google_ads_service)
    insights_service = InsightsService(google_ads_service)

    register_health_tools(mcp, google_ads_service)
    register_campaign_tools(mcp, google_ads_service, campaign_service)
    register_ad_group_tools(mcp, google_ads_service, ad_group_service)
    register_keyword_tools(mcp, google_ads_service, keyword_service)
    register_search_term_tools(mcp, google_ads_service, search_term_service)
    register_budget_tools(mcp, google_ads_service, budget_service)
    register_dashboard_tools(mcp, google_ads_service, dashboard_service)
    register_insights_tools(mcp, google_ads_service, insights_service)

    logger.info("MCP tools registered successfully")
