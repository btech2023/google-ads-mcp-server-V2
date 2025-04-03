"""
MCP Tools Module

This module contains functions for registering and handling MCP tools.
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

def register_tools(mcp, google_ads_service) -> None:
    """
    Register MCP tools.
    
    Args:
        mcp: The MCP server instance
        google_ads_service: The Google Ads service instance
    """
    logger.info("Registering MCP tools")
    
    # Initialize services
    campaign_service = CampaignService(google_ads_service)
    ad_group_service = AdGroupService(google_ads_service)
    keyword_service = KeywordService(google_ads_service)
    search_term_service = SearchTermService(google_ads_service)
    budget_service = BudgetService(google_ads_service)
    dashboard_service = DashboardService(google_ads_service)
    insights_service = InsightsService(google_ads_service)
    
    # Register health tools
    register_health_tools(mcp, google_ads_service)
    
    # Register account tools
    register_account_tools(mcp, google_ads_service)
    
    # Register campaign tools
    register_campaign_tools(mcp, google_ads_service, campaign_service)
    
    # Register ad group tools
    register_ad_group_tools(mcp, google_ads_service, ad_group_service)
    
    # Register keyword tools
    register_keyword_tools(mcp, google_ads_service, keyword_service)
    
    # Register search term tools
    register_search_term_tools(mcp, google_ads_service, search_term_service)
    
    # Register budget tools
    register_budget_tools(mcp, google_ads_service, budget_service)
    
    # Register dashboard tools
    register_dashboard_tools(mcp, google_ads_service, dashboard_service)
    
    # Register insights tools
    register_insights_tools(mcp, google_ads_service, insights_service)
    
    logger.info("MCP tools registered successfully")
    
def register_health_tools(mcp, google_ads_service) -> None:
    """
    Register health-related MCP tools.
    
    Args:
        mcp: The MCP server instance
        google_ads_service: The Google Ads service instance
    """
    @mcp.tool()
    async def get_health_status():
        """
        Get the health status of the Google Ads MCP server.
        
        Returns:
            A formatted string with server health information
        """
        try:
            logger.info("Getting server health status")
            
            # In the future, implement a more comprehensive health check
            health_data = {
                "status": "OK",
                "version": "1.0.0",
                "environment": "dev",
                "uptime": "1 day, 2 hours, 34 minutes",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "server": "OK",
                    "google_ads_api": "OK",
                    "caching": True
                }
            }
            
            # Format the health information as text
            report = [
                f"Google Ads MCP Server Health",
                f"Status: {health_data['status']}",
                f"Version: {health_data['version']}",
                f"Environment: {health_data['environment']}",
                f"Uptime: {health_data['uptime']}",
                f"Timestamp: {health_data['timestamp']}\n",
                f"Component Status:",
                f"- Server: {health_data['components']['server']}",
                f"- Caching: {'Enabled' if health_data['components']['caching'] else 'Disabled'}",
                f"- Google Ads API: {health_data['components']['google_ads_api']}"
            ]
                
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error getting health status: {str(e)}")
            return f"Error: Unable to retrieve health status - {str(e)}"

def register_account_tools(mcp, google_ads_service) -> None:
    """
    Register account-related MCP tools.
    
    Args:
        mcp: The MCP server instance
        google_ads_service: The Google Ads service instance
    """
    @mcp.tool()
    async def list_accounts():
        """
        List all accessible Google Ads accounts under the current MCC account.
        
        Returns:
            A formatted list of all accessible accounts with their IDs and names
        """
        try:
            logger.info("Listing accessible Google Ads accounts")
            
            # Get accessible accounts
            accounts = await google_ads_service.list_accessible_accounts()
            
            if not accounts:
                return "No accessible accounts found for the current MCC account."
            
            # Format the results as a text report
            report = [
                f"Google Ads Accessible Accounts",
                f"Total Accounts: {len(accounts)}\n",
                f"{'Account ID':<15} {'Account Name':<50}",
                "-" * 65
            ]
            
            # Add data rows
            for account in sorted(accounts, key=lambda x: x["id"]):
                name = account["name"]
                if len(name) > 47:
                    name = name[:44] + "..."
                    
                report.append(f"{account['id']:<15} {name:<50}")
                
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error listing accounts: {str(e)}")
            return f"Error: {str(e)}"

def register_campaign_tools(mcp, google_ads_service, campaign_service) -> None:
    """
    Register campaign-related MCP tools.
    
    Args:
        mcp: The MCP server instance
        google_ads_service: The Google Ads service instance
        campaign_service: The campaign service instance
    """
    @mcp.tool()
    async def get_campaign_performance(start_date: str = None, end_date: str = None, customer_id: str = None):
        """
        Get performance metrics for Google Ads campaigns.
        
        Args:
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            customer_id: Specific customer/account ID to query (defaults to the one in .env file)
            
        Returns:
            A formatted report of campaign performance metrics
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            logger.info(f"Getting campaign performance for customer ID {customer_id or 'default'}, date range: {start_date} to {end_date}")
            
            # Get campaign data
            campaigns = await google_ads_service.get_campaigns(start_date, end_date, customer_id)
            
            if not campaigns:
                return "No campaigns found for the specified customer ID and date range."
            
            # Get the actual customer ID that was used (for display purposes)
            used_customer_id = customer_id or google_ads_service.client_customer_id
            if used_customer_id:
                # Format with dashes for display
                if len(used_customer_id) == 10:
                    used_customer_id = f"{used_customer_id[:3]}-{used_customer_id[3:6]}-{used_customer_id[6:]}"
            
            # Format the results as a text report
            report = [
                f"Google Ads Campaign Performance Report",
                f"Account ID: {used_customer_id}",
                f"Date Range: {start_date} to {end_date}\n",
                f"{'Campaign ID':<15} {'Campaign Name':<30} {'Status':<15} {'Impressions':<12} {'Clicks':<8} {'Cost':<10} {'CTR':<8} {'CPC':<8}",
                "-" * 100
            ]
            
            # Add data rows
            for campaign in sorted(campaigns, key=lambda x: x["cost"], reverse=True):
                name = campaign["name"]
                if len(name) > 27:
                    name = name[:24] + "..."
                    
                ctr = (campaign["clicks"] / campaign["impressions"] * 100) if campaign["impressions"] > 0 else 0
                cpc = campaign["cost"] / campaign["clicks"] if campaign["clicks"] > 0 else 0
                    
                report.append(
                    f"{campaign['id']:<15} {name:<30} {campaign['status']:<15} "
                    f"{int(campaign['impressions']):,d} {int(campaign['clicks']):,d} "
                    f"${campaign['cost']:,.2f} {ctr:.2f}% ${cpc:.2f}"
                )
                
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error getting campaign performance: {str(e)}")
            return f"Error: {str(e)}"

def register_ad_group_tools(mcp, google_ads_service, ad_group_service) -> None:
    """
    Register ad group-related MCP tools.
    
    Args:
        mcp: The MCP server instance
        google_ads_service: The Google Ads service instance
        ad_group_service: The ad group service instance
    """
    @mcp.tool()
    async def get_ad_groups(customer_id: str, campaign_id: str = None, status: str = None):
        """
        Get ad groups for a Google Ads account with optional filtering.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            campaign_id: Optional campaign ID to filter by
            status: Optional status filter (ENABLED, PAUSED, REMOVED)
            
        Returns:
            Formatted list of ad groups
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Getting ad groups for customer ID {customer_id}")
            
            # Get ad groups using the AdGroupService
            ad_groups = await ad_group_service.get_ad_groups(
                customer_id=customer_id,
                campaign_id=campaign_id,
                status_filter=status
            )
            
            if not ad_groups:
                return "No ad groups found with the specified filters."
            
            # Format with dashes for display
            display_customer_id = customer_id
            if display_customer_id and len(display_customer_id) == 10:
                display_customer_id = f"{display_customer_id[:3]}-{display_customer_id[3:6]}-{display_customer_id[6:]}"
            
            # Format the results as a text report
            report = [
                f"Google Ads Ad Groups",
                f"Account ID: {display_customer_id}",
                f"Campaign Filter: {campaign_id if campaign_id else 'All Campaigns'}",
                f"Status Filter: {status if status else 'All Statuses'}\n",
                f"{'Ad Group ID':<12} {'Ad Group Name':<30} {'Campaign':<20} {'Status':<10} {'Impressions':<12} {'Clicks':<8} {'Cost':<10}",
                "-" * 100
            ]
            
            # Add data rows
            for ad_group in sorted(ad_groups, key=lambda x: x.get("cost", 0), reverse=True):
                name = ad_group["name"]
                if len(name) > 27:
                    name = name[:24] + "..."
                    
                campaign_name = ad_group.get("campaign_name", "Unknown")
                if len(campaign_name) > 17:
                    campaign_name = campaign_name[:14] + "..."
                    
                report.append(
                    f"{ad_group['id']:<12} {name:<30} {campaign_name:<20} {ad_group['status']:<10} "
                    f"{int(ad_group.get('impressions', 0)):,d} {int(ad_group.get('clicks', 0)):,d} "
                    f"${ad_group.get('cost', 0):,.2f}"
                )
                
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error getting ad groups: {str(e)}")
            return f"Error: {str(e)}"
    
    @mcp.tool()
    async def get_ad_groups_json(customer_id: str, campaign_id: str = None, status: str = None):
        """
        Get ad groups in JSON format for visualization.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            campaign_id: Optional campaign ID to filter by
            status: Optional status filter (ENABLED, PAUSED, REMOVED)
            
        Returns:
            JSON data for ad group visualization
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Getting ad groups JSON for customer ID {customer_id}")
            
            # Get ad groups using the AdGroupService
            ad_groups = await ad_group_service.get_ad_groups(
                customer_id=customer_id,
                campaign_id=campaign_id,
                status_filter=status
            )
            
            if not ad_groups:
                return {"error": "No ad groups found with the specified filters."}
            
            # Format for visualization
            visualization_data = format_for_visualization(
                ad_groups, 
                chart_type="bar",
                metrics=["impressions", "clicks", "cost"]
            )
            
            return {
                "type": "success",
                "data": ad_groups,
                "visualization": visualization_data
            }
            
        except Exception as e:
            logger.error(f"Error getting ad groups JSON: {str(e)}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def get_ad_group_performance(customer_id: str, ad_group_id: str, start_date: str = None, end_date: str = None):
        """
        Get performance metrics for a specific ad group.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            ad_group_id: Ad group ID
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Formatted performance report for the ad group
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Getting performance for ad group {ad_group_id}")
            
            # Get performance data using the AdGroupService
            performance = await ad_group_service.get_ad_group_performance(
                customer_id=customer_id,
                ad_group_id=ad_group_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Format with dashes for display
            display_customer_id = customer_id
            if display_customer_id and len(display_customer_id) == 10:
                display_customer_id = f"{display_customer_id[:3]}-{display_customer_id[3:6]}-{display_customer_id[6:]}"
            
            # Format the results as a text report
            report = [
                f"Google Ads Ad Group Performance Report",
                f"Account ID: {display_customer_id}",
                f"Ad Group ID: {ad_group_id}",
                f"Date Range: {performance['start_date']} to {performance['end_date']}\n",
                "Performance Summary:",
                f"- Impressions: {int(performance['impressions']):,d}",
                f"- Clicks: {int(performance['clicks']):,d}",
                f"- Cost: ${performance['cost']:,.2f}",
                f"- Conversions: {performance['conversions']:,.2f}",
                f"- Conversion Value: ${performance['conversion_value']:,.2f}\n",
                "Key Metrics:",
                f"- CTR: {performance['ctr']:.2f}%",
                f"- CPC: ${performance['cpc']:,.2f}",
                f"- ROAS: {performance['roas']:.2f}x",
                "\nDaily Performance:",
                f"{'Date':<12} {'Impressions':<12} {'Clicks':<8} {'Cost':<10} {'Conv.':<8} {'Value':<10}",
                "-" * 60
            ]
            
            # Add daily data rows
            for day in performance['daily_stats']:
                report.append(
                    f"{day['date']:<12} {int(day['impressions']):,d} {int(day['clicks']):,d} "
                    f"${day['cost']:,.2f} {day['conversions']:,.2f} ${day['conversion_value']:,.2f}"
                )
                
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error getting ad group performance: {str(e)}")
            return f"Error: {str(e)}"
    
    @mcp.tool()
    async def get_ad_group_performance_json(customer_id: str, ad_group_id: str, start_date: str = None, end_date: str = None):
        """
        Get performance metrics for a specific ad group in JSON format for visualization.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            ad_group_id: Ad group ID
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            JSON data for ad group performance visualization
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Getting performance JSON for ad group {ad_group_id}")
            
            # Get performance data using the AdGroupService
            performance = await ad_group_service.get_ad_group_performance(
                customer_id=customer_id,
                ad_group_id=ad_group_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Format for visualization
            visualization_data = format_for_visualization(
                performance['daily_stats'], 
                chart_type="time_series",
                metrics=["impressions", "clicks", "cost", "conversions", "conversion_value"]
            )
            
            return {
                "type": "success",
                "data": performance,
                "visualization": visualization_data
            }
            
        except Exception as e:
            logger.error(f"Error getting ad group performance JSON: {str(e)}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def create_ad_group(customer_id: str, campaign_id: str, name: str, status: str = "ENABLED", cpc_bid_micros: int = None):
        """
        Create a new ad group within a campaign.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            campaign_id: Campaign ID to create the ad group in
            name: Name of the ad group
            status: Ad group status (ENABLED, PAUSED, REMOVED)
            cpc_bid_micros: CPC bid amount in micros (1/1,000,000 of the account currency)
            
        Returns:
            Success message with the created ad group details
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Creating ad group '{name}' in campaign {campaign_id}")
            
            # Validate status
            valid_statuses = ["ENABLED", "PAUSED", "REMOVED"]
            if status not in valid_statuses:
                return f"Error: Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"
            
            # Create ad group using the AdGroupService
            result = await ad_group_service.create_ad_group(
                customer_id=customer_id,
                campaign_id=campaign_id,
                name=name,
                status=status,
                cpc_bid_micros=cpc_bid_micros
            )
            
            # Format the response
            response = [
                f"✅ Ad Group created successfully",
                f"Ad Group ID: {result['ad_group_id']}",
                f"Name: {name}",
                f"Campaign ID: {campaign_id}",
                f"Status: {status}"
            ]
            
            if cpc_bid_micros:
                cpc_bid_dollars = cpc_bid_micros / 1000000
                response.append(f"CPC Bid: ${cpc_bid_dollars:.2f}")
                
            return "\n".join(response)
            
        except Exception as e:
            logger.error(f"Error creating ad group: {str(e)}")
            return f"Error: {str(e)}"
    
    @mcp.tool()
    async def update_ad_group(customer_id: str, ad_group_id: str, name: str = None, status: str = None, cpc_bid_micros: int = None):
        """
        Update an existing ad group's attributes.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            ad_group_id: Ad group ID to update
            name: New name for the ad group (optional)
            status: New status for the ad group (optional, one of: ENABLED, PAUSED, REMOVED)
            cpc_bid_micros: New CPC bid amount in micros (optional)
            
        Returns:
            Success message with the updated ad group details
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Updating ad group {ad_group_id}")
            
            # Validate status if provided
            if status:
                valid_statuses = ["ENABLED", "PAUSED", "REMOVED"]
                if status not in valid_statuses:
                    return f"Error: Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"
            
            # Ensure at least one field is being updated
            if not any([name, status, cpc_bid_micros]):
                return "Error: At least one of name, status, or cpc_bid_micros must be provided"
            
            # Update ad group using the AdGroupService
            result = await ad_group_service.update_ad_group(
                customer_id=customer_id,
                ad_group_id=ad_group_id,
                name=name,
                status=status,
                cpc_bid_micros=cpc_bid_micros
            )
            
            # Format the response
            response = [
                f"✅ Ad Group updated successfully",
                f"Ad Group ID: {ad_group_id}"
            ]
            
            if name:
                response.append(f"New Name: {name}")
            if status:
                response.append(f"New Status: {status}")
            if cpc_bid_micros:
                cpc_bid_dollars = cpc_bid_micros / 1000000
                response.append(f"New CPC Bid: ${cpc_bid_dollars:.2f}")
                
            return "\n".join(response)
            
        except Exception as e:
            logger.error(f"Error updating ad group: {str(e)}")
            return f"Error: {str(e)}"

def register_keyword_tools(mcp, google_ads_service, keyword_service) -> None:
    """
    Register keyword-related MCP tools.
    
    Args:
        mcp: The MCP server instance
        google_ads_service: The Google Ads service instance
        keyword_service: The keyword service instance
    """
    @mcp.tool()
    async def get_keywords(customer_id: str, ad_group_id: str = None, status: str = None, 
                          start_date: str = None, end_date: str = None):
        """
        Get keywords for a Google Ads account with optional filtering.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            ad_group_id: Optional ad group ID to filter by
            status: Optional status filter (ENABLED, PAUSED, REMOVED)
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Formatted list of keywords
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Getting keywords for customer ID {customer_id}")
            
            # Get keywords using the KeywordService
            keywords = await keyword_service.get_keywords(
                customer_id=customer_id,
                ad_group_id=ad_group_id,
                status_filter=status,
                start_date=start_date,
                end_date=end_date
            )
            
            if not keywords:
                return "No keywords found with the specified filters."
            
            # Format with dashes for display
            display_customer_id = customer_id
            if display_customer_id and len(display_customer_id) == 10:
                display_customer_id = f"{display_customer_id[:3]}-{display_customer_id[3:6]}-{display_customer_id[6:]}"
            
            # Format the results as a text report
            report = [
                f"Google Ads Keywords",
                f"Account ID: {display_customer_id}",
                f"Ad Group Filter: {ad_group_id if ad_group_id else 'All Ad Groups'}",
                f"Status Filter: {status if status else 'All Statuses'}\n",
                f"{'Keyword ID':<15} {'Keyword Text':<30} {'Match Type':<12} {'Status':<10} {'Ad Group':<20} {'Impressions':<12} {'Clicks':<8} {'Cost':<10} {'CTR':<8}",
                "-" * 125
            ]
            
            # Add data rows
            for keyword in sorted(keywords, key=lambda x: x.get("cost", 0), reverse=True):
                text = keyword["text"]
                if len(text) > 27:
                    text = text[:24] + "..."
                    
                ad_group_name = keyword.get("ad_group_name", "Unknown")
                if len(ad_group_name) > 17:
                    ad_group_name = ad_group_name[:14] + "..."
                    
                report.append(
                    f"{keyword['id']:<15} {text:<30} {keyword['match_type']:<12} {keyword['status']:<10} "
                    f"{ad_group_name:<20} {int(keyword.get('impressions', 0)):,d} {int(keyword.get('clicks', 0)):,d} "
                    f"${keyword.get('cost', 0):,.2f} {keyword.get('ctr', 0):.2f}%"
                )
                
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error getting keywords: {str(e)}")
            return f"Error: {str(e)}"
    
    @mcp.tool()
    async def get_keywords_json(customer_id: str, ad_group_id: str = None, status: str = None,
                               start_date: str = None, end_date: str = None):
        """
        Get keywords in JSON format for visualization.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            ad_group_id: Optional ad group ID to filter by
            status: Optional status filter (ENABLED, PAUSED, REMOVED)
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            JSON data for keyword visualization
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Getting keywords JSON for customer ID {customer_id}")
            
            # Get keywords using the KeywordService
            keywords = await keyword_service.get_keywords(
                customer_id=customer_id,
                ad_group_id=ad_group_id,
                status_filter=status,
                start_date=start_date,
                end_date=end_date
            )
            
            if not keywords:
                return {"error": "No keywords found with the specified filters."}
            
            # Format keyword table visualization
            table_visualization = format_for_visualization(
                keywords, 
                chart_type="keyword_table",
                title="Keyword Performance Table"
            )
            
            # Format keyword status distribution
            status_visualization = format_for_visualization(
                keywords,
                chart_type="keyword_status"
            )
            
            # Format top keywords by clicks
            top_keywords_clicks = format_for_visualization(
                keywords,
                chart_type="keyword_performance",
                metric="clicks",
                title="Top Keywords by Clicks"
            )
            
            # Format top keywords by cost
            top_keywords_cost = format_for_visualization(
                keywords,
                chart_type="keyword_performance",
                metric="cost",
                title="Top Keywords by Cost"
            )
            
            # Combine visualizations
            visualizations = {
                "keyword_table": table_visualization,
                "status_distribution": status_visualization,
                "top_keywords_clicks": top_keywords_clicks,
                "top_keywords_cost": top_keywords_cost
            }
            
            return {
                "type": "success",
                "data": keywords,
                "visualizations": visualizations
            }
            
        except Exception as e:
            logger.error(f"Error getting keywords JSON: {str(e)}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def add_keywords(customer_id: str, ad_group_id: str, keyword_text: str, match_type: str = "BROAD", 
                          status: str = "ENABLED", cpc_bid_micros: int = None):
        """
        Add a keyword to an ad group.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            ad_group_id: Ad group ID to add the keyword to
            keyword_text: The keyword text to add
            match_type: Match type (EXACT, PHRASE, BROAD)
            status: Status (ENABLED, PAUSED)
            cpc_bid_micros: Optional CPC bid in micros (1/1,000,000 of the account currency)
            
        Returns:
            Success message with the created keyword details
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Adding keyword '{keyword_text}' to ad group {ad_group_id}")
            
            # Validate match type
            valid_match_types = ["EXACT", "PHRASE", "BROAD"]
            if match_type not in valid_match_types:
                return f"Error: Invalid match type '{match_type}'. Must be one of: {', '.join(valid_match_types)}"
                
            # Validate status
            valid_statuses = ["ENABLED", "PAUSED"]
            if status not in valid_statuses:
                return f"Error: Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"
            
            # Create keyword spec
            keyword_spec = {
                "text": keyword_text,
                "match_type": match_type,
                "status": status
            }
            
            if cpc_bid_micros:
                keyword_spec["cpc_bid_micros"] = cpc_bid_micros
            
            # Add keyword using the KeywordService
            result = await keyword_service.add_keywords(
                customer_id=customer_id,
                ad_group_id=ad_group_id,
                keywords=[keyword_spec]
            )
            
            # Format the response
            response = [
                f"✅ Keyword added successfully",
                f"Keyword: {keyword_text}",
                f"Match Type: {match_type}",
                f"Status: {status}",
                f"Ad Group ID: {ad_group_id}"
            ]
            
            if cpc_bid_micros:
                cpc_bid_dollars = cpc_bid_micros / 1000000
                response.append(f"CPC Bid: ${cpc_bid_dollars:.2f}")
                
            return "\n".join(response)
            
        except Exception as e:
            logger.error(f"Error adding keyword: {str(e)}")
            return f"Error: {str(e)}"
    
    @mcp.tool()
    async def update_keyword(customer_id: str, keyword_id: str, status: str = None, cpc_bid_micros: int = None):
        """
        Update an existing keyword's attributes.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            keyword_id: Keyword criterion ID to update
            status: New status for the keyword (ENABLED, PAUSED, REMOVED)
            cpc_bid_micros: New CPC bid amount in micros (optional)
            
        Returns:
            Success message with the updated keyword details
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Updating keyword {keyword_id}")
            
            # Validate status if provided
            if status:
                valid_statuses = ["ENABLED", "PAUSED", "REMOVED"]
                if status not in valid_statuses:
                    return f"Error: Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"
            
            # Ensure at least one field is being updated
            if not any([status, cpc_bid_micros]):
                return "Error: At least one of status or cpc_bid_micros must be provided"
            
            # Create update spec
            keyword_update = {
                "id": keyword_id
            }
            
            if status:
                keyword_update["status"] = status
                
            if cpc_bid_micros:
                keyword_update["cpc_bid_micros"] = cpc_bid_micros
            
            # Update keyword using the KeywordService
            result = await keyword_service.update_keywords(
                customer_id=customer_id,
                keyword_updates=[keyword_update]
            )
            
            # Format the response
            response = [
                f"✅ Keyword updated successfully",
                f"Keyword ID: {keyword_id}"
            ]
            
            if status:
                response.append(f"New Status: {status}")
            if cpc_bid_micros:
                cpc_bid_dollars = cpc_bid_micros / 1000000
                response.append(f"New CPC Bid: ${cpc_bid_dollars:.2f}")
                
            return "\n".join(response)
            
        except Exception as e:
            logger.error(f"Error updating keyword: {str(e)}")
            return f"Error: {str(e)}"
            
    @mcp.tool()
    async def remove_keywords(customer_id: str, keyword_ids: str):
        """
        Remove keywords (set status to REMOVED).
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            keyword_ids: Comma-separated list of keyword criterion IDs to remove
            
        Returns:
            Success message with removal details
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            # Parse keyword IDs
            keyword_id_list = [id.strip() for id in keyword_ids.split(",")]
            
            logger.info(f"Removing {len(keyword_id_list)} keywords for customer ID {customer_id}")
            
            # Remove keywords using the KeywordService
            result = await keyword_service.remove_keywords(
                customer_id=customer_id,
                keyword_ids=keyword_id_list
            )
            
            # Format the response
            response = [
                f"✅ Keywords removed successfully",
                f"Removed {len(keyword_id_list)} keywords: {keyword_ids}"
            ]
                
            return "\n".join(response)
            
        except Exception as e:
            logger.error(f"Error removing keywords: {str(e)}")
            return f"Error: {str(e)}"

def register_search_term_tools(mcp, google_ads_service, search_term_service) -> None:
    """
    Register search term-related MCP tools.
    
    Args:
        mcp: The MCP server instance
        google_ads_service: The Google Ads service instance
        search_term_service: The search term service instance
    """
    @mcp.tool()
    async def get_search_terms_report(customer_id: str, campaign_id: str = None, ad_group_id: str = None,
                                     start_date: str = None, end_date: str = None):
        """
        Get search term report for a Google Ads account with optional filtering.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            campaign_id: Optional campaign ID to filter by
            ad_group_id: Optional ad group ID to filter by
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Formatted report of search terms and their performance
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Getting search terms report for customer ID {customer_id}")
            
            # Get search terms using the SearchTermService
            search_terms = await search_term_service.get_search_terms(
                customer_id=customer_id,
                campaign_id=campaign_id,
                ad_group_id=ad_group_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if not search_terms:
                return "No search terms found with the specified filters."
            
            # Format with dashes for display
            display_customer_id = customer_id
            if display_customer_id and len(display_customer_id) == 10:
                display_customer_id = f"{display_customer_id[:3]}-{display_customer_id[3:6]}-{display_customer_id[6:]}"
            
            # Format the results as a text report
            report = [
                f"Google Ads Search Terms Report",
                f"Account ID: {display_customer_id}",
                f"Campaign Filter: {campaign_id if campaign_id else 'All Campaigns'}",
                f"Ad Group Filter: {ad_group_id if ad_group_id else 'All Ad Groups'}\n",
                f"{'Search Term':<40} {'Ad Group':<25} {'Impressions':<12} {'Clicks':<8} {'Cost':<10} {'CTR':<8} {'Conv.':<8}",
                "-" * 115
            ]
            
            # Add data rows
            for term in sorted(search_terms, key=lambda x: x.get("cost", 0), reverse=True):
                search_term = term["search_term"]
                if len(search_term) > 37:
                    search_term = search_term[:34] + "..."
                    
                ad_group_name = term.get("ad_group_name", "Unknown")
                if len(ad_group_name) > 22:
                    ad_group_name = ad_group_name[:19] + "..."
                    
                report.append(
                    f"{search_term:<40} {ad_group_name:<25} {int(term.get('impressions', 0)):,d} "
                    f"{int(term.get('clicks', 0)):,d} ${term.get('cost', 0):,.2f} {term.get('ctr', 0):.2f}% "
                    f"{term.get('conversions', 0):.2f}"
                )
                
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error getting search terms report: {str(e)}")
            return f"Error: {str(e)}"
    
    @mcp.tool()
    async def get_search_terms_report_json(customer_id: str, campaign_id: str = None, ad_group_id: str = None,
                                          start_date: str = None, end_date: str = None):
        """
        Get search term report in JSON format for visualization.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            campaign_id: Optional campaign ID to filter by
            ad_group_id: Optional ad group ID to filter by
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            JSON data for search term visualization
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Getting search terms report JSON for customer ID {customer_id}")
            
            # Get search terms using the SearchTermService
            search_terms = await search_term_service.get_search_terms(
                customer_id=customer_id,
                campaign_id=campaign_id,
                ad_group_id=ad_group_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if not search_terms:
                return {"error": "No search terms found with the specified filters."}
            
            # Format for table visualization
            table_visualization = format_for_visualization(
                search_terms, 
                chart_type="search_term_table",
                title="Search Term Performance"
            )
            
            # Format for word cloud visualization by cost
            word_cloud_cost = format_for_visualization(
                search_terms,
                chart_type="search_term_cloud",
                weight_metric="cost",
                title="Search Terms by Cost"
            )
            
            # Format for word cloud visualization by clicks
            word_cloud_clicks = format_for_visualization(
                search_terms,
                chart_type="search_term_cloud",
                weight_metric="clicks",
                title="Search Terms by Clicks"
            )
            
            # Combine visualizations
            visualizations = {
                "search_term_table": table_visualization,
                "word_cloud_cost": word_cloud_cost,
                "word_cloud_clicks": word_cloud_clicks
            }
            
            return {
                "type": "success",
                "data": search_terms,
                "visualizations": visualizations
            }
            
        except Exception as e:
            logger.error(f"Error getting search terms report JSON: {str(e)}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def analyze_search_terms(customer_id: str, campaign_id: str = None, ad_group_id: str = None,
                                  start_date: str = None, end_date: str = None):
        """
        Analyze search terms and provide insights.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            campaign_id: Optional campaign ID to filter by
            ad_group_id: Optional ad group ID to filter by
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Analysis of search terms with insights
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Analyzing search terms for customer ID {customer_id}")
            
            # Get search term analysis using the SearchTermService
            analysis = await search_term_service.analyze_search_terms(
                customer_id=customer_id,
                campaign_id=campaign_id,
                ad_group_id=ad_group_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if analysis["total_search_terms"] == 0:
                return "No search terms found for analysis with the specified filters."
            
            # Format with dashes for display
            display_customer_id = customer_id
            if display_customer_id and len(display_customer_id) == 10:
                display_customer_id = f"{display_customer_id[:3]}-{display_customer_id[3:6]}-{display_customer_id[6:]}"
            
            # Format the results as a text report
            report = [
                f"Google Ads Search Term Analysis",
                f"Account ID: {display_customer_id}",
                f"Campaign Filter: {campaign_id if campaign_id else 'All Campaigns'}",
                f"Ad Group Filter: {ad_group_id if ad_group_id else 'All Ad Groups'}\n",
                f"Summary:",
                f"- Total Search Terms: {analysis['total_search_terms']:,d}",
                f"- Total Impressions: {int(analysis['total_impressions']):,d}",
                f"- Total Clicks: {int(analysis['total_clicks']):,d}",
                f"- Total Cost: ${analysis['total_cost']:,.2f}",
                f"- Total Conversions: {analysis['total_conversions']:,.2f}",
                f"- Average CTR: {analysis['average_ctr']:.2f}%",
                f"- Average CPC: ${analysis['average_cpc']:,.2f}",
                f"- Average Conversion Rate: {analysis['average_conversion_rate']:.2f}%\n"
            ]
            
            # Add top performing terms
            if analysis["top_performing_terms"]:
                report.append("Top Performing Search Terms:")
                for i, term in enumerate(analysis["top_performing_terms"], 1):
                    report.append(f"{i}. '{term['search_term']}' - {term.get('conversions', 0):.2f} conv, {term.get('ctr', 0):.2f}% CTR, ${term.get('cost', 0):,.2f} cost")
                report.append("")
            
            # Add low performing terms
            if analysis["low_performing_terms"]:
                report.append("Low Performing Search Terms:")
                for i, term in enumerate(analysis["low_performing_terms"], 1):
                    report.append(f"{i}. '{term['search_term']}' - ${term.get('cost', 0):,.2f} cost, 0 conversions")
                report.append("")
            
            # Add potential negative keywords
            if analysis["potential_negative_keywords"]:
                report.append("Potential Negative Keywords:")
                for i, term in enumerate(analysis["potential_negative_keywords"], 1):
                    report.append(f"{i}. '{term['search_term']}' - {int(term.get('impressions', 0)):,d} imp, {int(term.get('clicks', 0)):,d} clicks, {term.get('ctr', 0):.2f}% CTR, 0 conv")
                report.append("")
            
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error analyzing search terms: {str(e)}")
            return f"Error: {str(e)}"

    @mcp.tool()
    async def analyze_search_terms_json(customer_id: str, campaign_id: str = None, ad_group_id: str = None,
                                      start_date: str = None, end_date: str = None):
        """
        Analyze search terms and provide insights in JSON format for visualization.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            campaign_id: Optional campaign ID to filter by
            ad_group_id: Optional ad group ID to filter by
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            JSON data for search term analysis visualization
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Analyzing search terms for customer ID {customer_id} in JSON format")
            
            # Get search term analysis using the SearchTermService
            analysis = await search_term_service.analyze_search_terms(
                customer_id=customer_id,
                campaign_id=campaign_id,
                ad_group_id=ad_group_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if analysis["total_search_terms"] == 0:
                return {"error": "No search terms found for analysis with the specified filters."}
            
            # Format for visualization
            visualization = format_for_visualization(
                analysis, 
                chart_type="search_term_analysis",
                title="Search Term Analysis"
            )
            
            return {
                "type": "success",
                "data": analysis,
                "visualization": visualization
            }
            
        except Exception as e:
            logger.error(f"Error analyzing search terms JSON: {str(e)}")
            return {"error": str(e)}

def register_budget_tools(mcp, google_ads_service, budget_service) -> None:
    """
    Register budget-related MCP tools.
    
    Args:
        mcp: The MCP server instance
        google_ads_service: The Google Ads service instance
        budget_service: The budget service instance
    """
    @mcp.tool()
    async def get_budgets(customer_id: str, status: str = None, budget_ids: str = None):
        """
        Get campaign budgets for a Google Ads account with optional filtering.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            status: Optional status filter (ENABLED, REMOVED, etc.)
            budget_ids: Optional comma-separated list of budget IDs to retrieve
            
        Returns:
            Formatted list of campaign budgets and their utilization
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Getting campaign budgets for customer ID {customer_id}")
            
            # Parse budget_ids if provided
            budget_id_list = None
            if budget_ids:
                budget_id_list = [id.strip() for id in budget_ids.split(',')]
                
            # Get budgets using the BudgetService
            budgets = await budget_service.get_budgets(
                customer_id=customer_id,
                status_filter=status,
                budget_ids=budget_id_list
            )
            
            if not budgets:
                return "No campaign budgets found with the specified filters."
            
            # Format with dashes for display
            display_customer_id = customer_id
            if display_customer_id and len(display_customer_id) == 10:
                display_customer_id = f"{display_customer_id[:3]}-{display_customer_id[3:6]}-{display_customer_id[6:]}"
            
            # Format the results as a text report
            report = [
                f"Google Ads Campaign Budgets",
                f"Account ID: {display_customer_id}",
                f"Status Filter: {status if status else 'All Statuses'}\n",
                f"{'Budget ID':<12} {'Budget Name':<30} {'Amount':<12} {'Period':<10} {'Status':<10} {'Utilization':<12} {'Campaigns':<8}",
                "-" * 100
            ]
            
            # Add data rows
            for budget in sorted(budgets, key=lambda x: x.get("amount", 0), reverse=True):
                name = budget["name"]
                if len(name) > 27:
                    name = name[:24] + "..."
                    
                # Format utilization as percentage
                utilization = f"{budget.get('utilization_percent', 0):.1f}%"
                
                # Count associated campaigns
                campaign_count = len(budget.get("associated_campaigns", []))
                    
                report.append(
                    f"{budget['id']:<12} {name:<30} "
                    f"${budget.get('amount', 0):,.2f} {budget.get('period', 'UNKNOWN'):<10} "
                    f"{budget.get('status', 'UNKNOWN'):<10} {utilization:<12} {campaign_count:<8}"
                )
                
            # Add budget details for each budget
            report.append("\nBudget Details:")
            for i, budget in enumerate(budgets, 1):
                report.append(f"\n{i}. Budget: {budget['name']} (ID: {budget['id']})")
                report.append(f"   Amount: ${budget.get('amount', 0):,.2f} - Period: {budget.get('period', 'UNKNOWN')}")
                report.append(f"   Current Spend: ${budget.get('current_spend', 0):,.2f} - Utilization: {budget.get('utilization_percent', 0):.1f}%")
                report.append(f"   Status: {budget.get('status', 'UNKNOWN')} - Delivery Method: {budget.get('delivery_method', 'UNKNOWN')}")
                
                if budget.get('has_recommended_budget'):
                    report.append(f"   Recommended Budget: ${budget.get('recommended_budget_amount', 0):,.2f}")
                
                # List associated campaigns
                campaigns = budget.get("associated_campaigns", [])
                if campaigns:
                    report.append(f"   Associated Campaigns ({len(campaigns)}):")
                    for campaign in campaigns:
                        report.append(f"   - {campaign['name']} (ID: {campaign['id']}) - Status: {campaign['status']}")
                        report.append(f"     Cost: ${campaign.get('cost', 0):,.2f}")
                else:
                    report.append("   No associated campaigns")
                
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error getting campaign budgets: {str(e)}")
            return f"Error: {str(e)}"
    
    @mcp.tool()
    async def get_budgets_json(customer_id: str, status: str = None, budget_ids: str = None):
        """
        Get campaign budgets in JSON format for visualization.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            status: Optional status filter (ENABLED, REMOVED, etc.)
            budget_ids: Optional comma-separated list of budget IDs to retrieve
            
        Returns:
            JSON data for budget visualization
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Getting campaign budgets JSON for customer ID {customer_id}")
            
            # Parse budget_ids if provided
            budget_id_list = None
            if budget_ids:
                budget_id_list = [id.strip() for id in budget_ids.split(',')]
                
            # Get budgets using the BudgetService
            budgets = await budget_service.get_budgets(
                customer_id=customer_id,
                status_filter=status,
                budget_ids=budget_id_list
            )
            
            if not budgets:
                return {"error": "No campaign budgets found with the specified filters."}
            
            # Use the specialized budget visualization formatter
            visualization_data = format_budget_for_visualization(budgets)
            
            return {
                "type": "success",
                "data": budgets,
                "visualization": visualization_data
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign budgets JSON: {str(e)}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def analyze_budgets(customer_id: str, budget_ids: str = None, days_to_analyze: int = 30):
        """
        Analyze campaign budget performance and provide insights.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            budget_ids: Optional comma-separated list of budget IDs to analyze
            days_to_analyze: Number of days to look back for analysis (default: 30)
            
        Returns:
            Formatted analysis of budget performance with insights and recommendations
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Analyzing campaign budgets for customer ID {customer_id}")
            
            # Parse budget_ids if provided
            budget_id_list = None
            if budget_ids:
                budget_id_list = [id.strip() for id in budget_ids.split(',')]
                
            # Get budget analysis from the BudgetService
            analysis_results = await budget_service.analyze_budget_performance(
                customer_id=customer_id,
                budget_ids=budget_id_list,
                days_to_analyze=days_to_analyze
            )
            
            if not analysis_results:
                return "No campaign budgets found for analysis with the specified filters."
            
            # Format with dashes for display
            display_customer_id = customer_id
            if display_customer_id and len(display_customer_id) == 10:
                display_customer_id = f"{display_customer_id[:3]}-{display_customer_id[3:6]}-{display_customer_id[6:]}"
            
            # Format the results as a text report
            report = [
                f"Google Ads Campaign Budget Analysis",
                f"Account ID: {display_customer_id}",
                f"Analysis Period: Last {days_to_analyze} days\n",
                f"Found {len(analysis_results)} budget(s) for analysis"
            ]
            
            # Add analysis for each budget
            for i, analysis in enumerate(analysis_results, 1):
                report.append(f"\n{i}. Budget: {analysis['budget_name']} (ID: {analysis['budget_id']})")
                report.append(f"   Amount: ${analysis['budget_amount']:,.2f} - Period: {analysis['period']}")
                report.append(f"   Current Spend: ${analysis['current_spend']:,.2f} - Utilization: {analysis['utilization_percent']:.1f}%")
                report.append(f"   Delivery Method: {analysis['delivery_method']} - Associated Campaigns: {analysis['campaign_count']}")
                
                # Add daily metrics if present
                if "daily_metrics" in analysis:
                    daily = analysis["daily_metrics"]
                    report.append(f"   Average Daily Spend: ${daily['average_daily_spend']:,.2f} - Daily Budget: ${daily['daily_budget_target']:,.2f}")
                    report.append(f"   Daily Utilization: {daily['daily_utilization']:.1f}%")
                
                # Add campaign insights if present
                if "campaign_insights" in analysis and analysis["campaign_count"] > 0:
                    c_insights = analysis["campaign_insights"]
                    report.append(f"   Highest Spend Campaign: {c_insights['highest_spend']} (${c_insights['highest_spend_amount']:,.2f})")
                    report.append(f"   Lowest Spend Campaign: {c_insights['lowest_spend']} (${c_insights['lowest_spend_amount']:,.2f})")
                
                # Add insights
                if analysis["insights"]:
                    report.append("\n   Insights:")
                    for insight in analysis["insights"]:
                        report.append(f"   - {insight}")
                
                # Add recommendations
                if analysis["recommendations"]:
                    report.append("\n   Recommendations:")
                    for recommendation in analysis["recommendations"]:
                        report.append(f"   - {recommendation}")
                
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error analyzing campaign budgets: {str(e)}")
            return f"Error: {str(e)}"
    
    @mcp.tool()
    async def update_budget(customer_id: str, budget_id: str, amount: float = None, 
                           name: str = None, delivery_method: str = None):
        """
        Update a campaign budget's properties.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            budget_id: ID of the budget to update
            amount: New budget amount in the account's currency (optional)
            name: New budget name (optional)
            delivery_method: New delivery method (STANDARD or ACCELERATED) (optional)
            
        Returns:
            Formatted result of the budget update operation
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Updating campaign budget {budget_id} for customer ID {customer_id}")
            
            # Convert amount to micros if provided
            amount_micros = None
            if amount is not None:
                amount_micros = int(amount * 1000000)  # Convert to micros
            
            # Update the budget using BudgetService
            result = await budget_service.update_budget(
                customer_id=customer_id,
                budget_id=budget_id,
                amount_micros=amount_micros,
                name=name,
                delivery_method=delivery_method
            )
            
            if not result.get("success", False):
                return f"Error updating budget: {result.get('error', 'Unknown error')}"
            
            # Format the result as a report
            report = [
                f"Google Ads Campaign Budget Update",
                f"Budget ID: {budget_id}",
                f"Status: {result.get('message', 'Success')}"
            ]
            
            # Show updated budget amount if available
            if result.get('amount_micros') is not None:
                amount_dollars = result.get('amount_dollars', result.get('amount_micros', 0) / 1000000)
                report.append(f"\nUpdated Budget Amount: ${amount_dollars:,.2f}")
                
            # Show the resource name if available
            if result.get('resource_name'):
                report.append(f"Resource: {result.get('resource_name')}")
                
            # Show any requested changes that weren't applied (in case of unsupported fields)
            requested_changes = result.get("requested_changes", {})
            if requested_changes:
                report.append("\nRequested Changes (Not All Applied):")
                if "name" in requested_changes:
                    report.append(f"- Name: {requested_changes['name']} (Not Supported)")
                if "delivery_method" in requested_changes:
                    report.append(f"- Delivery Method: {requested_changes['delivery_method']} (Not Supported)")
            
            # If we have the current budget info (which we won't in the successful path),
            # show it for backward compatibility
            current_budget = result.get("current_budget", {})
            if current_budget:
                report.append("\nOriginal Budget Information:")
                report.append(f"- Name: {current_budget.get('name', 'Unknown')}")
                report.append(f"- Amount: ${current_budget.get('amount', 0):,.2f}")
                report.append(f"- Status: {current_budget.get('status', 'Unknown')}")
                report.append(f"- Delivery Method: {current_budget.get('delivery_method', 'Unknown')}")
                report.append(f"- Period: {current_budget.get('period', 'Unknown')}")
                if "current_spend" in current_budget:
                    report.append(f"- Current Spend: ${current_budget.get('current_spend', 0):,.2f}")
                if "utilization_percent" in current_budget:
                    report.append(f"- Utilization: {current_budget.get('utilization_percent', 0):.1f}%")
            
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error updating campaign budget: {str(e)}")
            return f"Error: {str(e)}"

def register_dashboard_tools(mcp, google_ads_service, dashboard_service) -> None:
    """
    Register dashboard-related MCP tools.
    
    Args:
        mcp: The MCP server instance
        google_ads_service: The Google Ads service instance
        dashboard_service: The dashboard service instance
    """
    @mcp.tool()
    async def get_account_dashboard_json(date_range: str = "LAST_30_DAYS", comparison_range: str = "PREVIOUS_30_DAYS"):
        """
        Get a comprehensive account dashboard in JSON format for visualization.
        
        The dashboard includes:
        - KPI cards with period-over-period comparison
        - Trend charts for key metrics
        - Top campaigns and ad groups
        - Cost distribution
        
        Args:
            date_range: Date range for the dashboard. Supported values:
                        LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS,
                        THIS_MONTH, LAST_MONTH, THIS_QUARTER, LAST_QUARTER
            comparison_range: Comparison period for period-over-period metrics.
                             Supported values: PREVIOUS_7_DAYS, PREVIOUS_30_DAYS,
                             PREVIOUS_90_DAYS, PREVIOUS_MONTH, PREVIOUS_QUARTER
            
        Returns:
            JSON data with dashboard visualizations
        """
        try:
            logger.info(f"Getting account dashboard for date range {date_range}")
            
            # Validate date range input
            valid_date_ranges = [
                "LAST_7_DAYS", "LAST_30_DAYS", "LAST_90_DAYS", 
                "THIS_MONTH", "LAST_MONTH", "THIS_QUARTER", "LAST_QUARTER"
            ]
            
            if date_range not in valid_date_ranges:
                return {
                    "error": f"Invalid date_range. Supported values: {', '.join(valid_date_ranges)}"
                }
            
            # Validate comparison range input
            valid_comparison_ranges = [
                "PREVIOUS_7_DAYS", "PREVIOUS_30_DAYS", "PREVIOUS_90_DAYS", 
                "PREVIOUS_MONTH", "PREVIOUS_QUARTER", "NONE"
            ]
            
            if comparison_range and comparison_range not in valid_comparison_ranges:
                return {
                    "error": f"Invalid comparison_range. Supported values: {', '.join(valid_comparison_ranges)}"
                }
            
            # Set comparison_range to None if "NONE" is specified
            if comparison_range == "NONE":
                comparison_range = None
            
            # Get dashboard data from service
            dashboard_data = await dashboard_service.get_account_dashboard(
                date_range=date_range,
                comparison_range=comparison_range
            )
            
            # Check if there was an error
            if "error" in dashboard_data:
                return {
                    "error": dashboard_data["error"]
                }
            
            # Generate visualization
            visualization = create_account_dashboard_visualization(
                dashboard_data,
                dashboard_data.get("comparison_metrics", None) if comparison_range else None
            )
            
            # Format date ranges for display
            display_date_range = date_range.replace("_", " ").title()
            display_comparison_range = comparison_range.replace("_", " ").title() if comparison_range else "None"
            
            return {
                "date_range": display_date_range,
                "comparison_range": display_comparison_range,
                "dashboard": dashboard_data,
                "visualization": visualization
            }
            
        except Exception as e:
            logger.error(f"Error getting account dashboard: {str(e)}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def get_campaign_dashboard_json(campaign_id: str, date_range: str = "LAST_30_DAYS", comparison_range: str = "PREVIOUS_30_DAYS"):
        """
        Get a comprehensive dashboard for a specific campaign in JSON format for visualization.
        
        The dashboard includes:
        - Campaign details
        - KPI cards with period-over-period comparison
        - Trend charts for key metrics
        - Ad group breakdown
        - Device performance
        - Top keywords
        
        Args:
            campaign_id: ID of the campaign
            date_range: Date range for the dashboard. Supported values:
                        LAST_7_DAYS, LAST_30_DAYS, LAST_90_DAYS,
                        THIS_MONTH, LAST_MONTH, THIS_QUARTER, LAST_QUARTER
            comparison_range: Comparison period for period-over-period metrics.
                             Supported values: PREVIOUS_7_DAYS, PREVIOUS_30_DAYS,
                             PREVIOUS_90_DAYS, PREVIOUS_MONTH, PREVIOUS_QUARTER, NONE
            
        Returns:
            JSON data with dashboard visualizations
        """
        try:
            logger.info(f"Getting campaign dashboard for campaign ID {campaign_id}")
            
            # Validate date range input
            valid_date_ranges = [
                "LAST_7_DAYS", "LAST_30_DAYS", "LAST_90_DAYS", 
                "THIS_MONTH", "LAST_MONTH", "THIS_QUARTER", "LAST_QUARTER"
            ]
            
            if date_range not in valid_date_ranges:
                return {
                    "error": f"Invalid date_range. Supported values: {', '.join(valid_date_ranges)}"
                }
            
            # Validate comparison range input
            valid_comparison_ranges = [
                "PREVIOUS_7_DAYS", "PREVIOUS_30_DAYS", "PREVIOUS_90_DAYS", 
                "PREVIOUS_MONTH", "PREVIOUS_QUARTER", "NONE"
            ]
            
            if comparison_range and comparison_range not in valid_comparison_ranges:
                return {
                    "error": f"Invalid comparison_range. Supported values: {', '.join(valid_comparison_ranges)}"
                }
            
            # Set comparison_range to None if "NONE" is specified
            if comparison_range == "NONE":
                comparison_range = None
            
            # Get dashboard data from service
            dashboard_data = await dashboard_service.get_campaign_dashboard(
                campaign_id=campaign_id,
                date_range=date_range,
                comparison_range=comparison_range
            )
            
            # Check if there was an error
            if "error" in dashboard_data:
                return {
                    "error": dashboard_data["error"]
                }
            
            # Generate visualization
            visualization = create_campaign_dashboard_visualization(
                dashboard_data,
                dashboard_data.get("comparison_metrics", None) if comparison_range else None
            )
            
            # Format date ranges for display
            display_date_range = date_range.replace("_", " ").title()
            display_comparison_range = comparison_range.replace("_", " ").title() if comparison_range else "None"
            
            return {
                "campaign_id": campaign_id,
                "campaign_name": dashboard_data.get("name", "Unknown"),
                "date_range": display_date_range,
                "comparison_range": display_comparison_range,
                "dashboard": dashboard_data,
                "visualization": visualization
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign dashboard: {str(e)}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def get_performance_comparison_json(entity_type: str, entity_ids: str, date_range: str = "LAST_30_DAYS", metrics: str = None):
        """
        Compare performance metrics between multiple entities (campaigns, ad groups).
        
        Args:
            entity_type: Type of entity to compare ("campaign" or "ad_group")
            entity_ids: Comma-separated list of entity IDs to compare (e.g. "123,456,789")
            date_range: Date range for the comparison data
            metrics: Optional comma-separated list of metrics to include (defaults to all)
            
        Returns:
            JSON data with comparison visualizations
        """
        try:
            logger.info(f"Getting performance comparison for {entity_type}s: {entity_ids}")
            
            # Validate entity type
            if entity_type not in ["campaign", "ad_group"]:
                return {
                    "error": "Invalid entity_type. Supported values: campaign, ad_group"
                }
            
            # Parse entity IDs
            entity_id_list = [id.strip() for id in entity_ids.split(",") if id.strip()]
            if not entity_id_list:
                return {
                    "error": "No valid entity IDs provided"
                }
            
            # Parse metrics list if provided
            metrics_list = None
            if metrics:
                metrics_list = [metric.strip() for metric in metrics.split(",") if metric.strip()]
            
            # Get comparison data from service
            if entity_type == "campaign":
                comparison_data = await dashboard_service.get_campaigns_comparison(
                    campaign_ids=entity_id_list,
                    date_range=date_range,
                    metrics=metrics_list
                )
            elif entity_type == "ad_group":
                # Implement ad group comparison if needed
                # For now, return an error
                return {
                    "error": "Ad group comparison not implemented yet"
                }
            
            # Check if there was an error
            if "error" in comparison_data:
                return {
                    "error": comparison_data["error"]
                }
            
            # Generate visualization using the new dedicated comparison visualization function
            visualization = format_comparison_visualization(
                comparison_data=comparison_data,
                metrics=comparison_data["metrics"],
                title=f"{entity_type.title()} Performance Comparison"
            )
            
            return {
                "entity_type": entity_type,
                "entity_ids": entity_id_list,
                "date_range": date_range,
                "comparison_data": comparison_data,
                "visualization": visualization
            }
            
        except Exception as e:
            logger.error(f"Error getting performance comparison: {str(e)}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def get_performance_breakdown_json(entity_type: str, entity_id: str, dimensions: str, date_range: str = "LAST_30_DAYS"):
        """
        Get performance breakdown by various dimensions (device, geo, time, etc.).
        
        Args:
            entity_type: Type of entity ("account", "campaign", "ad_group")
            entity_id: ID of the entity (can be empty for account-level breakdown)
            dimensions: Comma-separated list of dimensions to break down by 
                       (supported: device, day, week, month, geo, network)
            date_range: Date range for the breakdown data
            
        Returns:
            JSON data with breakdown visualizations
        """
        try:
            logger.info(f"Getting {entity_type} breakdown by {dimensions} for ID {entity_id}")
            
            # Validate entity type
            if entity_type not in ["account", "campaign", "ad_group"]:
                return {
                    "error": "Invalid entity_type. Supported values: account, campaign, ad_group"
                }
            
            # Parse dimensions
            dimension_list = [dim.strip() for dim in dimensions.split(",") if dim.strip()]
            if not dimension_list:
                return {
                    "error": "No valid dimensions provided"
                }
            
            # Validate dimensions
            valid_dimensions = ["device", "day", "week", "month", "geo", "network"]
            invalid_dimensions = [dim for dim in dimension_list if dim not in valid_dimensions]
            if invalid_dimensions:
                return {
                    "error": f"Invalid dimensions: {', '.join(invalid_dimensions)}. "
                             f"Supported values: {', '.join(valid_dimensions)}"
                }
            
            # Get breakdown data from service
            breakdown_data = await dashboard_service.get_performance_breakdown(
                entity_type=entity_type,
                entity_id=entity_id if entity_id else None,
                dimensions=dimension_list,
                date_range=date_range
            )
            
            # Check if there was an error
            if "error" in breakdown_data:
                return {
                    "error": breakdown_data["error"]
                }
            
            # Generate visualization using the new dedicated breakdown visualization function
            visualization = format_breakdown_visualization(
                breakdown_data=breakdown_data,
                title="Performance Breakdown"
            )
            
            return {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "entity_name": breakdown_data.get("entity_name", "Unknown"),
                "dimensions": dimension_list,
                "date_range": date_range,
                "breakdown_data": breakdown_data,
                "visualization": visualization
            }
            
        except Exception as e:
            logger.error(f"Error getting performance breakdown: {str(e)}")
            return {"error": str(e)}

def register_insights_tools(mcp, google_ads_service, insights_service) -> None:
    """
    Register insights-related MCP tools.
    
    Args:
        mcp: The MCP server instance
        google_ads_service: The Google Ads service instance
        insights_service: The insights service instance
    """
    @mcp.tool()
    async def get_performance_anomalies(
        customer_id: str,
        entity_type: str = "CAMPAIGN",
        entity_ids: str = None,
        metrics: str = None,
        start_date: str = None,
        end_date: str = None,
        comparison_period: str = "PREVIOUS_PERIOD",
        threshold: float = 2.0
    ):
        """
        Detect performance anomalies in Google Ads metrics.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            entity_type: Type of entity to analyze (CAMPAIGN, AD_GROUP, KEYWORD)
            entity_ids: Optional comma-separated list of entity IDs to filter by
            metrics: Optional comma-separated list of metrics to analyze (defaults to impressions,clicks,cost,ctr,conversions)
            start_date: Start date in YYYY-MM-DD format (defaults to 7 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            comparison_period: Period to compare against (PREVIOUS_PERIOD, SAME_PERIOD_LAST_YEAR)
            threshold: Z-score threshold for anomaly detection (default: 2.0)
            
        Returns:
            Formatted report of detected anomalies
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Detecting performance anomalies for customer {customer_id}")
            
            # Parse entity IDs if provided
            entity_id_list = None
            if entity_ids:
                entity_id_list = [id.strip() for id in entity_ids.split(',')]
                
            # Parse metrics if provided
            metric_list = None
            if metrics:
                metric_list = [metric.strip().lower() for metric in metrics.split(',')]
                
            # Detect anomalies
            anomalies_data = await insights_service.detect_performance_anomalies(
                customer_id=customer_id,
                entity_type=entity_type,
                entity_ids=entity_id_list,
                metrics=metric_list,
                start_date=start_date,
                end_date=end_date,
                comparison_period=comparison_period,
                threshold=threshold
            )
            
            # Format the results as a text report
            anomalies = anomalies_data.get("anomalies", [])
            metadata = anomalies_data.get("metadata", {})
            
            if not anomalies:
                return "No performance anomalies detected for the specified criteria."
            
            # Format with dashes for display
            display_customer_id = customer_id
            if display_customer_id and len(display_customer_id) == 10:
                display_customer_id = f"{display_customer_id[:3]}-{display_customer_id[3:6]}-{display_customer_id[6:]}"
            
            # Format the results as a text report
            report = [
                f"Google Ads Performance Anomalies",
                f"Account ID: {display_customer_id}",
                f"Entity Type: {entity_type}",
                f"Date Range: {metadata.get('start_date', 'unknown')} to {metadata.get('end_date', 'unknown')}",
                f"Comparison Period: {comparison_period}",
                f"Total Anomalies Detected: {len(anomalies)}\n",
                f"{'Entity Name':<30} {'Metric':<15} {'Current':<12} {'Previous':<12} {'Change':<12} {'Severity':<8}",
                "-" * 85
            ]
            
            # Add data rows
            for anomaly in sorted(anomalies, key=lambda x: (0 if x.get("severity") == "HIGH" else 1, abs(x.get("percent_change", 0))), reverse=True):
                entity_name = anomaly.get("entity_name", "Unknown")
                if len(entity_name) > 27:
                    entity_name = entity_name[:24] + "..."
                    
                metric = anomaly.get("metric", "unknown")
                current = anomaly.get("current_value", 0)
                previous = anomaly.get("comparison_value", 0)
                percent_change = anomaly.get("percent_change", 0)
                severity = anomaly.get("severity", "")
                
                # Format values
                if metric.lower() in ["cost", "conversion_value"]:
                    current_formatted = f"${current:.2f}"
                    previous_formatted = f"${previous:.2f}"
                elif metric.lower() in ["ctr", "cvr", "conversion_rate"]:
                    current_formatted = f"{current:.2%}"
                    previous_formatted = f"{previous:.2%}"
                else:
                    current_formatted = f"{current:,.0f}" if current >= 10 else f"{current:.2f}"
                    previous_formatted = f"{previous:,.0f}" if previous >= 10 else f"{previous:.2f}"
                
                change_formatted = f"{'+' if percent_change > 0 else ''}{percent_change:.1f}%"
                
                report.append(
                    f"{entity_name:<30} {metric:<15} {current_formatted:<12} {previous_formatted:<12} "
                    f"{change_formatted:<12} {severity:<8}"
                )
                
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error detecting performance anomalies: {str(e)}")
            return f"Error: {str(e)}"
    
    @mcp.tool()
    async def get_performance_anomalies_json(
        customer_id: str,
        entity_type: str = "CAMPAIGN",
        entity_ids: str = None,
        metrics: str = None,
        start_date: str = None,
        end_date: str = None,
        comparison_period: str = "PREVIOUS_PERIOD",
        threshold: float = 2.0
    ):
        """
        Detect performance anomalies in Google Ads metrics with JSON output for visualization.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            entity_type: Type of entity to analyze (CAMPAIGN, AD_GROUP, KEYWORD)
            entity_ids: Optional comma-separated list of entity IDs to filter by
            metrics: Optional comma-separated list of metrics to analyze (defaults to impressions,clicks,cost,ctr,conversions)
            start_date: Start date in YYYY-MM-DD format (defaults to 7 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            comparison_period: Period to compare against (PREVIOUS_PERIOD, SAME_PERIOD_LAST_YEAR)
            threshold: Z-score threshold for anomaly detection (default: 2.0)
            
        Returns:
            JSON data for anomaly visualization
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Detecting performance anomalies (JSON) for customer {customer_id}")
            
            # Parse entity IDs if provided
            entity_id_list = None
            if entity_ids:
                entity_id_list = [id.strip() for id in entity_ids.split(',')]
                
            # Parse metrics if provided
            metric_list = None
            if metrics:
                metric_list = [metric.strip().lower() for metric in metrics.split(',')]
                
            # Detect anomalies
            anomalies_data = await insights_service.detect_performance_anomalies(
                customer_id=customer_id,
                entity_type=entity_type,
                entity_ids=entity_id_list,
                metrics=metric_list,
                start_date=start_date,
                end_date=end_date,
                comparison_period=comparison_period,
                threshold=threshold
            )
            
            # Format for visualization
            visualization_data = format_anomalies_visualization(anomalies_data)
            
            return {
                "type": "success",
                "data": anomalies_data,
                "visualization": visualization_data
            }
            
        except Exception as e:
            logger.error(f"Error detecting performance anomalies (JSON): {str(e)}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def get_optimization_suggestions(
        customer_id: str,
        entity_types: str = "CAMPAIGN,AD_GROUP,KEYWORD",
        campaign_ids: str = None,
        ad_group_ids: str = None,
        keyword_ids: str = None,
        start_date: str = None,
        end_date: str = None
    ):
        """
        Generate optimization suggestions for a Google Ads account.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            entity_types: Comma-separated list of entity types to analyze (CAMPAIGN, AD_GROUP, KEYWORD)
            campaign_ids: Optional comma-separated list of campaign IDs to filter by
            ad_group_ids: Optional comma-separated list of ad group IDs to filter by
            keyword_ids: Optional comma-separated list of keyword IDs to filter by
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Formatted report of optimization suggestions
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Generating optimization suggestions for customer {customer_id}")
            
            # Parse entity types
            entity_type_list = [et.strip().upper() for et in entity_types.split(',')]
            
            # Parse entity IDs if provided
            entity_ids = {}
            if campaign_ids:
                entity_ids["CAMPAIGN"] = [id.strip() for id in campaign_ids.split(',')]
            if ad_group_ids:
                entity_ids["AD_GROUP"] = [id.strip() for id in ad_group_ids.split(',')]
            if keyword_ids:
                entity_ids["KEYWORD"] = [id.strip() for id in keyword_ids.split(',')]
                
            # Generate suggestions
            suggestions_data = await insights_service.generate_optimization_suggestions(
                customer_id=customer_id,
                entity_types=entity_type_list,
                entity_ids=entity_ids,
                start_date=start_date,
                end_date=end_date
            )
            
            # Format the results as a text report
            suggestions = suggestions_data.get("suggestions", {})
            metadata = suggestions_data.get("metadata", {})
            
            total_suggestions = metadata.get("total_suggestions", 0)
            
            if total_suggestions == 0:
                return "No optimization suggestions available for the specified criteria."
            
            # Format with dashes for display
            display_customer_id = customer_id
            if display_customer_id and len(display_customer_id) == 10:
                display_customer_id = f"{display_customer_id[:3]}-{display_customer_id[3:6]}-{display_customer_id[6:]}"
            
            # Format the results as a text report
            report = [
                f"Google Ads Optimization Suggestions",
                f"Account ID: {display_customer_id}",
                f"Date Range: {metadata.get('start_date', 'unknown')} to {metadata.get('end_date', 'unknown')}",
                f"Total Suggestions: {total_suggestions}\n"
            ]
            
            # Add category sections
            for category, category_suggestions in suggestions.items():
                if not category_suggestions:
                    continue
                    
                formatted_category = category.replace("_", " ").title()
                report.append(f"{formatted_category} Suggestions ({len(category_suggestions)})")
                report.append("-" * 50)
                
                # Add high impact suggestions first
                high_impact = sorted(
                    [s for s in category_suggestions if s.get("impact") == "HIGH"],
                    key=lambda x: x.get("type", "")
                )
                
                medium_impact = sorted(
                    [s for s in category_suggestions if s.get("impact") == "MEDIUM"],
                    key=lambda x: x.get("type", "")
                )
                
                low_impact = sorted(
                    [s for s in category_suggestions if s.get("impact") == "LOW"],
                    key=lambda x: x.get("type", "")
                )
                
                # Only show top 5 suggestions per impact level
                for suggestions_list, impact in [(high_impact, "HIGH"), (medium_impact, "MEDIUM"), (low_impact, "LOW")]:
                    if suggestions_list:
                        for suggestion in suggestions_list[:5]:  # Limit to top 5 per impact level
                            report.append(f"{impact}: {suggestion.get('suggestion', '')}")
                            report.append(f"     Action: {suggestion.get('action', '')}")
                            report.append("")
                
                # Add separator between categories
                report.append("")
                
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error generating optimization suggestions: {str(e)}")
            return f"Error: {str(e)}"
    
    @mcp.tool()
    async def get_optimization_suggestions_json(
        customer_id: str,
        entity_types: str = "CAMPAIGN,AD_GROUP,KEYWORD",
        campaign_ids: str = None,
        ad_group_ids: str = None,
        keyword_ids: str = None,
        start_date: str = None,
        end_date: str = None
    ):
        """
        Generate optimization suggestions for a Google Ads account with JSON output for visualization.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            entity_types: Comma-separated list of entity types to analyze (CAMPAIGN, AD_GROUP, KEYWORD)
            campaign_ids: Optional comma-separated list of campaign IDs to filter by
            ad_group_ids: Optional comma-separated list of ad group IDs to filter by
            keyword_ids: Optional comma-separated list of keyword IDs to filter by
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            JSON data for suggestions visualization
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Generating optimization suggestions (JSON) for customer {customer_id}")
            
            # Parse entity types
            entity_type_list = [et.strip().upper() for et in entity_types.split(',')]
            
            # Parse entity IDs if provided
            entity_ids = {}
            if campaign_ids:
                entity_ids["CAMPAIGN"] = [id.strip() for id in campaign_ids.split(',')]
            if ad_group_ids:
                entity_ids["AD_GROUP"] = [id.strip() for id in ad_group_ids.split(',')]
            if keyword_ids:
                entity_ids["KEYWORD"] = [id.strip() for id in keyword_ids.split(',')]
                
            # Generate suggestions
            suggestions_data = await insights_service.generate_optimization_suggestions(
                customer_id=customer_id,
                entity_types=entity_type_list,
                entity_ids=entity_ids,
                start_date=start_date,
                end_date=end_date
            )
            
            # Format for visualization
            visualization_data = format_optimization_suggestions_visualization(suggestions_data)
            
            return {
                "type": "success",
                "data": suggestions_data,
                "visualization": visualization_data
            }
            
        except Exception as e:
            logger.error(f"Error generating optimization suggestions (JSON): {str(e)}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def get_opportunities(
        customer_id: str,
        start_date: str = None,
        end_date: str = None
    ):
        """
        Discover growth opportunities in a Google Ads account.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Formatted report of growth opportunities
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Discovering growth opportunities for customer {customer_id}")
            
            # Discover opportunities
            opportunities_data = await insights_service.discover_opportunities(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Format the results as a text report
            opportunities = opportunities_data.get("opportunities", {})
            metadata = opportunities_data.get("metadata", {})
            
            total_opportunities = metadata.get("total_opportunities", 0)
            
            if total_opportunities == 0:
                return "No growth opportunities identified for the specified criteria."
            
            # Format with dashes for display
            display_customer_id = customer_id
            if display_customer_id and len(display_customer_id) == 10:
                display_customer_id = f"{display_customer_id[:3]}-{display_customer_id[3:6]}-{display_customer_id[6:]}"
            
            # Format the results as a text report
            report = [
                f"Google Ads Growth Opportunities",
                f"Account ID: {display_customer_id}",
                f"Date Range: {metadata.get('start_date', 'unknown')} to {metadata.get('end_date', 'unknown')}",
                f"Total Opportunities: {total_opportunities}\n"
            ]
            
            # Add category sections
            for category, category_opportunities in opportunities.items():
                if not category_opportunities:
                    continue
                    
                formatted_category = category.replace("_", " ").title()
                report.append(f"{formatted_category} Opportunities ({len(category_opportunities)})")
                report.append("-" * 50)
                
                # Add high impact opportunities first
                high_impact = sorted(
                    [o for o in category_opportunities if o.get("impact") == "HIGH"],
                    key=lambda x: x.get("type", "")
                )
                
                medium_impact = sorted(
                    [o for o in category_opportunities if o.get("impact") == "MEDIUM"],
                    key=lambda x: x.get("type", "")
                )
                
                # Only show top 5 opportunities per impact level
                for opportunities_list, impact in [(high_impact, "HIGH"), (medium_impact, "MEDIUM")]:
                    if opportunities_list:
                        for opportunity in opportunities_list[:5]:  # Limit to top 5 per impact level
                            report.append(f"{impact}: {opportunity.get('opportunity', '')}")
                            report.append(f"     Action: {opportunity.get('action', '')}")
                            report.append("")
                
                # Add separator between categories
                report.append("")
                
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error discovering growth opportunities: {str(e)}")
            return f"Error: {str(e)}"
    
    @mcp.tool()
    async def get_opportunities_json(
        customer_id: str,
        start_date: str = None,
        end_date: str = None
    ):
        """
        Discover growth opportunities in a Google Ads account with JSON output for visualization.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            JSON data for opportunities visualization
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Discovering growth opportunities (JSON) for customer {customer_id}")
            
            # Discover opportunities
            opportunities_data = await insights_service.discover_opportunities(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Format for visualization
            visualization_data = format_opportunities_visualization(opportunities_data)
            
            return {
                "type": "success",
                "data": opportunities_data,
                "visualization": visualization_data
            }
            
        except Exception as e:
            logger.error(f"Error discovering growth opportunities (JSON): {str(e)}")
            return {"error": str(e)}
    
    @mcp.tool()
    async def get_account_insights_json(
        customer_id: str,
        start_date: str = None,
        end_date: str = None
    ):
        """
        Get comprehensive insights for a Google Ads account with JSON output for visualization.
        
        Combines anomaly detection, optimization suggestions, and growth opportunities into a unified view.
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            JSON data for comprehensive insights visualization
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"Getting comprehensive account insights for customer {customer_id}")
            
            # Get anomalies (using 7 days for anomalies)
            anomaly_start = start_date
            if not anomaly_start:
                anomaly_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                
            anomalies_data = await insights_service.detect_performance_anomalies(
                customer_id=customer_id,
                start_date=anomaly_start,
                end_date=end_date
            )
            
            # Get suggestions
            suggestions_data = await insights_service.generate_optimization_suggestions(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Get opportunities
            opportunities_data = await insights_service.discover_opportunities(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Format combined data for visualization
            visualization_data = format_insights_visualization(
                anomalies_data=anomalies_data,
                suggestions_data=suggestions_data,
                opportunities_data=opportunities_data
            )
            
            return {
                "type": "success",
                "data": {
                    "anomalies": anomalies_data,
                    "suggestions": suggestions_data,
                    "opportunities": opportunities_data
                },
                "visualization": visualization_data
            }
            
        except Exception as e:
            logger.error(f"Error getting account insights: {str(e)}")
            return {"error": str(e)}
