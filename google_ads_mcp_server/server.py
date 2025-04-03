#!/usr/bin/env python
"""
Google Ads MCP Server

This server exposes Google Ads API functionality through the Model Context Protocol (MCP).
"""

import os
import json
import logging
import uuid
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import List

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

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

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add a unique request ID to each request for tracing."""
    request_id = str(uuid.uuid4())
    # You can add the request ID to the context for logging if structlog is set up
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Initialize monitoring if enabled
if os.environ.get("ENABLE_METRICS", "false").lower() == "true":
    try:
        from monitoring import init_monitoring
        logger.info("Initializing monitoring...")
        init_monitoring(app)
    except ImportError as e:
        logger.warning(f"Monitoring module not available: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to initialize monitoring: {str(e)}")

# Mount the MCP's SSE app to the FastAPI app at the /mcp path
app.mount("/mcp", mcp.sse_app())

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

# Label Management Tools
@mcp.tool()
async def get_labels(customer_id: str = None):
    """
    Get all labels defined in the Google Ads account.
    
    Args:
        customer_id: Specific customer/account ID to query (defaults to the one in .env file)
        
    Returns:
        A formatted list of labels with their IDs, names, and attributes
    """
    try:
        logger.info(f"Getting labels for customer ID {customer_id or 'default'}")
        
        # Initialize Google Ads service and get labels
        service = GoogleAdsService()
        labels = await service.get_labels(customer_id)
        
        if not labels:
            return "No labels found for the specified customer ID."
        
        # Format the results as a text report
        report = [
            f"Google Ads Labels",
            f"Total Labels: {len(labels)}\n",
            f"{'Label ID':<10} {'Label Name':<30} {'Status':<10} {'Background Color':<15} {'Description':<30}",
            "-" * 95
        ]
        
        # Add data rows
        for label in sorted(labels, key=lambda x: x["name"]):
            name = label["name"]
            if len(name) > 27:
                name = name[:24] + "..."
                
            description = label.get("description", "")
            if description and len(description) > 27:
                description = description[:24] + "..."
                
            report.append(
                f"{label['id']:<10} {name:<30} {label['status']:<10} "
                f"{label.get('background_color', ''):<15} {description:<30}"
            )
            
        return "\n".join(report)
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def get_labels_json(customer_id: str = None):
    """
    Get all labels defined in the Google Ads account in JSON format for visualization.
    
    Args:
        customer_id: Specific customer/account ID to query (defaults to the one in .env file)
        
    Returns:
        A JSON string containing labels data for visualization
    """
    try:
        logger.info(f"Getting labels for customer ID {customer_id or 'default'} (JSON format)")
        
        # Initialize Google Ads service and get labels
        service = GoogleAdsService()
        labels = await service.get_labels(customer_id)
        
        if not labels:
            return json.dumps({"error": "No labels found for the specified customer ID"})
        
        # Format for visualization according to specification
        visualization_data = {
            "chart_type": "table",
            "title": "Google Ads Labels",
            "columns": [
                {
                    "title": "Label ID",
                    "dataKey": "id",
                    "width": 100,
                    "format": "text"
                },
                {
                    "title": "Label Name",
                    "dataKey": "name",
                    "width": 200,
                    "format": "text"
                },
                {
                    "title": "Status",
                    "dataKey": "status",
                    "width": 100,
                    "format": "text"
                },
                {
                    "title": "Background Color",
                    "dataKey": "background_color",
                    "width": 150,
                    "format": "text"
                },
                {
                    "title": "Description",
                    "dataKey": "description",
                    "width": 300,
                    "format": "text"
                }
            ],
            "data": labels,
            "pagination": True,
            "sortable": True,
            "defaultSort": "name",
            "defaultSortDirection": "asc"
        }
        
        return json.dumps({
            "response": {
                "message": f"Found {len(labels)} labels in the account.",
                "visualization_data": visualization_data
            }
        })
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return json.dumps({"error": f"Unexpected error: {str(e)}"})

@mcp.tool()
async def get_campaigns_by_label(label_id: str, start_date: str = None, end_date: str = None, customer_id: str = None):
    """
    Get campaigns that have a specific label with performance metrics.
    
    Args:
        label_id: The ID of the label to filter by
        start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
        end_date: End date in YYYY-MM-DD format (defaults to today)
        customer_id: Specific customer/account ID to query (defaults to the one in .env file)
        
    Returns:
        A formatted report of campaign performance metrics filtered by label
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        logger.info(f"Getting campaigns with label ID {label_id} for customer ID {customer_id or 'default'}, date range: {start_date} to {end_date}")
        
        # Initialize Google Ads service and get campaign data
        service = GoogleAdsService()
        campaigns = await service.get_campaigns_by_label(label_id, start_date, end_date, customer_id)
        
        if not campaigns:
            return f"No campaigns found with label ID {label_id} for the specified date range."
        
        # Get the actual customer ID that was used (for display purposes)
        used_customer_id = customer_id or service.client_customer_id
        if used_customer_id:
            # Format with dashes for display
            if len(used_customer_id) == 10:
                used_customer_id = f"{used_customer_id[:3]}-{used_customer_id[3:6]}-{used_customer_id[6:]}"
        
        # Get the label name from the first campaign (all campaigns should have the same label)
        label_name = campaigns[0]["label"]["name"] if campaigns else f"Label {label_id}"
        
        # Format the results as a text report
        report = [
            f"Google Ads Campaign Performance Report - Label: {label_name}",
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
                
            report.append(
                f"{campaign['id']:<15} {name:<30} {campaign['status']:<15} "
                f"{int(campaign['impressions']):,d} {int(campaign['clicks']):,d} "
                f"${campaign['cost']:,.2f} {campaign['ctr']:.2f}% ${campaign['cpc']:.2f}"
            )
            
        return "\n".join(report)
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def get_campaigns_by_label_json(label_id: str, start_date: str = None, end_date: str = None, customer_id: str = None):
    """
    Get campaigns that have a specific label with performance metrics in JSON format for visualization.
    
    Args:
        label_id: The ID of the label to filter by
        start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
        end_date: End date in YYYY-MM-DD format (defaults to today)
        customer_id: Specific customer/account ID to query (defaults to the one in .env file)
        
    Returns:
        A JSON string containing campaign performance data filtered by label for visualization
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        logger.info(f"Getting campaigns with label ID {label_id} for customer ID {customer_id or 'default'}, date range: {start_date} to {end_date} (JSON format)")
        
        # Initialize Google Ads service and get campaign data
        service = GoogleAdsService()
        campaigns = await service.get_campaigns_by_label(label_id, start_date, end_date, customer_id)
        
        if not campaigns:
            return json.dumps({"error": f"No campaigns found with label ID {label_id} for the specified date range"})
        
        # Get the actual customer ID that was used
        used_customer_id = customer_id or service.client_customer_id
        
        # Get the label name from the first campaign
        label_name = campaigns[0]["label"]["name"] if campaigns else f"Label {label_id}"
        
        # Format for bar chart visualization according to specification
        visualization_data = {
            "chart_type": "bar",
            "title": f"Campaign Performance by Label: {label_name}",
            "subtitle": f"Performance metrics from {start_date} to {end_date}",
            "data": campaigns,
            "axes": {
                "x": {
                    "label": "Campaign",
                    "dataKey": "name",
                    "type": "category"
                },
                "y": {
                    "label": "Value",
                    "type": "number"
                }
            },
            "series": [
                {
                    "name": "Clicks",
                    "dataKey": "clicks",
                    "color": "#82ca9d",
                    "type": "bar"
                },
                {
                    "name": "Conversions",
                    "dataKey": "conversions",
                    "color": "#ff8042",
                    "type": "bar"
                },
                {
                    "name": "Cost",
                    "dataKey": "cost",
                    "color": "#8884d8",
                    "type": "bar"
                }
            ],
            "legend": True,
            "grid": True,
            "tooltip": True
        }
        
        return json.dumps({
            "response": {
                "message": f"Found {len(campaigns)} campaigns with label '{label_name}'.",
                "visualization_data": visualization_data,
                "raw_data": {
                    "customer_id": used_customer_id,
                    "label_id": label_id,
                    "label_name": label_name,
                    "date_range": {
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "campaigns": campaigns,
                    "total_campaigns": len(campaigns)
                }
            }
        })
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return json.dumps({"error": f"Unexpected error: {str(e)}"})

@mcp.tool()
async def get_ad_groups_by_label(label_id: str, start_date: str = None, end_date: str = None, customer_id: str = None):
    """
    Get ad groups that have a specific label with performance metrics.
    
    Args:
        label_id: The ID of the label to filter by
        start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
        end_date: End date in YYYY-MM-DD format (defaults to today)
        customer_id: Specific customer/account ID to query (defaults to the one in .env file)
        
    Returns:
        A formatted report of ad group performance metrics filtered by label
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        logger.info(f"Getting ad groups with label ID {label_id} for customer ID {customer_id or 'default'}, date range: {start_date} to {end_date}")
        
        # Initialize Google Ads service and get ad group data
        service = GoogleAdsService()
        ad_groups = await service.get_ad_groups_by_label(label_id, start_date, end_date, customer_id)
        
        if not ad_groups:
            return f"No ad groups found with label ID {label_id} for the specified date range."
        
        # Get the actual customer ID that was used (for display purposes)
        used_customer_id = customer_id or service.client_customer_id
        if used_customer_id:
            # Format with dashes for display
            if len(used_customer_id) == 10:
                used_customer_id = f"{used_customer_id[:3]}-{used_customer_id[3:6]}-{used_customer_id[6:]}"
        
        # Get the label name from the first ad group (all should have the same label)
        label_name = ad_groups[0]["label"]["name"] if ad_groups else f"Label {label_id}"
        
        # Format the results as a text report
        report = [
            f"Google Ads Ad Group Performance Report - Label: {label_name}",
            f"Account ID: {used_customer_id}",
            f"Date Range: {start_date} to {end_date}\n",
            f"{'Ad Group ID':<10} {'Ad Group Name':<25} {'Campaign':<25} {'Status':<10} {'Impressions':<12} {'Clicks':<8} {'Cost':<10} {'CTR':<8} {'CPC':<8}",
            "-" * 115
        ]
        
        # Add data rows
        for ad_group in sorted(ad_groups, key=lambda x: x["cost"], reverse=True):
            name = ad_group["name"]
            if len(name) > 22:
                name = name[:19] + "..."
                
            campaign_name = ad_group["campaign"]["name"]
            if len(campaign_name) > 22:
                campaign_name = campaign_name[:19] + "..."
                
            report.append(
                f"{ad_group['id']:<10} {name:<25} {campaign_name:<25} {ad_group['status']:<10} "
                f"{int(ad_group['impressions']):,d} {int(ad_group['clicks']):,d} "
                f"${ad_group['cost']:,.2f} {ad_group['ctr']:.2f}% ${ad_group['cpc']:.2f}"
            )
            
        return "\n".join(report)
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def get_ad_groups_by_label_json(label_id: str, start_date: str = None, end_date: str = None, customer_id: str = None):
    """
    Get ad groups that have a specific label with performance metrics in JSON format for visualization.
    
    Args:
        label_id: The ID of the label to filter by
        start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
        end_date: End date in YYYY-MM-DD format (defaults to today)
        customer_id: Specific customer/account ID to query (defaults to the one in .env file)
        
    Returns:
        A JSON string containing ad group performance data filtered by label for visualization
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        logger.info(f"Getting ad groups with label ID {label_id} for customer ID {customer_id or 'default'}, date range: {start_date} to {end_date} (JSON format)")
        
        # Initialize Google Ads service and get ad group data
        service = GoogleAdsService()
        ad_groups = await service.get_ad_groups_by_label(label_id, start_date, end_date, customer_id)
        
        if not ad_groups:
            return json.dumps({"error": f"No ad groups found with label ID {label_id} for the specified date range"})
        
        # Get the actual customer ID that was used
        used_customer_id = customer_id or service.client_customer_id
        
        # Get the label name from the first ad group
        label_name = ad_groups[0]["label"]["name"] if ad_groups else f"Label {label_id}"
        
        # Format for visualization according to specification
        visualization_data = {
            "chart_type": "bar",
            "title": f"Ad Group Performance by Label: {label_name}",
            "subtitle": f"Performance metrics from {start_date} to {end_date}",
            "data": ad_groups,
            "axes": {
                "x": {
                    "label": "Ad Group",
                    "dataKey": "name",
                    "type": "category"
                },
                "y": {
                    "label": "Value",
                    "type": "number"
                }
            },
            "series": [
                {
                    "name": "Clicks",
                    "dataKey": "clicks",
                    "color": "#82ca9d",
                    "type": "bar"
                },
                {
                    "name": "Conversions",
                    "dataKey": "conversions",
                    "color": "#ff8042",
                    "type": "bar"
                },
                {
                    "name": "Cost",
                    "dataKey": "cost",
                    "color": "#8884d8",
                    "type": "bar"
                }
            ],
            "legend": True,
            "grid": True,
            "tooltip": True
        }
        
        return json.dumps({
            "response": {
                "message": f"Found {len(ad_groups)} ad groups with label '{label_name}'.",
                "visualization_data": visualization_data,
                "raw_data": {
                    "customer_id": used_customer_id,
                    "label_id": label_id,
                    "label_name": label_name,
                    "date_range": {
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "ad_groups": ad_groups,
                    "total_ad_groups": len(ad_groups)
                }
            }
        })
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return json.dumps({"error": f"Unexpected error: {str(e)}"})

@mcp.tool()
async def get_ads_by_label(label_id: str, start_date: str = None, end_date: str = None, customer_id: str = None):
    """
    Get ads that have a specific label with performance metrics.
    
    Args:
        label_id: The ID of the label to filter by
        start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
        end_date: End date in YYYY-MM-DD format (defaults to today)
        customer_id: Specific customer/account ID to query (defaults to the one in .env file)
        
    Returns:
        A formatted report of ad performance metrics filtered by label
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        logger.info(f"Getting ads with label ID {label_id} for customer ID {customer_id or 'default'}, date range: {start_date} to {end_date}")
        
        # Initialize Google Ads service and get ad data
        service = GoogleAdsService()
        ads = await service.get_ads_by_label(label_id, start_date, end_date, customer_id)
        
        if not ads:
            return f"No ads found with label ID {label_id} for the specified date range."
        
        # Get the actual customer ID that was used (for display purposes)
        used_customer_id = customer_id or service.client_customer_id
        if used_customer_id:
            # Format with dashes for display
            if len(used_customer_id) == 10:
                used_customer_id = f"{used_customer_id[:3]}-{used_customer_id[3:6]}-{used_customer_id[6:]}"
        
        # Get the label name from the first ad (all should have the same label)
        label_name = ads[0]["label"]["name"] if ads else f"Label {label_id}"
        
        # Format the results as a text report
        report = [
            f"Google Ads Ad Performance Report - Label: {label_name}",
            f"Account ID: {used_customer_id}",
            f"Date Range: {start_date} to {end_date}\n",
            f"{'Ad ID':<10} {'Ad Name':<25} {'Type':<10} {'Ad Group':<20} {'Campaign':<20} {'Status':<10} {'Impr.':<8} {'Clicks':<6} {'CTR':<6} {'Cost':<8}",
            "-" * 125
        ]
        
        # Add data rows
        for ad in sorted(ads, key=lambda x: x["cost"], reverse=True):
            name = ad["name"]
            if len(name) > 22:
                name = name[:19] + "..."
                
            ad_group_name = ad["ad_group"]["name"]
            if len(ad_group_name) > 17:
                ad_group_name = ad_group_name[:14] + "..."
                
            campaign_name = ad["campaign"]["name"]
            if len(campaign_name) > 17:
                campaign_name = campaign_name[:14] + "..."
                
            report.append(
                f"{ad['id']:<10} {name:<25} {ad['type']:<10} {ad_group_name:<20} {campaign_name:<20} "
                f"{ad['status']:<10} {int(ad['impressions']):,d} {int(ad['clicks']):,d} "
                f"{ad['ctr']:.2f}% ${ad['cost']:,.2f}"
            )
            
        return "\n".join(report)
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def get_ads_by_label_json(label_id: str, start_date: str = None, end_date: str = None, customer_id: str = None):
    """
    Get ads that have a specific label with performance metrics in JSON format for visualization.
    
    Args:
        label_id: The ID of the label to filter by
        start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
        end_date: End date in YYYY-MM-DD format (defaults to today)
        customer_id: Specific customer/account ID to query (defaults to the one in .env file)
        
    Returns:
        A JSON string containing ad performance data filtered by label for visualization
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        logger.info(f"Getting ads with label ID {label_id} for customer ID {customer_id or 'default'}, date range: {start_date} to {end_date} (JSON format)")
        
        # Initialize Google Ads service and get ad data
        service = GoogleAdsService()
        ads = await service.get_ads_by_label(label_id, start_date, end_date, customer_id)
        
        if not ads:
            return json.dumps({"error": f"No ads found with label ID {label_id} for the specified date range"})
        
        # Get the actual customer ID that was used
        used_customer_id = customer_id or service.client_customer_id
        
        # Get the label name from the first ad
        label_name = ads[0]["label"]["name"] if ads else f"Label {label_id}"
        
        # Format for visualization according to specification
        visualization_data = {
            "chart_type": "bar",
            "title": f"Ad Performance by Label: {label_name}",
            "subtitle": f"Performance metrics from {start_date} to {end_date}",
            "data": ads,
            "axes": {
                "x": {
                    "label": "Ad",
                    "dataKey": "name",
                    "type": "category"
                },
                "y": {
                    "label": "Value",
                    "type": "number"
                }
            },
            "series": [
                {
                    "name": "Impressions",
                    "dataKey": "impressions",
                    "color": "#8884d8",
                    "type": "bar"
                },
                {
                    "name": "Clicks",
                    "dataKey": "clicks",
                    "color": "#82ca9d",
                    "type": "bar"
                },
                {
                    "name": "Cost",
                    "dataKey": "cost",
                    "color": "#ffc658",
                    "type": "bar"
                }
            ],
            "legend": True,
            "grid": True,
            "tooltip": True
        }
        
        return json.dumps({
            "response": {
                "message": f"Found {len(ads)} ads with label '{label_name}'.",
                "visualization_data": visualization_data,
                "raw_data": {
                    "customer_id": used_customer_id,
                    "label_id": label_id,
                    "label_name": label_name,
                    "date_range": {
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "ads": ads,
                    "total_ads": len(ads)
                }
            }
        })
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return json.dumps({"error": f"Unexpected error: {str(e)}"})

@mcp.tool()
async def get_keywords_by_label(label_id: str, start_date: str = None, end_date: str = None, customer_id: str = None):
    """
    Get keywords that have a specific label with performance metrics.
    
    Args:
        label_id: The ID of the label to filter by
        start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
        end_date: End date in YYYY-MM-DD format (defaults to today)
        customer_id: Specific customer/account ID to query (defaults to the one in .env file)
        
    Returns:
        A formatted report of keyword performance metrics filtered by label
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        logger.info(f"Getting keywords with label ID {label_id} for customer ID {customer_id or 'default'}, date range: {start_date} to {end_date}")
        
        # Initialize Google Ads service and get keyword data
        service = GoogleAdsService()
        keywords = await service.get_keywords_by_label(label_id, start_date, end_date, customer_id)
        
        if not keywords:
            return f"No keywords found with label ID {label_id} for the specified date range."
        
        # Get the actual customer ID that was used (for display purposes)
        used_customer_id = customer_id or service.client_customer_id
        if used_customer_id:
            # Format with dashes for display
            if len(used_customer_id) == 10:
                used_customer_id = f"{used_customer_id[:3]}-{used_customer_id[3:6]}-{used_customer_id[6:]}"
        
        # Get the label name from the first keyword (all should have the same label)
        label_name = keywords[0]["label"]["name"] if keywords else f"Label {label_id}"
        
        # Format the results as a text report
        report = [
            f"Google Ads Keyword Performance Report - Label: {label_name}",
            f"Account ID: {used_customer_id}",
            f"Date Range: {start_date} to {end_date}\n",
            f"{'Keyword':<25} {'Match Type':<12} {'Ad Group':<20} {'Campaign':<20} {'Status':<10} {'Impr.':<8} {'Clicks':<6} {'CTR':<6} {'CPC':<7} {'Cost':<8}",
            "-" * 125
        ]
        
        # Add data rows
        for keyword in sorted(keywords, key=lambda x: x["cost"], reverse=True):
            text = keyword["text"]
            if len(text) > 22:
                text = text[:19] + "..."
                
            ad_group_name = keyword["ad_group"]["name"]
            if len(ad_group_name) > 17:
                ad_group_name = ad_group_name[:14] + "..."
                
            campaign_name = keyword["campaign"]["name"]
            if len(campaign_name) > 17:
                campaign_name = campaign_name[:14] + "..."
                
            report.append(
                f"{text:<25} {keyword['match_type']:<12} {ad_group_name:<20} {campaign_name:<20} "
                f"{keyword['status']:<10} {int(keyword['impressions']):,d} {int(keyword['clicks']):,d} "
                f"{keyword['ctr']:.2f}% ${keyword['cpc']:.2f} ${keyword['cost']:,.2f}"
            )
            
        return "\n".join(report)
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def get_keywords_by_label_json(label_id: str, start_date: str = None, end_date: str = None, customer_id: str = None):
    """
    Get keywords that have a specific label with performance metrics in JSON format for visualization.
    
    Args:
        label_id: The ID of the label to filter by
        start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
        end_date: End date in YYYY-MM-DD format (defaults to today)
        customer_id: Specific customer/account ID to query (defaults to the one in .env file)
        
    Returns:
        A JSON string containing keyword performance data filtered by label for visualization
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        logger.info(f"Getting keywords with label ID {label_id} for customer ID {customer_id or 'default'}, date range: {start_date} to {end_date} (JSON format)")
        
        # Initialize Google Ads service and get keyword data
        service = GoogleAdsService()
        keywords = await service.get_keywords_by_label(label_id, start_date, end_date, customer_id)
        
        if not keywords:
            return json.dumps({"error": f"No keywords found with label ID {label_id} for the specified date range"})
        
        # Get the actual customer ID that was used
        used_customer_id = customer_id or service.client_customer_id
        
        # Get the label name from the first keyword
        label_name = keywords[0]["label"]["name"] if keywords else f"Label {label_id}"
        
        # Format for visualization according to specification - table view for keywords
        visualization_data = {
            "chart_type": "table",
            "title": f"Keyword Performance by Label: {label_name}",
            "subtitle": f"Performance metrics from {start_date} to {end_date}",
            "columns": [
                {
                    "title": "Keyword",
                    "dataKey": "text",
                    "width": 200,
                    "format": "text"
                },
                {
                    "title": "Match Type",
                    "dataKey": "match_type",
                    "width": 120,
                    "format": "text"
                },
                {
                    "title": "Impressions",
                    "dataKey": "impressions",
                    "width": 100,
                    "format": "number"
                },
                {
                    "title": "Clicks",
                    "dataKey": "clicks",
                    "width": 80,
                    "format": "number"
                },
                {
                    "title": "CTR",
                    "dataKey": "ctr",
                    "width": 80,
                    "format": "percent"
                },
                {
                    "title": "CPC",
                    "dataKey": "cpc",
                    "width": 80,
                    "format": "currency"
                },
                {
                    "title": "Cost",
                    "dataKey": "cost",
                    "width": 80,
                    "format": "currency"
                },
                {
                    "title": "Conv.",
                    "dataKey": "conversions",
                    "width": 80,
                    "format": "number"
                }
            ],
            "data": keywords,
            "pagination": True,
            "sortable": True,
            "defaultSort": "cost",
            "defaultSortDirection": "desc"
        }
        
        return json.dumps({
            "response": {
                "message": f"Found {len(keywords)} keywords with label '{label_name}'.",
                "visualization_data": visualization_data,
                "raw_data": {
                    "customer_id": used_customer_id,
                    "label_id": label_id,
                    "label_name": label_name,
                    "date_range": {
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "keywords": keywords,
                    "total_keywords": len(keywords)
                }
            }
        })
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return json.dumps({"error": f"Unexpected error: {str(e)}"})

@mcp.tool()
async def pause_ad(ad_group_id: str, ad_id: str, customer_id: str = None):
    """
    Pause a Google Ads ad.
    
    Args:
        ad_group_id: The ad group ID containing the ad
        ad_id: The ID of the ad to pause
        customer_id: Optional customer ID (defaults to the one in .env file)
        
    Returns:
        Operation status message
    """
    try:
        logger.info(f"Pausing ad with ID {ad_id} in ad group {ad_group_id} for customer ID {customer_id or 'default'}")
        
        # Initialize Google Ads service and pause the ad
        service = GoogleAdsService()
        result = await service.pause_ad(ad_group_id, ad_id, customer_id)
        
        # Format the response
        response = [
            f"✅ Google Ads - Ad Paused Successfully",
            f"Ad ID: {ad_id}",
            f"Ad Group ID: {ad_group_id}",
        ]
        
        # Add the customer ID info
        used_customer_id = customer_id or service.client_customer_id
        if used_customer_id:
            # Format with dashes for display
            if len(used_customer_id) == 10:
                used_customer_id = f"{used_customer_id[:3]}-{used_customer_id[3:6]}-{used_customer_id[6:]}"
            response.append(f"Customer ID: {used_customer_id}")
            
        # Add resource name if available
        if result.get("resource_name"):
            response.append(f"Resource Name: {result['resource_name']}")
            
        return "\n".join(response)
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return f"❌ Error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"❌ Unexpected error: {str(e)}"

@mcp.tool()
async def pause_ad_json(ad_group_id: str, ad_id: str, customer_id: str = None):
    """
    Pause a Google Ads ad and return JSON result for visualization.
    
    Args:
        ad_group_id: The ad group ID containing the ad
        ad_id: The ID of the ad to pause
        customer_id: Optional customer ID (defaults to the one in .env file)
        
    Returns:
        JSON string with operation result for visualization
    """
    try:
        logger.info(f"Pausing ad with ID {ad_id} in ad group {ad_group_id} for customer ID {customer_id or 'default'} (JSON format)")
        
        # Initialize Google Ads service and pause the ad
        service = GoogleAdsService()
        result = await service.pause_ad(ad_group_id, ad_id, customer_id)
        
        # Get the actual customer ID that was used
        used_customer_id = customer_id or service.client_customer_id
        
        # Return JSON response
        response = {
            "status": "success",
            "action": "pause_ad",
            "ad_id": ad_id,
            "ad_group_id": ad_group_id,
            "customer_id": used_customer_id,
            "resource_name": result.get("resource_name"),
            "message": "Ad successfully paused",
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(response)
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return json.dumps({
            "status": "error",
            "action": "pause_ad",
            "ad_id": ad_id,
            "ad_group_id": ad_group_id,
            "customer_id": customer_id,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return json.dumps({
            "status": "error",
            "action": "pause_ad",
            "ad_id": ad_id,
            "ad_group_id": ad_group_id,
            "customer_id": customer_id,
            "error": f"Unexpected error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })

@mcp.tool()
async def create_responsive_search_ad(
    ad_group_id: str, 
    headlines: List[str], 
    descriptions: List[str], 
    final_url: str, 
    path1: str = None, 
    path2: str = None, 
    customer_id: str = None
):
    """
    Create a new responsive search ad in Google Ads.
    
    Args:
        ad_group_id: The ad group ID where to create the ad
        headlines: List of headlines for the ad (3-15 required)
        descriptions: List of descriptions for the ad (2-4 required)
        final_url: The URL for the ad
        path1: Optional first path for the display URL
        path2: Optional second path for the display URL
        customer_id: Optional customer ID (defaults to the one in .env file)
        
    Returns:
        Operation status message
    """
    try:
        logger.info(f"Creating responsive search ad in ad group {ad_group_id} for customer ID {customer_id or 'default'}")
        
        # Initialize Google Ads service and create the ad
        service = GoogleAdsService()
        result = await service.create_responsive_search_ad(
            ad_group_id, 
            headlines, 
            descriptions, 
            final_url, 
            path1, 
            path2, 
            customer_id
        )
        
        # Format the response
        response = [
            f"✅ Google Ads - Responsive Search Ad Created Successfully",
            f"Ad Group ID: {ad_group_id}",
            f"Final URL: {final_url}",
            f"\nHeadlines ({len(headlines)}):"
        ]
        
        # Add headlines
        for i, headline in enumerate(headlines, 1):
            response.append(f"{i}. {headline}")
            
        # Add descriptions
        response.append(f"\nDescriptions ({len(descriptions)}):")
        for i, description in enumerate(descriptions, 1):
            response.append(f"{i}. {description}")
            
        # Add paths if specified
        if path1 or path2:
            display_url = f"{final_url.split('//')[1].split('/')[0]}"
            if path1:
                display_url += f"/{path1}"
            if path2:
                display_url += f"/{path2}"
            response.append(f"\nDisplay URL: {display_url}")
            
        # Add the customer ID info
        used_customer_id = customer_id or service.client_customer_id
        if used_customer_id:
            # Format with dashes for display
            if len(used_customer_id) == 10:
                used_customer_id = f"{used_customer_id[:3]}-{used_customer_id[3:6]}-{used_customer_id[6:]}"
            response.append(f"\nCustomer ID: {used_customer_id}")
            
        # Add resource name if available
        if result.get("resource_name"):
            response.append(f"Resource Name: {result['resource_name']}")
            
        # Note about ad status
        response.append("\nNote: The ad has been created with PAUSED status for safety. You can enable it in the Google Ads interface.")
            
        return "\n".join(response)
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return f"❌ Error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"❌ Unexpected error: {str(e)}"

@mcp.tool()
async def create_responsive_search_ad_json(
    ad_group_id: str, 
    headlines: List[str], 
    descriptions: List[str], 
    final_url: str, 
    path1: str = None, 
    path2: str = None, 
    customer_id: str = None
):
    """
    Create a new responsive search ad in Google Ads and return JSON result for visualization.
    
    Args:
        ad_group_id: The ad group ID where to create the ad
        headlines: List of headlines for the ad (3-15 required)
        descriptions: List of descriptions for the ad (2-4 required)
        final_url: The URL for the ad
        path1: Optional first path for the display URL
        path2: Optional second path for the display URL
        customer_id: Optional customer ID (defaults to the one in .env file)
        
    Returns:
        JSON string with operation result for visualization
    """
    try:
        logger.info(f"Creating responsive search ad in ad group {ad_group_id} for customer ID {customer_id or 'default'} (JSON format)")
        
        # Initialize Google Ads service and create the ad
        service = GoogleAdsService()
        result = await service.create_responsive_search_ad(
            ad_group_id, 
            headlines, 
            descriptions, 
            final_url, 
            path1, 
            path2, 
            customer_id
        )
        
        # Get the actual customer ID that was used
        used_customer_id = customer_id or service.client_customer_id
        
        # Create display URL for preview
        display_url = f"{final_url.split('//')[1].split('/')[0]}"
        if path1:
            display_url += f"/{path1}"
        if path2:
            display_url += f"/{path2}"
        
        # Create response
        response = {
            "status": "success",
            "action": "create_responsive_search_ad",
            "ad_group_id": ad_group_id,
            "customer_id": used_customer_id,
            "resource_name": result.get("resource_name"),
            "ad_details": {
                "headlines": headlines,
                "descriptions": descriptions,
                "final_url": final_url,
                "display_url": display_url,
                "path1": path1,
                "path2": path2
            },
            "message": "Responsive search ad successfully created with PAUSED status",
            "timestamp": datetime.now().isoformat(),
            "visualization_data": {
                "chart_type": "kpi_cards",
                "title": "Ad Creation Success",
                "data": [
                    {
                        "title": "Ad Status",
                        "value": "PAUSED",
                        "format": "string",
                        "color": "#ffc658"
                    },
                    {
                        "title": "Headlines",
                        "value": len(headlines),
                        "format": "number",
                        "color": "#8884d8"
                    },
                    {
                        "title": "Descriptions",
                        "value": len(descriptions),
                        "format": "number",
                        "color": "#82ca9d"
                    }
                ],
                "layout": "horizontal",
                "card_width": 250,
                "card_height": 150
            }
        }
        
        return json.dumps(response)
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return json.dumps({
            "status": "error",
            "action": "create_responsive_search_ad",
            "ad_group_id": ad_group_id,
            "customer_id": customer_id,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return json.dumps({
            "status": "error",
            "action": "create_responsive_search_ad",
            "ad_group_id": ad_group_id,
            "customer_id": customer_id,
            "error": f"Unexpected error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })

@mcp.tool()
async def get_date_ranges(preset: str = None):
    """
    Get common date range presets in YYYY-MM-DD format for Google Ads reporting.
    
    Args:
        preset: Optional specific preset to return (today, yesterday, last_7_days, last_30_days, 
                this_month, last_month, this_quarter, last_quarter, this_year, last_year, year_to_date)
                If not provided, all available presets will be returned.
        
    Returns:
        Formatted date ranges in YYYY-MM-DD format
    """
    try:
        logger.info(f"Getting date range presets, specific preset requested: {preset or 'None'}")
        
        # Get today's date
        today = datetime.now()
        date_presets = {}
        
        # Today
        date_presets["today"] = {
            "start_date": today.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "description": "Data for today only"
        }
        
        # Yesterday
        yesterday = today - timedelta(days=1)
        date_presets["yesterday"] = {
            "start_date": yesterday.strftime("%Y-%m-%d"),
            "end_date": yesterday.strftime("%Y-%m-%d"),
            "description": "Data for yesterday only"
        }
        
        # Last 7 days
        last_7_days_start = today - timedelta(days=7)
        date_presets["last_7_days"] = {
            "start_date": last_7_days_start.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "description": "Data for the last 7 days including today"
        }
        
        # Last 30 days
        last_30_days_start = today - timedelta(days=30)
        date_presets["last_30_days"] = {
            "start_date": last_30_days_start.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "description": "Data for the last 30 days including today"
        }
        
        # This month
        this_month_start = today.replace(day=1)
        date_presets["this_month"] = {
            "start_date": this_month_start.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "description": f"Data for the current month ({this_month_start.strftime('%B %Y')})"
        }
        
        # Last month
        last_month_end = this_month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        date_presets["last_month"] = {
            "start_date": last_month_start.strftime("%Y-%m-%d"),
            "end_date": last_month_end.strftime("%Y-%m-%d"),
            "description": f"Data for last month ({last_month_start.strftime('%B %Y')})"
        }
        
        # This quarter
        current_quarter = (today.month - 1) // 3 + 1
        this_quarter_start = datetime(today.year, 3 * current_quarter - 2, 1)
        date_presets["this_quarter"] = {
            "start_date": this_quarter_start.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "description": f"Data for Q{current_quarter} {today.year}"
        }
        
        # Last quarter
        if current_quarter == 1:
            last_quarter = 4
            last_quarter_year = today.year - 1
        else:
            last_quarter = current_quarter - 1
            last_quarter_year = today.year
            
        last_quarter_start = datetime(last_quarter_year, 3 * last_quarter - 2, 1)
        if last_quarter == 4:
            last_quarter_end = datetime(last_quarter_year, 12, 31)
        else:
            last_quarter_end = datetime(last_quarter_year, 3 * last_quarter + 1, 1) - timedelta(days=1)
            
        date_presets["last_quarter"] = {
            "start_date": last_quarter_start.strftime("%Y-%m-%d"),
            "end_date": last_quarter_end.strftime("%Y-%m-%d"),
            "description": f"Data for Q{last_quarter} {last_quarter_year}"
        }
        
        # This year
        this_year_start = datetime(today.year, 1, 1)
        date_presets["this_year"] = {
            "start_date": this_year_start.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "description": f"Data for {today.year} year-to-date"
        }
        
        # Last year
        last_year_start = datetime(today.year - 1, 1, 1)
        last_year_end = datetime(today.year - 1, 12, 31)
        date_presets["last_year"] = {
            "start_date": last_year_start.strftime("%Y-%m-%d"),
            "end_date": last_year_end.strftime("%Y-%m-%d"),
            "description": f"Data for the entire {today.year - 1} year"
        }
        
        # Year-to-date
        ytd_start = datetime(today.year, 1, 1)
        date_presets["year_to_date"] = {
            "start_date": ytd_start.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "description": f"Data from January 1, {today.year} to today"
        }
        
        # If a specific preset was requested, return only that one
        if preset and preset.lower() in date_presets:
            selected_preset = date_presets[preset.lower()]
            return (
                f"Date Range: {selected_preset['description']}\n"
                f"start_date: {selected_preset['start_date']}\n"
                f"end_date: {selected_preset['end_date']}"
            )
        
        # Otherwise, return all available presets
        report = ["Available Date Range Presets for Google Ads Reporting:\n"]
        
        for key, range_data in date_presets.items():
            report.append(
                f"{key}:\n"
                f"  Description: {range_data['description']}\n"
                f"  start_date: {range_data['start_date']}\n"
                f"  end_date: {range_data['end_date']}\n"
            )
            
        return "\n".join(report)
        
    except Exception as e:
        logger.error(f"Error getting date range presets: {str(e)}")
        return f"Error: Unable to generate date range presets - {str(e)}"

@mcp.tool()
async def get_date_ranges_json(preset: str = None):
    """
    Get common date range presets in YYYY-MM-DD format for Google Ads reporting in JSON format.
    
    Args:
        preset: Optional specific preset to return (today, yesterday, last_7_days, last_30_days, 
                this_month, last_month, this_quarter, last_quarter, this_year, last_year, year_to_date)
                If not provided, all available presets will be returned.
        
    Returns:
        JSON string with date range information for visualization
    """
    try:
        logger.info(f"Getting date range presets in JSON format, specific preset requested: {preset or 'None'}")
        
        # Get today's date
        today = datetime.now()
        date_presets = {}
        
        # Today
        date_presets["today"] = {
            "start_date": today.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "description": "Data for today only",
            "days": 1
        }
        
        # Yesterday
        yesterday = today - timedelta(days=1)
        date_presets["yesterday"] = {
            "start_date": yesterday.strftime("%Y-%m-%d"),
            "end_date": yesterday.strftime("%Y-%m-%d"),
            "description": "Data for yesterday only",
            "days": 1
        }
        
        # Last 7 days
        last_7_days_start = today - timedelta(days=7)
        date_presets["last_7_days"] = {
            "start_date": last_7_days_start.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "description": "Data for the last 7 days including today",
            "days": 7
        }
        
        # Last 30 days
        last_30_days_start = today - timedelta(days=30)
        date_presets["last_30_days"] = {
            "start_date": last_30_days_start.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "description": "Data for the last 30 days including today",
            "days": 30
        }
        
        # This month
        this_month_start = today.replace(day=1)
        days_this_month = (today - this_month_start).days + 1
        date_presets["this_month"] = {
            "start_date": this_month_start.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "description": f"Data for the current month ({this_month_start.strftime('%B %Y')})",
            "days": days_this_month
        }
        
        # Last month
        last_month_end = this_month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        days_last_month = (last_month_end - last_month_start).days + 1
        date_presets["last_month"] = {
            "start_date": last_month_start.strftime("%Y-%m-%d"),
            "end_date": last_month_end.strftime("%Y-%m-%d"),
            "description": f"Data for last month ({last_month_start.strftime('%B %Y')})",
            "days": days_last_month
        }
        
        # This quarter
        current_quarter = (today.month - 1) // 3 + 1
        this_quarter_start = datetime(today.year, 3 * current_quarter - 2, 1)
        days_this_quarter = (today - this_quarter_start).days + 1
        date_presets["this_quarter"] = {
            "start_date": this_quarter_start.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "description": f"Data for Q{current_quarter} {today.year}",
            "days": days_this_quarter
        }
        
        # Last quarter
        if current_quarter == 1:
            last_quarter = 4
            last_quarter_year = today.year - 1
        else:
            last_quarter = current_quarter - 1
            last_quarter_year = today.year
            
        last_quarter_start = datetime(last_quarter_year, 3 * last_quarter - 2, 1)
        if last_quarter == 4:
            last_quarter_end = datetime(last_quarter_year, 12, 31)
        else:
            last_quarter_end = datetime(last_quarter_year, 3 * last_quarter + 1, 1) - timedelta(days=1)
            
        days_last_quarter = (last_quarter_end - last_quarter_start).days + 1
        date_presets["last_quarter"] = {
            "start_date": last_quarter_start.strftime("%Y-%m-%d"),
            "end_date": last_quarter_end.strftime("%Y-%m-%d"),
            "description": f"Data for Q{last_quarter} {last_quarter_year}",
            "days": days_last_quarter
        }
        
        # This year
        this_year_start = datetime(today.year, 1, 1)
        days_this_year = (today - this_year_start).days + 1
        date_presets["this_year"] = {
            "start_date": this_year_start.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "description": f"Data for {today.year} year-to-date",
            "days": days_this_year
        }
        
        # Last year
        last_year_start = datetime(today.year - 1, 1, 1)
        last_year_end = datetime(today.year - 1, 12, 31)
        days_last_year = 365 + (1 if (today.year - 1) % 4 == 0 and (today.year - 1) % 100 != 0 or (today.year - 1) % 400 == 0 else 0)
        date_presets["last_year"] = {
            "start_date": last_year_start.strftime("%Y-%m-%d"),
            "end_date": last_year_end.strftime("%Y-%m-%d"),
            "description": f"Data for the entire {today.year - 1} year",
            "days": days_last_year
        }
        
        # Year-to-date
        ytd_start = datetime(today.year, 1, 1)
        days_ytd = (today - ytd_start).days + 1
        date_presets["year_to_date"] = {
            "start_date": ytd_start.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "description": f"Data from January 1, {today.year} to today",
            "days": days_ytd
        }
        
        # If a specific preset was requested, return only that one
        if preset and preset.lower() in date_presets:
            return json.dumps(date_presets[preset.lower()])
        
        # Otherwise, return all available presets with visualization data
        response = {
            "presets": date_presets,
            "visualization_data": {
                "chart_type": "table",
                "title": "Available Date Range Presets",
                "columns": [
                    {
                        "title": "Preset",
                        "dataKey": "preset",
                        "width": 150
                    },
                    {
                        "title": "Description",
                        "dataKey": "description",
                        "width": 250
                    },
                    {
                        "title": "Start Date",
                        "dataKey": "start_date",
                        "width": 120
                    },
                    {
                        "title": "End Date",
                        "dataKey": "end_date",
                        "width": 120
                    },
                    {
                        "title": "Days",
                        "dataKey": "days",
                        "width": 80,
                        "format": "number"
                    }
                ],
                "data": []
            }
        }
        
        # Build table data for visualization
        for key, range_data in date_presets.items():
            response["visualization_data"]["data"].append({
                "preset": key,
                "description": range_data["description"],
                "start_date": range_data["start_date"],
                "end_date": range_data["end_date"],
                "days": range_data["days"]
            })
        
        return json.dumps(response)
        
    except Exception as e:
        logger.error(f"Error getting date range presets in JSON format: {str(e)}")
        return json.dumps({
            "error": f"Unable to generate date range presets - {str(e)}"
        })

@mcp.tool()
async def get_ad_groups(start_date: str = None, end_date: str = None, campaign_id: str = None, customer_id: str = None):
    """
    Get performance metrics for Google Ads ad groups.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
        end_date: End date in YYYY-MM-DD format (defaults to today)
        campaign_id: Optional campaign ID to filter ad groups by
        customer_id: Specific customer/account ID to query (defaults to the one in .env file)
        
    Returns:
        A formatted report of ad group performance metrics
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        campaign_info = f", campaign ID {campaign_id}" if campaign_id else ""
        logger.info(f"Getting ad group performance for customer ID {customer_id or 'default'}{campaign_info}, date range: {start_date} to {end_date}")
        
        # Initialize Google Ads service and get ad group data
        service = GoogleAdsService()
        ad_groups = await service.get_ad_groups(start_date, end_date, campaign_id, customer_id)
        
        if not ad_groups:
            return "No ad groups found for the specified customer ID and date range."
        
        # Get the actual customer ID that was used (for display purposes)
        used_customer_id = customer_id or service.client_customer_id
        if used_customer_id:
            # Format with dashes for display
            if len(used_customer_id) == 10:
                used_customer_id = f"{used_customer_id[:3]}-{used_customer_id[3:6]}-{used_customer_id[6:]}"
        
        # Format the results as a text report
        report = [
            f"Google Ads Ad Group Performance Report",
            f"Account ID: {used_customer_id}",
            f"Date Range: {start_date} to {end_date}",
            f"Campaign Filter: {campaign_id if campaign_id else 'All Campaigns'}\n",
            f"{'Ad Group ID':<12} {'Ad Group Name':<30} {'Campaign':<20} {'Status':<10} {'Impressions':<12} {'Clicks':<8} {'Cost':<10} {'CTR':<8} {'CPC':<8}",
            "-" * 118
        ]
        
        # Add data rows
        for ad_group in sorted(ad_groups, key=lambda x: x["cost"], reverse=True):
            name = ad_group["name"]
            if len(name) > 27:
                name = name[:24] + "..."
                
            campaign_name = ad_group["campaign_name"]
            if len(campaign_name) > 17:
                campaign_name = campaign_name[:14] + "..."
                
            report.append(
                f"{ad_group['id']:<12} {name:<30} {campaign_name:<20} {ad_group['status']:<10} "
                f"{int(ad_group['impressions']):,d} {int(ad_group['clicks']):,d} "
                f"${ad_group['cost']:,.2f} {ad_group['ctr']:.2f}% ${ad_group['cpc']:.2f}"
            )
            
        return "\n".join(report)
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def get_ad_groups_json(start_date: str = None, end_date: str = None, campaign_id: str = None, customer_id: str = None):
    """
    Get performance metrics for Google Ads ad groups in JSON format for visualization.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
        end_date: End date in YYYY-MM-DD format (defaults to today)
        campaign_id: Optional campaign ID to filter ad groups by
        customer_id: Specific customer/account ID to query (defaults to the one in .env file)
        
    Returns:
        A JSON string containing ad group performance data for visualization
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        campaign_info = f", campaign ID {campaign_id}" if campaign_id else ""
        logger.info(f"Getting ad group performance for customer ID {customer_id or 'default'}{campaign_info}, date range: {start_date} to {end_date} (JSON format)")
        
        # Initialize Google Ads service and get ad group data
        service = GoogleAdsService()
        ad_groups = await service.get_ad_groups(start_date, end_date, campaign_id, customer_id)
        
        if not ad_groups:
            return json.dumps({"error": "No ad groups found for the specified customer ID and date range"})
        
        # Get the actual customer ID that was used
        used_customer_id = customer_id or service.client_customer_id
        
        # Prepare visualization data
        visualization_data = {
            "chart_type": "table",
            "title": "Ad Group Performance",
            "columns": [
                {
                    "title": "Ad Group ID",
                    "dataKey": "id",
                    "width": 100,
                    "format": "text"
                },
                {
                    "title": "Ad Group Name",
                    "dataKey": "name",
                    "width": 200,
                    "format": "text"
                },
                {
                    "title": "Campaign",
                    "dataKey": "campaign_name",
                    "width": 150,
                    "format": "text"
                },
                {
                    "title": "Status",
                    "dataKey": "status",
                    "width": 100,
                    "format": "text"
                },
                {
                    "title": "Impressions",
                    "dataKey": "impressions",
                    "width": 120,
                    "format": "number"
                },
                {
                    "title": "Clicks",
                    "dataKey": "clicks",
                    "width": 100,
                    "format": "number"
                },
                {
                    "title": "CTR",
                    "dataKey": "ctr",
                    "width": 80,
                    "format": "percent"
                },
                {
                    "title": "Cost",
                    "dataKey": "cost",
                    "width": 100,
                    "format": "currency"
                },
                {
                    "title": "CPC",
                    "dataKey": "cpc",
                    "width": 100,
                    "format": "currency"
                },
                {
                    "title": "Conversions",
                    "dataKey": "conversions",
                    "width": 120,
                    "format": "number"
                },
                {
                    "title": "Cost/Conv.",
                    "dataKey": "cost_per_conversion",
                    "width": 120,
                    "format": "currency"
                }
            ],
            "data": ad_groups,
            "pagination": true,
            "sortable": true,
            "defaultSort": "cost",
            "defaultSortDirection": "desc"
        }
        
        # Return JSON data
        return json.dumps({
            "customer_id": used_customer_id,
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            },
            "campaign_id": campaign_id,
            "ad_groups": ad_groups,
            "total_ad_groups": len(ad_groups),
            "visualization_data": visualization_data
        })
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return json.dumps({"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return json.dumps({"error": f"Unexpected error: {str(e)}"})

@mcp.tool()
async def create_ad_group(campaign_id: str, name: str, status: str = "ENABLED", cpc_bid: float = None, customer_id: str = None):
    """
    Create a new ad group in Google Ads.
    
    Args:
        campaign_id: The campaign ID where the ad group will be created
        name: The name of the ad group
        status: Ad group status (ENABLED, PAUSED, REMOVED) - defaults to ENABLED
        cpc_bid: Optional CPC bid in account currency (will be converted to micros)
        customer_id: Optional customer ID (defaults to the one in .env file)
        
    Returns:
        Operation status message
    """
    try:
        logger.info(f"Creating ad group '{name}' in campaign {campaign_id} for customer ID {customer_id or 'default'}")
        
        # Convert CPC bid to micros if provided
        cpc_bid_micros = None
        if cpc_bid is not None:
            cpc_bid_micros = int(cpc_bid * 1000000)  # Convert to micros
        
        # Initialize Google Ads service and create ad group
        service = GoogleAdsService()
        result = await service.create_ad_group(
            campaign_id=campaign_id,
            name=name,
            status=status,
            cpc_bid_micros=cpc_bid_micros,
            customer_id=customer_id
        )
        
        # Format the response
        response = [
            f"✅ Google Ads - Ad Group Created Successfully",
            f"Name: {name}",
            f"Campaign ID: {campaign_id}",
            f"Status: {status}"
        ]
        
        # Add CPC bid if provided
        if cpc_bid is not None:
            response.append(f"CPC Bid: ${cpc_bid:.2f}")
            
        # Add the customer ID info
        used_customer_id = customer_id or service.client_customer_id
        if used_customer_id:
            # Format with dashes for display
            if len(used_customer_id) == 10:
                used_customer_id = f"{used_customer_id[:3]}-{used_customer_id[3:6]}-{used_customer_id[6:]}"
            response.append(f"Customer ID: {used_customer_id}")
            
        # Add resource name if available
        if result.get("resource_name"):
            response.append(f"Resource Name: {result['resource_name']}")
            
        return "\n".join(response)
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return f"❌ Error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"❌ Unexpected error: {str(e)}"

@mcp.tool()
async def update_ad_group(ad_group_id: str, name: str = None, status: str = None, cpc_bid: float = None, customer_id: str = None):
    """
    Update an existing ad group in Google Ads.
    
    Args:
        ad_group_id: The ID of the ad group to update
        name: Optional new name for the ad group
        status: Optional new status (ENABLED, PAUSED, REMOVED)
        cpc_bid: Optional new CPC bid in account currency (will be converted to micros)
        customer_id: Optional customer ID (defaults to the one in .env file)
        
    Returns:
        Operation status message
    """
    try:
        logger.info(f"Updating ad group {ad_group_id} for customer ID {customer_id or 'default'}")
        
        # Convert CPC bid to micros if provided
        cpc_bid_micros = None
        if cpc_bid is not None:
            cpc_bid_micros = int(cpc_bid * 1000000)  # Convert to micros
        
        # Initialize Google Ads service and update ad group
        service = GoogleAdsService()
        result = await service.update_ad_group(
            ad_group_id=ad_group_id,
            name=name,
            status=status,
            cpc_bid_micros=cpc_bid_micros,
            customer_id=customer_id
        )
        
        # Format the response
        response = [
            f"✅ Google Ads - Ad Group Updated Successfully",
            f"Ad Group ID: {ad_group_id}",
            f"Updated Fields: {', '.join(result['updated_fields'])}"
        ]
        
        # Add specific field updates
        if name is not None:
            response.append(f"New Name: {name}")
        if status is not None:
            response.append(f"New Status: {status}")
        if cpc_bid is not None:
            response.append(f"New CPC Bid: ${cpc_bid:.2f}")
            
        # Add the customer ID info
        used_customer_id = customer_id or service.client_customer_id
        if used_customer_id:
            # Format with dashes for display
            if len(used_customer_id) == 10:
                used_customer_id = f"{used_customer_id[:3]}-{used_customer_id[3:6]}-{used_customer_id[6:]}"
            response.append(f"Customer ID: {used_customer_id}")
            
        # Add resource name if available
        if result.get("resource_name"):
            response.append(f"Resource Name: {result['resource_name']}")
            
        return "\n".join(response)
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return f"❌ Error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"❌ Unexpected error: {str(e)}"

@mcp.tool()
async def create_ad_group_json(campaign_id: str, name: str, status: str = "ENABLED", cpc_bid: float = None, customer_id: str = None):
    """
    Create a new ad group in Google Ads and return JSON result for visualization.
    
    Args:
        campaign_id: The campaign ID where the ad group will be created
        name: The name of the ad group
        status: Ad group status (ENABLED, PAUSED, REMOVED) - defaults to ENABLED
        cpc_bid: Optional CPC bid in account currency (will be converted to micros)
        customer_id: Optional customer ID (defaults to the one in .env file)
        
    Returns:
        JSON string with operation result for visualization
    """
    try:
        logger.info(f"Creating ad group '{name}' in campaign {campaign_id} for customer ID {customer_id or 'default'} (JSON format)")
        
        # Convert CPC bid to micros if provided
        cpc_bid_micros = None
        if cpc_bid is not None:
            cpc_bid_micros = int(cpc_bid * 1000000)  # Convert to micros
        
        # Initialize Google Ads service and create ad group
        service = GoogleAdsService()
        result = await service.create_ad_group(
            campaign_id=campaign_id,
            name=name,
            status=status,
            cpc_bid_micros=cpc_bid_micros,
            customer_id=customer_id
        )
        
        # Get the actual customer ID that was used
        used_customer_id = customer_id or service.client_customer_id
        
        # Create response
        response = {
            "status": "success",
            "action": "create_ad_group",
            "ad_group": {
                "name": name,
                "campaign_id": campaign_id,
                "status": status,
                "cpc_bid": cpc_bid,
                "resource_name": result.get("resource_name")
            },
            "customer_id": used_customer_id,
            "message": result.get("message", "Ad group created successfully"),
            "timestamp": datetime.now().isoformat(),
            "visualization_data": {
                "chart_type": "kpi_cards",
                "title": "Ad Group Creation",
                "data": [
                    {
                        "title": "Status",
                        "value": "Created",
                        "format": "string",
                        "color": "#82ca9d"
                    },
                    {
                        "title": "Ad Group Name",
                        "value": name,
                        "format": "string",
                        "color": "#8884d8"
                    },
                    {
                        "title": "Initial Status",
                        "value": status,
                        "format": "string",
                        "color": "#82ca9d" if status == "ENABLED" else "#ffc658"
                    }
                ],
                "layout": "horizontal",
                "card_width": 250,
                "card_height": 150
            }
        }
        
        return json.dumps(response)
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return json.dumps({
            "status": "error",
            "action": "create_ad_group",
            "campaign_id": campaign_id,
            "name": name,
            "customer_id": customer_id,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return json.dumps({
            "status": "error",
            "action": "create_ad_group",
            "campaign_id": campaign_id,
            "name": name,
            "customer_id": customer_id,
            "error": f"Unexpected error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })

@mcp.tool()
async def update_ad_group_json(ad_group_id: str, name: str = None, status: str = None, cpc_bid: float = None, customer_id: str = None):
    """
    Update an existing ad group in Google Ads and return JSON result for visualization.
    
    Args:
        ad_group_id: The ID of the ad group to update
        name: Optional new name for the ad group
        status: Optional new status (ENABLED, PAUSED, REMOVED)
        cpc_bid: Optional new CPC bid in account currency (will be converted to micros)
        customer_id: Optional customer ID (defaults to the one in .env file)
        
    Returns:
        JSON string with operation result for visualization
    """
    try:
        logger.info(f"Updating ad group {ad_group_id} for customer ID {customer_id or 'default'} (JSON format)")
        
        # Convert CPC bid to micros if provided
        cpc_bid_micros = None
        if cpc_bid is not None:
            cpc_bid_micros = int(cpc_bid * 1000000)  # Convert to micros
        
        # Initialize Google Ads service and update ad group
        service = GoogleAdsService()
        result = await service.update_ad_group(
            ad_group_id=ad_group_id,
            name=name,
            status=status,
            cpc_bid_micros=cpc_bid_micros,
            customer_id=customer_id
        )
        
        # Get the actual customer ID that was used
        used_customer_id = customer_id or service.client_customer_id
        
        # Determine status color
        status_color = "#ffc658"  # Default yellow for unknown
        if status == "ENABLED":
            status_color = "#82ca9d"  # Green
        elif status == "PAUSED":
            status_color = "#ffc658"  # Yellow
        elif status == "REMOVED":
            status_color = "#ff8042"  # Red/Orange
        
        # Create visualization cards based on what was updated
        kpi_cards = []
        
        if name is not None:
            kpi_cards.append({
                "title": "New Name",
                "value": name,
                "format": "string",
                "color": "#8884d8"
            })
            
        if status is not None:
            kpi_cards.append({
                "title": "New Status",
                "value": status,
                "format": "string",
                "color": status_color
            })
            
        if cpc_bid is not None:
            kpi_cards.append({
                "title": "New CPC Bid",
                "value": cpc_bid,
                "format": "currency",
                "color": "#82ca9d"
            })
        
        # Create response
        response = {
            "status": "success",
            "action": "update_ad_group",
            "ad_group_id": ad_group_id,
            "updated_fields": result.get("updated_fields", []),
            "customer_id": used_customer_id,
            "resource_name": result.get("resource_name"),
            "message": result.get("message", "Ad group updated successfully"),
            "timestamp": datetime.now().isoformat()
        }
        
        # Add updates if present
        updates = {}
        if name is not None:
            updates["name"] = name
        if status is not None:
            updates["status"] = status
        if cpc_bid is not None:
            updates["cpc_bid"] = cpc_bid
            
        if updates:
            response["updates"] = updates
            
        # Add visualization data if we have cards
        if kpi_cards:
            response["visualization_data"] = {
                "chart_type": "kpi_cards",
                "title": "Ad Group Update",
                "data": kpi_cards,
                "layout": "horizontal",
                "card_width": 250,
                "card_height": 150
            }
        
        return json.dumps(response)
        
    except GoogleAdsClientError as e:
        logger.error(f"Google Ads client error: {str(e)}")
        return json.dumps({
            "status": "error",
            "action": "update_ad_group",
            "ad_group_id": ad_group_id,
            "customer_id": customer_id,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return json.dumps({
            "status": "error",
            "action": "update_ad_group",
            "ad_group_id": ad_group_id,
            "customer_id": customer_id,
            "error": f"Unexpected error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })

@mcp.tool()
async def get_ad_group_performance_json(ad_group_id: str, start_date: str = None, end_date: str = None, customer_id: str = None):
    """
    Get performance metrics for a specific Google Ads ad group over time in JSON format for visualization.
    
    Args:
        ad_group_id: The ID of the ad group to get performance for
        start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
        end_date: End date in YYYY-MM-DD format (defaults to today)
        customer_id: Specific customer/account ID to query (defaults to the one in .env file)
        
    Returns:
        A JSON string containing ad group performance data for visualization
    """
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        logger.info(f"Getting performance for ad group {ad_group_id}, customer ID {customer_id or 'default'}, date range: {start_date} to {end_date} (JSON format)")
        
        # Initialize Google Ads service and get ad group data
        service = GoogleAdsService()
        
        # First get the ad group data to know the name and campaign
        ad_groups = await service.get_ad_groups(start_date, end_date, None, customer_id)
        ad_group_data = next((ag for ag in ad_groups if ag["id"] == ad_group_id), None)
        
        if not ad_group_data:
            return json.dumps({"error": f"Ad group with ID {ad_group_id} not found"})
        
        # Then get the daily performance data for this ad group
        daily_stats = await service.get_ad_group_daily_stats(ad_group_id, start_date, end_date, customer_id)
        
        if not daily_stats:
            return json.dumps({"error": f"No daily performance data found for ad group {ad_group_id}"})
        
        # Get the actual customer ID that was used
        used_customer_id = customer_id or service.client_customer_id
        
        # Create time series visualization data
        time_series_data = {
            "chart_type": "time_series",
            "title": f"Ad Group Performance: {ad_group_data['name']}",
            "subtitle": f"Daily metrics from {start_date} to {end_date}",
            "data": daily_stats,
            "axes": {
                "x": {
                    "label": "Date",
                    "dataKey": "date",
                    "type": "category"
                },
                "y": {
                    "label": "Value",
                    "type": "number"
                }
            },
            "series": [
                {
                    "name": "Impressions",
                    "dataKey": "impressions",
                    "color": "#8884d8",
                    "type": "line",
                    "yAxisId": "impressions"
                },
                {
                    "name": "Clicks",
                    "dataKey": "clicks",
                    "color": "#82ca9d",
                    "type": "line",
                    "yAxisId": "clicks"
                },
                {
                    "name": "Cost ($)",
                    "dataKey": "cost",
                    "color": "#ffc658",
                    "type": "line",
                    "yAxisId": "cost"
                },
                {
                    "name": "Conversions",
                    "dataKey": "conversions",
                    "color": "#ff8042",
                    "type": "line",
                    "yAxisId": "conversions"
                }
            ],
            "legend": True,
            "grid": True,
            "tooltip": True
        }
        
        # Create KPI summary cards
        # Calculate totals
        total_impressions = sum(day["impressions"] for day in daily_stats)
        total_clicks = sum(day["clicks"] for day in daily_stats)
        total_cost = sum(day["cost"] for day in daily_stats)
        total_conversions = sum(day["conversions"] for day in daily_stats)
        
        # Calculate averages and rates
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        avg_cpc = total_cost / total_clicks if total_clicks > 0 else 0
        conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        cost_per_conversion = total_cost / total_conversions if total_conversions > 0 else 0
        
        kpi_cards_data = {
            "chart_type": "kpi_cards",
            "title": "Ad Group Summary Metrics",
            "data": [
                {
                    "title": "Impressions",
                    "value": total_impressions,
                    "format": "number",
                    "color": "#8884d8"
                },
                {
                    "title": "Clicks",
                    "value": total_clicks,
                    "format": "number",
                    "color": "#82ca9d"
                },
                {
                    "title": "CTR",
                    "value": avg_ctr,
                    "format": "percent",
                    "color": "#ffc658"
                },
                {
                    "title": "Cost",
                    "value": total_cost,
                    "format": "currency",
                    "color": "#ff8042"
                },
                {
                    "title": "CPC",
                    "value": avg_cpc,
                    "format": "currency",
                    "color": "#8884d8"
                },
                {
                    "title": "Conversions",
                    "value": total_conversions,
                    "format": "number",
                    "color": "#82ca9d"
                },
                {
                    "title": "Conv. Rate",
                    "value": conversion_rate,
                    "format": "percent",
                    "color": "#ffc658"
                },
                {
                    "title": "Cost/Conv.",
                    "value": cost_per_conversion,
                    "format": "currency",
                    "color": "#ff8042"
                }
            ],
            "layout": "horizontal",
            "card_width": 150,
            "card_height": 120
        }
        
        # Return JSON data with multiple visualizations
        return json.dumps({
            "customer_id": used_customer_id,
            "ad_group": ad_group_data,
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            },
            "daily_stats": daily_stats,
            "visualizations": {
                "time_series": time_series_data,
                "kpi_cards": kpi_cards_data
            }
        })
        
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
    port = int(os.environ.get("PORT", "8000"))
    logger.info(f"Server will be available at http://localhost:{port}")
    logger.info(f"Health check endpoint: http://localhost:{port}/health")
    logger.info(f"MCP server will be available at http://localhost:{port}/mcp")
    if os.environ.get("ENABLE_METRICS", "false").lower() == "true":
        logger.info(f"Metrics endpoint: http://localhost:{port}/metrics")
    uvicorn.run(app, host="0.0.0.0", port=port) 