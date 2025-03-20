#!/usr/bin/env python
"""
Google Ads MCP Server

This server exposes Google Ads API functionality through the Model Context Protocol (MCP).
"""

import os
import json
import logging
from datetime import datetime, timedelta
from http import HTTPStatus

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from google_ads_client import GoogleAdsService, GoogleAdsClientError
from health import health_check

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("google-ads-mcp")

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

# Initialize the MCP server
mcp = FastMCP(
    "Google Ads MCP Server",
    description="A server that provides access to Google Ads data through the Model Context Protocol"
)

# Create FastAPI app for HTTP endpoints (like health checks)
app = FastAPI(title="Google Ads MCP Server API")
mcp.include_routers(app)

# HTTP health check endpoint for container probes
@app.get("/health")
async def http_health_check():
    """HTTP endpoint for health checks, used by container probes."""
    health_data = await health_check.get_health()
    if health_data["status"] == "OK":
        return health_data
    return JSONResponse(
        status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        content=health_data
    )

@mcp.tool()
async def get_health_status():
    """
    Get the health status of the Google Ads MCP server.
    
    Returns:
        A formatted string with server health information
    """
    try:
        logger.info("Getting server health status")
        health_data = await health_check.get_health()
        
        # Format the health information as text
        report = [
            f"Google Ads MCP Server Health",
            f"Status: {health_data['status']}",
            f"Version: {health_data['version']}",
            f"Environment: {health_data['environment']}",
            f"Uptime: {health_data['uptime_formatted']}",
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

@mcp.tool()
async def get_health_status_json():
    """
    Get the health status of the Google Ads MCP server in JSON format.
    
    Returns:
        A JSON string with server health information for visualization
    """
    try:
        logger.info("Getting server health status (JSON format)")
        health_data = await health_check.get_health()
        return json.dumps(health_data)
        
    except Exception as e:
        logger.error(f"Error getting health status in JSON format: {str(e)}")
        return json.dumps({"error": f"Unable to retrieve health status - {str(e)}"})

@mcp.tool()
async def list_accounts():
    """
    List all accessible Google Ads accounts under the current MCC account.
    
    Returns:
        A formatted list of all accessible accounts with their IDs and names
    """
    try:
        logger.info("Listing accessible Google Ads accounts")
        
        # Initialize Google Ads service and get accessible accounts
        service = GoogleAdsService()
        accounts = await service.list_accessible_accounts()
        
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
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def get_accounts_json():
    """
    List all accessible Google Ads accounts in JSON format for visualization.
    
    Returns:
        A JSON string containing accounts data for visualization
    """
    try:
        logger.info("Listing accessible Google Ads accounts (JSON format)")
        
        # Initialize Google Ads service and get accessible accounts
        service = GoogleAdsService()
        accounts = await service.list_accessible_accounts()
        
        if not accounts:
            return json.dumps({"error": "No accessible accounts found"})
        
        # Return JSON data
        return json.dumps({
            "accounts": accounts,
            "total_accounts": len(accounts)
        })
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return json.dumps({"error": f"Unexpected error: {str(e)}"})

@mcp.tool()
async def get_account_hierarchy(customer_id: str = None):
    """
    Get the Google Ads account hierarchy from the specified account.
    
    Args:
        customer_id: Optional customer ID to use as the root (defaults to login_customer_id)
        
    Returns:
        A formatted representation of the account hierarchy
    """
    try:
        logger.info(f"Getting account hierarchy for customer ID {customer_id or 'default'}")
        
        # Initialize Google Ads service and get hierarchy
        service = GoogleAdsService()
        hierarchy = await service.get_account_hierarchy(customer_id)
        
        if not hierarchy:
            return "No account hierarchy found."
        
        # Format the results as a text report
        report = [
            f"Google Ads Account Hierarchy",
            f"Root Account: {hierarchy.get('name', 'Unknown')} ({hierarchy['id']})\n"
        ]
        
        # Add child accounts
        if hierarchy.get('children'):
            report.append(f"Child Accounts ({len(hierarchy['children'])}):")
            for i, child in enumerate(hierarchy['children'], 1):
                report.append(f"{i}. {child.get('name', 'Unknown')} ({child['id']})")
        else:
            report.append("No child accounts found.")
            
        return "\n".join(report)
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def get_account_hierarchy_json(customer_id: str = None):
    """
    Get the Google Ads account hierarchy in JSON format for visualization.
    
    Args:
        customer_id: Optional customer ID to use as the root (defaults to login_customer_id)
        
    Returns:
        A JSON string containing account hierarchy data for visualization
    """
    try:
        logger.info(f"Getting account hierarchy for customer ID {customer_id or 'default'} (JSON format)")
        
        # Initialize Google Ads service and get hierarchy
        service = GoogleAdsService()
        hierarchy = await service.get_account_hierarchy(customer_id)
        
        if not hierarchy:
            return json.dumps({"error": "No account hierarchy found"})
        
        # Return JSON data
        return json.dumps(hierarchy)
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return json.dumps({"error": f"Unexpected error: {str(e)}"})

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
        
        # Initialize Google Ads service and get campaign data
        service = GoogleAdsService()
        campaigns = await service.get_campaigns(start_date, end_date, customer_id)
        
        if not campaigns:
            return "No campaigns found for the specified customer ID and date range."
        
        # Get the actual customer ID that was used (for display purposes)
        used_customer_id = customer_id or service.client_customer_id
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
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def get_campaign_performance_json(start_date: str = None, end_date: str = None, customer_id: str = None):
    """
    Get performance metrics for Google Ads campaigns in JSON format for visualization.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
        end_date: End date in YYYY-MM-DD format (defaults to today)
        customer_id: Specific customer/account ID to query (defaults to the one in .env file)
        
    Returns:
        A JSON string containing campaign performance data for visualization
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        logger.info(f"Getting campaign performance for customer ID {customer_id or 'default'}, date range: {start_date} to {end_date} (JSON format)")
        
        # Initialize Google Ads service and get campaign data
        service = GoogleAdsService()
        campaigns = await service.get_campaigns(start_date, end_date, customer_id)
        
        if not campaigns:
            return json.dumps({"error": "No campaigns found for the specified customer ID and date range"})
        
        # Get the actual customer ID that was used
        used_customer_id = customer_id or service.client_customer_id
        
        # Return JSON data
        return json.dumps({
            "customer_id": used_customer_id,
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            },
            "campaigns": campaigns,
            "total_campaigns": len(campaigns)
        })
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return json.dumps({"error": f"Unexpected error: {str(e)}"})

@mcp.tool()
async def get_account_summary(start_date: str = None, end_date: str = None, customer_id: str = None):
    """
    Get a summary of account performance metrics.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
        end_date: End date in YYYY-MM-DD format (defaults to today)
        customer_id: Specific customer/account ID to query (defaults to the one in .env file)
        
    Returns:
        A formatted summary of account performance metrics
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        logger.info(f"Getting account summary for customer ID {customer_id or 'default'}, date range: {start_date} to {end_date}")
        
        # Initialize Google Ads service and get account summary
        service = GoogleAdsService()
        summary = await service.get_account_summary(start_date, end_date, customer_id)
        
        if not summary:
            return "No data found for the specified customer ID and date range."
        
        # Get the actual customer ID that was used
        used_customer_id = summary.get("customer_id", "")
        if used_customer_id:
            # Format with dashes for display
            if len(used_customer_id) == 10:
                used_customer_id = f"{used_customer_id[:3]}-{used_customer_id[3:6]}-{used_customer_id[6:]}"
        
        # Format the results as a text report
        report = [
            f"Google Ads Account Summary",
            f"Account ID: {used_customer_id}",
            f"Date Range: {summary['date_range']['start_date']} to {summary['date_range']['end_date']}\n",
            f"Key Performance Indicators:",
            f"- Total Impressions:      {int(summary['total_impressions']):,d}",
            f"- Total Clicks:           {int(summary['total_clicks']):,d}",
            f"- Total Cost:             ${summary['total_cost']:,.2f}",
            f"- Total Conversions:      {summary['total_conversions']:.1f}",
            f"- CTR:                    {summary['ctr']:.2f}%",
            f"- Average CPC:            ${summary['cpc']:.2f}",
            f"- Conversion Rate:        {summary['conversion_rate']:.2f}%",
            f"- Cost per Conversion:    ${summary['cost_per_conversion']:,.2f}"
        ]
            
        return "\n".join(report)
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def get_account_summary_json(start_date: str = None, end_date: str = None, customer_id: str = None):
    """
    Get a summary of account performance metrics in JSON format for visualization.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
        end_date: End date in YYYY-MM-DD format (defaults to today)
        customer_id: Specific customer/account ID to query (defaults to the one in .env file)
        
    Returns:
        A JSON string containing account summary data for visualization
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        logger.info(f"Getting account summary for customer ID {customer_id or 'default'}, date range: {start_date} to {end_date} (JSON format)")
        
        # Initialize Google Ads service and get account summary
        service = GoogleAdsService()
        summary = await service.get_account_summary(start_date, end_date, customer_id)
        
        if not summary:
            return json.dumps({"error": "No data found for the specified customer ID and date range"})
        
        # Return JSON data
        return json.dumps(summary)
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return json.dumps({"error": f"Unexpected error: {str(e)}"})

if __name__ == "__main__":
    logger.info("Starting Google Ads MCP server...")
    # Check the application environment
    app_env = os.environ.get("APP_ENV", "dev")
    app_version = os.environ.get("APP_VERSION", "1.0.0")
    logger.info(f"Environment: {app_env}, Version: {app_version}")
    
    # Log health check initialization
    logger.info("Initializing health check service...")
    
    # Start the FastAPI application with the MCP server
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    logger.info(f"Server will be available at http://localhost:{port}")
    logger.info(f"Health check endpoint: http://localhost:{port}/health")
    uvicorn.run(app, host="0.0.0.0", port=port) 