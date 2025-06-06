# SAGE-Viz: Time Series Visualization Enhancement for Google Ads KPI
**Date: 2025-03-17**

## Overview
This document provides the complete implementation of time series visualization functionality for the Google Ads KPI MCP Server. It includes the missing `_format_time_series` method and completes the server.py implementation, enabling effective visualization of Google Ads performance data in Claude Artifacts.

## 1. The `_format_time_series` Method

### 1.1 Purpose
The `_format_time_series` method transforms raw Google Ads KPI data into a structured format optimized for time series visualization in Claude Artifacts. This method:
- Groups metrics by date
- Aggregates multiple campaign data points for each date
- Formats data for compatibility with common charting libraries
- Provides appropriate metadata for axis labels and titles

### 1.2 Implementation
```python
def _format_time_series(kpi_data):
    """Format KPI data for time series visualization.
    
    Args:
        kpi_data: List of daily KPI data points.
        
    Returns:
        Dictionary with time series data formatted for visualization.
    """
    # Group by date
    dates = {}
    for item in kpi_data:
        date = item.get("date")
        if not date:
            continue
            
        if date not in dates:
            dates[date] = {
                "date": date,
                "cost": 0,
                "conversions": 0,
                "clicks": 0,
                "impressions": 0
            }
        
        # Aggregate metrics for this date
        dates[date]["cost"] += item.get("cost", 0)
        dates[date]["conversions"] += item.get("conversions", 0)
        dates[date]["clicks"] += item.get("clicks", 0)
        dates[date]["impressions"] += item.get("impressions", 0)
    
    # Convert to sorted list
    time_series = list(dates.values())
    time_series.sort(key=lambda x: x["date"])
    
    # Prepare data for visualization in Recharts format
    recharts_data = []
    for data_point in time_series:
        recharts_data.append({
            "name": data_point["date"],
            "Cost": round(data_point["cost"], 2),
            "Conversions": round(data_point["conversions"], 2),
            "Clicks": data_point["clicks"],
            "Impressions": data_point["impressions"] / 1000  # Scale for better visualization
        })
    
    return {
        "title": "Daily Performance Metrics",
        "data": recharts_data,
        "description": f"Performance trends from {time_series[0]['date'] if time_series else 'N/A'} to {time_series[-1]['date'] if time_series else 'N/A'}",
        "labels": {
            "x": "Date",
            "y": "Value",
            "series": ["Cost", "Conversions", "Clicks", "Impressions (thousands)"]
        },
        "chartType": "line",  # Recommend line chart for time series
        "raw_data": time_series  # Include raw data for potential custom processing
    }
```

## 2. Complete Server.py Tool Handler

The `handle_call_tool` method in server.py needs to be completed to properly use the `_format_time_series` method. Here's the completed implementation for this section:

```python
@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests for Google Ads operations.
    """
    if not arguments and name != "clear-kpi-cache":
        raise ValueError("Missing arguments")

    client = None
    try:
        client = get_google_ads_client()
        
        if name == "get-google-ads-kpis":
            customer_id = arguments.get("customer_id")
            start_date = arguments.get("start_date")
            end_date = arguments.get("end_date")
            segmentation = arguments.get("segmentation", [])
            campaign_type = arguments.get("campaign_type")
            campaign_name = arguments.get("campaign_name")
            campaign_label = arguments.get("campaign_label")
            
            if not customer_id or not start_date or not end_date:
                raise ValueError("Missing required arguments: customer_id, start_date, end_date")
                        
            # Fetch KPI data
            data = client.get_kpis(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date,
                segmentation=segmentation,
                campaign_type=campaign_type,
                campaign_name=campaign_name,
                campaign_label=campaign_label,
            )
            
            # Create cache key
            cache_key = f"{customer_id}_{start_date}_{end_date}"
            if segmentation:
                cache_key += f"_{'_'.join(segmentation)}"
            if campaign_type:
                cache_key += f"_{campaign_type}"
            if campaign_name:
                cache_key += f"_{campaign_name}"
            if campaign_label:
                cache_key += f"_{campaign_label}"
            
            # Format time series data if available
            time_series_viz = None
            if data.get("kpi_data"):
                time_series_viz = _format_time_series(data["kpi_data"])
            
            # Create a summary for the response with visualization-ready format
            summary = {
                "summary": data["summary"],
                "date_range": data["date_range"],
                "metadata": data["metadata"],
                "kpi_data_count": len(data.get("kpi_data", [])),
                "resource_uri": f"google-ads://kpi/{cache_key}",
                # Add visualization-ready data
                "visualization": {
                    "bar_chart": {
                        "title": f"Google Ads KPIs for {customer_id} ({start_date} to {end_date})",
                        "data": [
                            {"key": "Cost", "value": data["summary"]["total_cost"]},
                            {"key": "Conversions", "value": data["summary"]["total_conversions"]},
                            {"key": "Clicks", "value": data["summary"]["total_clicks"]},
                            {"key": "Impressions", "value": data["summary"]["total_impressions"] / 1000}  # Scale for better visualization
                        ],
                        "labels": {"x": "Metric", "y": "Value"}
                    },
                    "time_series": time_series_viz
                }
            }
            
            # Notify clients that resources have changed
            await server.request_context.session.send_resource_list_changed()
            
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(summary, indent=2),
                )
            ]
            
        elif name == "get-google-ads-comparison":
            customer_id = arguments.get("customer_id")
            current_start_date = arguments.get("current_start_date")
            current_end_date = arguments.get("current_end_date")
            previous_start_date = arguments.get("previous_start_date")
            previous_end_date = arguments.get("previous_end_date")
            segmentation = arguments.get("segmentation", [])
            campaign_type = arguments.get("campaign_type")
            campaign_name = arguments.get("campaign_name")
            campaign_label = arguments.get("campaign_label")
            
            if not customer_id or not current_start_date or not current_end_date:
                raise ValueError("Missing required arguments: customer_id, current_start_date, current_end_date")
            
            # Fetch period comparison data
            data = client.get_period_comparison(
                customer_id=customer_id,
                current_start_date=current_start_date,
                current_end_date=current_end_date,
                previous_start_date=previous_start_date,
                previous_end_date=previous_end_date,
                segmentation=segmentation,
                campaign_type=campaign_type,
                campaign_name=campaign_name,
                campaign_label=campaign_label,
            )
            
            # Create cache key
            cache_key = f"comparison_{customer_id}_{current_start_date}_{current_end_date}"
            if previous_start_date and previous_end_date:
                cache_key += f"_{previous_start_date}_{previous_end_date}"
            if segmentation:
                cache_key += f"_{'_'.join(segmentation)}"
            if campaign_type:
                cache_key += f"_{campaign_type}"
            if campaign_name:
                cache_key += f"_{campaign_name}"
            if campaign_label:
                cache_key += f"_{campaign_label}"
            
            # Format visualization data for Claude Artifacts
            recharts_comparison_data = []
            for idx, metric in enumerate(["Cost", "Conversions", "Clicks", "Impressions", "CTR"]):
                if metric == "CTR":
                    # Convert to percentage for display
                    current_value = data["current_period"]["summary"]["avg_ctr"] * 100
                    previous_value = data["previous_period"]["summary"]["avg_ctr"] * 100
                    change_pct = data["change"]["ctr"]["percentage"]
                else:
                    metric_key = metric.lower()
                    current_value = data["current_period"]["summary"][f"total_{metric_key}"]
                    previous_value = data["previous_period"]["summary"][f"total_{metric_key}"]
                    change_pct = data["change"][metric_key]["percentage"]
                
                recharts_comparison_data.append({
                    "name": metric,
                    "Current": current_value,
                    "Previous": previous_value,
                    "Change": change_pct
                })
            
            # Create a summary for the response with visualization-ready format
            summary = {
                "current_period": {
                    "date_range": data["metadata"]["current_period"],
                    "summary": data["current_period"]["summary"],
                },
                "previous_period": {
                    "date_range": data["metadata"]["previous_period"],
                    "summary": data["previous_period"]["summary"],
                },
                "change": data["change"],
                "resource_uri": f"google-ads://kpi/{cache_key}",
                # Add visualization-ready data
                "visualization": {
                    "comparison_chart": {
                        "title": f"Period Comparison for {customer_id}",
                        "subtitle": f"{data['metadata']['current_period']['start_date']} to {data['metadata']['current_period']['end_date']} vs. {data['metadata']['previous_period']['start_date']} to {data['metadata']['previous_period']['end_date']}",
                        "data": recharts_comparison_data,
                        "labels": {
                            "x": "Metric",
                            "y": "Value",
                            "current": f"{data['metadata']['current_period']['start_date']} to {data['metadata']['current_period']['end_date']}",
                            "previous": f"{data['metadata']['previous_period']['start_date']} to {data['metadata']['previous_period']['end_date']}"
                        },
                        "chartType": "barGroup"  # Recommend grouped bar chart for comparison
                    }
                }
            }
            
            # Add campaign visualization if available
            if data.get("campaign_changes"):
                # Get top campaigns by absolute change
                top_campaigns = sorted(
                    [c for c in data["campaign_changes"] if not c.get("is_new", False)],
                    key=lambda x: abs(x["changes"]["cost"]["absolute"]),
                    reverse=True
                )[:5]
                
                if top_campaigns:
                    campaign_data = []
                    for camp in top_campaigns:
                        campaign_data.append({
                            "name": camp["campaign_name"][:20] + ("..." if len(camp["campaign_name"]) > 20 else ""),
                            "Cost": camp["changes"]["cost"]["percentage"],
                            "Conversions": camp["changes"]["conversions"]["percentage"] if "conversions" in camp["changes"] else 0,
                            "Clicks": camp["changes"]["clicks"]["percentage"] if "clicks" in camp["changes"] else 0
                        })
                    
                    summary["visualization"]["campaign_changes"] = {
                        "title": "Top Campaign Changes",
                        "data": campaign_data,
                        "labels": {
                            "x": "Campaign",
                            "y": "% Change"
                        },
                        "chartType": "bar"
                    }
            
            # Notify clients that resources have changed
            await server.request_context.session.send_resource_list_changed()
            
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(summary, indent=2),
                )
            ]
            
        elif name == "clear-kpi-cache":
            # Clear the KPI cache
            success = client.clear_cache()
            
            # Notify clients that resources have changed
            await server.request_context.session.send_resource_list_changed()
            
            return [
                types.TextContent(
                    type="text",
                    text=f"KPI cache cleared {'successfully' if success else 'with errors'}.",
                )
            ]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except (ValueError, GoogleAdsClientError) as e:
        return [
            types.TextContent(
                type="text",
                text=f"Error: {str(e)}",
            )
        ]
    finally:
        # Ensure we close the client connection
        if client:
            client.close()
```

## 3. Complete Server Implementation

The full working server.py file (with the added `_format_time_series` function and proper imports) should be:

```python
import asyncio
import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio

from google_mcp_server.google_ads_client import GoogleAdsClient, GoogleAdsClientError
from google_mcp_server.database_manager import DatabaseManager

# Initialize the Google Ads client with environment variables
def get_google_ads_client():
    """Create and return a GoogleAdsClient instance using environment variables for authentication."""
    try:
        # Get the database path from environment or use default
        db_path = os.environ.get("GOOGLE_ADS_DB_PATH", "cache.db")
        
        # Get cache max age from environment or use default (15 minutes)
        cache_max_age_minutes = int(os.environ.get("GOOGLE_ADS_CACHE_MAX_AGE_MINUTES", "15"))
        
        # First check if we have all required env vars for direct authentication
        if (os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN") and 
            os.environ.get("GOOGLE_ADS_CLIENT_ID") and
            os.environ.get("GOOGLE_ADS_CLIENT_SECRET") and
            os.environ.get("GOOGLE_ADS_REFRESH_TOKEN")):
            
            return GoogleAdsClient(
                developer_token=os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN"),
                client_id=os.environ.get("GOOGLE_ADS_CLIENT_ID"),
                client_secret=os.environ.get("GOOGLE_ADS_CLIENT_SECRET"),
                refresh_token=os.environ.get("GOOGLE_ADS_REFRESH_TOKEN"),
                login_customer_id=os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
                version="v15",  # Using a stable version
                db_path=db_path,
                cache_max_age_minutes=cache_max_age_minutes,
            )
        # Fall back to config file if direct auth is not possible
        elif os.environ.get("GOOGLE_ADS_CONFIG_PATH"):
            return GoogleAdsClient(
                developer_token=os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN"),
                config_path=os.environ.get("GOOGLE_ADS_CONFIG_PATH"),
                version="v15",
                db_path=db_path,
                cache_max_age_minutes=cache_max_age_minutes,
            )
        else:
            raise ValueError(
                "Missing Google Ads API credentials. Please set the required environment variables or "
                "provide a config file path in GOOGLE_ADS_CONFIG_PATH."
            )
    except Exception as e:
        raise ValueError(f"Failed to initialize Google Ads client: {e}")

# Initialize the database manager for accessing cached data
db_manager = DatabaseManager(db_path=os.environ.get("GOOGLE_ADS_DB_PATH", "cache.db"))

server = Server("google-ads-mcp-server")

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    List available resources.
    """
    resources = []
    
    try:
        # Connect to the database
        conn = sqlite3.connect(os.environ.get("GOOGLE_ADS_DB_PATH", "cache.db"))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query all cache entries
        cursor.execute(
            "SELECT cache_key, account_id, start_date, end_date FROM account_kpi_cache"
        )
        
        # Create a resource for each cache entry
        for row in cursor.fetchall():
            resources.append(
                types.Resource(
                    uri=AnyUrl(f"google-ads://kpi/{row['cache_key']}"),
                    name=f"Google Ads KPI: {row['account_id']} ({row['start_date']} to {row['end_date']})",
                    description=f"Google Ads KPI data for account {row['account_id']} from {row['start_date']} to {row['end_date']}",
                    mimeType="application/json",
                )
            )
        
        conn.close()
    except sqlite3.Error as e:
        # If database access fails, just return an empty resource list
        pass
    
    return resources

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """
    Read a specific resource by its URI.
    For Google Ads KPI data, the resource URI is in the format google-ads://kpi/{cache_key}.
    """
    if uri.scheme != "google-ads":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    path = uri.path
    if path.startswith("/kpi/"):
        cache_key = path[5:]  # Remove "/kpi/" prefix
        kpi_data = db_manager.get_kpi_data(cache_key)
        
        if kpi_data:
            return json.dumps(kpi_data, indent=2)
    
    raise ValueError(f"Resource not found: {path}")

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """
    List available prompts.
    """
    return [
        types.Prompt(
            name="google-ads-kpi-analysis",
            description="Analyze Google Ads KPI data",
            arguments=[
                types.PromptArgument(
                    name="customer_id",
                    description="Google Ads customer ID",
                    required=True,
                ),
                types.PromptArgument(
                    name="start_date",
                    description="Start date (YYYY-MM-DD)",
                    required=True,
                ),
                types.PromptArgument(
                    name="end_date",
                    description="End date (YYYY-MM-DD)",
                    required=True,
                ),
                types.PromptArgument(
                    name="comparison_period",
                    description="Include previous period comparison (yes/no)",
                    required=False,
                ),
            ],
        )
    ]

@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """
    Generate a prompt based on Google Ads KPI data.
    """
    if name != "google-ads-kpi-analysis":
        raise ValueError(f"Unknown prompt: {name}")

    if not arguments:
        raise ValueError("Missing required arguments")

    customer_id = arguments.get("customer_id")
    start_date = arguments.get("start_date")
    end_date = arguments.get("end_date")
    comparison_period = arguments.get("comparison_period", "no").lower() == "yes"

    if not customer_id or not start_date or not end_date:
        raise ValueError("Missing required arguments: customer_id, start_date, end_date")

    try:
        client = get_google_ads_client()
        
        if comparison_period:
            # Get period comparison data
            data = client.get_period_comparison(
                customer_id=customer_id,
                current_start_date=start_date,
                current_end_date=end_date,
            )
            
            # Create cache key
            cache_key = f"comparison_{customer_id}_{start_date}_{end_date}"
            
            # Create a prompt message with the data
            return types.GetPromptResult(
                description=f"Google Ads KPI analysis for {customer_id} with period comparison",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"""Analyze the following Google Ads KPI data for customer ID {customer_id}:

Current period: {start_date} to {end_date}
Previous period: {data['metadata']['previous_period']['start_date']} to {data['metadata']['previous_period']['end_date']}

Current period metrics:
- Cost: ${data['current_period']['summary']['total_cost']:.2f}
- Conversions: {data['current_period']['summary']['total_conversions']:.2f}
- Conversion Value: ${data['current_period']['summary']['total_conversion_value']:.2f}
- Clicks: {data['current_period']['summary']['total_clicks']}
- Impressions: {data['current_period']['summary']['total_impressions']}
- CTR: {data['current_period']['summary']['avg_ctr'] * 100:.2f}%

Changes from previous period:
- Cost: {data['change']['cost']['percentage']:.2f}% (${data['change']['cost']['absolute']:.2f})
- Conversions: {data['change']['conversions']['percentage']:.2f}% ({data['change']['conversions']['absolute']:.2f})
- Conversion Value: {data['change']['conversion_value']['percentage']:.2f}% (${data['change']['conversion_value']['absolute']:.2f})
- Clicks: {data['change']['clicks']['percentage']:.2f}% ({data['change']['clicks']['absolute']})
- Impressions: {data['change']['impressions']['percentage']:.2f}% ({data['change']['impressions']['absolute']})
- CTR: {data['change']['ctr']['percentage']:.2f}% ({data['change']['ctr']['absolute'] * 100:.2f} percentage points)

Please provide a comprehensive analysis of this Google Ads performance data, including insights on:
1. Overall performance trends
2. Key metrics that improved or declined significantly
3. Potential factors contributing to these changes
4. Recommendations for optimization

The full data is available as a resource at google-ads://kpi/{cache_key}
""",
                        ),
                    )
                ],
            )
        else:
            # Get KPI data without comparison
            data = client.get_kpis(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date,
            )
            
            # Create cache key
            cache_key = f"{customer_id}_{start_date}_{end_date}"
            
            # Create a prompt message with the data
            return types.GetPromptResult(
                description=f"Google Ads KPI analysis for {customer_id}",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"""Analyze the following Google Ads KPI data for customer ID {customer_id} from {start_date} to {end_date}:

- Cost: ${data['summary']['total_cost']:.2f}
- Conversions: {data['summary']['total_conversions']:.2f}
- Conversion Value: ${data['summary']['total_conversion_value']:.2f}
- Clicks: {data['summary']['total_clicks']}
- Impressions: {data['summary']['total_impressions']}
- CTR: {data['summary']['avg_ctr'] * 100:.2f}%

Please provide a comprehensive analysis of this Google Ads performance data, including insights on:
1. Overall performance assessment
2. Key metrics that stand out
3. Recommendations for optimization

The full data is available as a resource at google-ads://kpi/{cache_key}
""",
                        ),
                    )
                ],
            )
    except (ValueError, GoogleAdsClientError) as e:
        return types.GetPromptResult(
            description="Error retrieving Google Ads KPI data",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"Failed to retrieve Google Ads KPI data: {str(e)}",
                    ),
                )
            ],
        )
    finally:
        if 'client' in locals():
            client.close()

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools related to Google Ads.
    """
    return [
        types.Tool(
            name="get-google-ads-kpis",
            description="Retrieve Google Ads KPIs for a specified date range",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                    "segmentation": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["campaign_type", "campaign_name", "campaign_label"]},
                    },
                    "campaign_type": {"type": "string"},
                    "campaign_name": {"type": "string"},
                    "campaign_label": {"type": "string"},
                },
                "required": ["customer_id", "start_date", "end_date"],
            },
        ),
        types.Tool(
            name="get-google-ads-comparison",
            description="Compare Google Ads KPIs between two time periods",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "current_start_date": {"type": "string", "format": "date"},
                    "current_end_date": {"type": "string", "format": "date"},
                    "previous_start_date": {"type": "string", "format": "date"},
                    "previous_end_date": {"type": "string", "format": "date"},
                    "segmentation": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["campaign_type", "campaign_name", "campaign_label"]},
                    },
                    "campaign_type": {"type": "string"},
                    "campaign_name": {"type": "string"},
                    "campaign_label": {"type": "string"},
                },
                "required": ["customer_id", "current_start_date", "current_end_date"],
            },
        ),
        types.Tool(
            name="clear-kpi-cache",
            description="Clear the KPI data cache",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]

def _format_time_series(kpi_data):
    """Format KPI data for time series visualization.
    
    Args:
        kpi_data: List of daily KPI data points.
        
    Returns:
        Dictionary with time series data formatted for visualization.
    """
    # Group by date
    dates = {}
    for item in kpi_data:
        date = item.get("date")
        if not date:
            continue
            
        if date not in dates:
            dates[date] = {
                "date": date,
                "cost": 0,
                "conversions": 0,
                "clicks": 0,
                "impressions": 0
            }
        
        # Aggregate metrics for this date
        dates[date]["cost"] += item.get("cost", 0)
        dates[date]["conversions"] += item.get("conversions", 0)
        dates[date]["clicks"] += item.get("clicks", 0)
        dates[date]["impressions"] += item.get("impressions", 0)
    
    # Convert to sorted list
    time_series = list(dates.values())
    time_series.sort(key=lambda x: x["date"])
    
    # Prepare data for visualization in Recharts format
    recharts_data = []
    for data_point in time_series:
        recharts_data.append({
            "name": data_point["date"],
            "Cost": round(data_point["cost"], 2),
            "Conversions": round(data_point["conversions"], 2),
            "Clicks": data_point["clicks"],
            "Impressions": data_point["impressions"] / 1000  # Scale for better visualization
        })
    
    return {
        "title": "Daily Performance Metrics",
        "data": recharts_data,
        "description": f"Performance trends from {time_series[0]['date'] if time_series else 'N/A'} to {time_series[-1]['date'] if time_series else 'N/A'}",
        "labels": {
            "x": "Date",
            "y": "Value",
            "series": ["Cost", "Conversions", "Clicks", "Impressions (thousands)"]
        },
        "chartType": "line",  # Recommend line chart for time series
        "raw_data": time_series  # Include raw data for potential custom processing
    }

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests for Google Ads operations.
    """
    if not arguments and name != "clear-kpi-cache":
        raise ValueError("Missing arguments")

    client = None
    try:
        client = get_google_ads_client()
        
        if name == "get-google-ads-kpis":
            customer_id = arguments.get("customer_id")
            start_date = arguments.get("start_date")
            end_date = arguments.get("end_date")
            segmentation = arguments.get("segmentation", [])
            campaign_type = arguments.get("campaign_type")
            campaign_name = arguments.get("campaign_name")
            campaign_label = arguments.get("campaign_label")
            
            if not customer_id or not start_date or not end_date:
                raise ValueError("Missing required arguments: customer_id, start_date, end_date")
                        
            # Fetch KPI data
            data = client.get_kpis(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date,
                segmentation=segmentation,
                campaign_type=campaign_type,
                campaign_name=campaign_name,
                campaign_label=campaign_label,
            )
            
            # Create cache key
            cache_key = f"{customer_id}_{start_date}_{end_date}"
            if segmentation:
                cache_key += f"_{'_'.join(segmentation)}"
            if campaign_type:
                cache_key += f"_{campaign_type}"
            if campaign_name:
                cache_key += f"_{campaign_name}"
            if campaign_label:
                cache_key += f"_{campaign_label}"
            
            # Format time series data if available
            time_series_viz = None
            if data.get("kpi_data"):
                time_series_viz = _format_time_series(data["kpi_data"])
            
            # Create a summary for the response with visualization-ready format
            summary = {
                "summary": data["summary"],
                "date_range": data["date_range"],
                "metadata": data["metadata"],
                "kpi_data_count": len(data.get("kpi_data", [])),
                "resource_uri": f"google-ads://kpi/{cache_key}",
                # Add visualization-ready data
                "visualization": {
                    "bar_chart": {
                        "title": f"Google Ads KPIs for {customer_id} ({start_date} to {end_date})",
                        "data": [
                            {"key": "Cost", "value": data["summary"]["total_cost"]},
                            {"key": "Conversions", "value": data["summary"]["total_conversions"]},
                            {"key": "Clicks", "value": data["summary"]["total_clicks"]},
                            {"key": "Impressions", "value": data["summary"]["total_impressions"] / 1000}  # Scale for better visualization
                        ],
                        "labels": {"x": "Metric", "y": "Value"}
                    },
                    "time_series": time_series_viz
                }
            }
            
            # Notify clients that resources have changed
            await server.request_context.session.send_resource_list_changed()
            
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(summary, indent=2),
                )
            ]
            
        elif name == "get-google-ads-comparison":
            customer_id = arguments.get("customer_id")
            current_start_date = arguments.get("current_start_date")
            current_end_date = arguments.get("current_end_date")
            previous_start_date = arguments.get("previous_start_date")
            previous_end_date = arguments.get("previous_end_date")
            segmentation = arguments.get("segmentation", [])
            campaign_type = arguments.get("campaign_type")
            campaign_name = arguments.get("campaign_name")
            campaign_label = arguments.get("campaign_label")
            
            if not customer_id or not current_start_date or not current_end_date:
                raise ValueError("Missing required arguments: customer_id, current_start_date, current_end_date")
            
            # Fetch period comparison data
            data = client.get_period_comparison(
                customer_id=customer_id,
                current_start_date=current_start_date,
                current_end_date=current_end_date,
                previous_start_date=previous_start_date,
                previous_end_date=previous_end_date,
                segmentation=segmentation,
                campaign_type=campaign_type,
                campaign_name=campaign_name,
                campaign_label=campaign_label,
            )
            
            # Create cache key
            cache_key = f"comparison_{customer_id}_{current_start_date}_{current_end_date}"
            if previous_start_date and previous_end_date:
                cache_key += f"_{previous_start_date}_{previous_end_date}"
            if segmentation:
                cache_key += f"_{'_'.join(segmentation)}"
            if campaign_type:
                cache_key += f"_{campaign_type}"
            if campaign_name:
                cache_key += f"_{campaign_name}"
            if campaign_label:
                cache_key += f"_{campaign_label}"
            
            # Format visualization data for Claude Artifacts
            recharts_comparison_data = []
            for idx, metric in enumerate(["Cost", "Conversions", "Clicks", "Impressions", "CTR"]):
                if metric == "CTR":
                    # Convert to percentage for display
                    current_value = data["current_period"]["summary"]["avg_ctr"] * 100
                    previous_value = data["previous_period"]["summary"]["avg_ctr"] * 100
                    change_pct = data["change"]["ctr"]["percentage"]
                else:
                    metric_key = metric.lower()
                    current_value = data["current_period"]["summary"][f"total_{metric_key}"]
                    previous_value = data["previous_period"]["summary"][f"total_{metric_key}"]
                    change_pct = data["change"][metric_key]["percentage"]
                
                recharts_comparison_data.append({
                    "name": metric,
                    "Current": current_value,
                    "Previous": previous_value,
                    "Change": change_pct
                })
            
            # Create a summary for the response with visualization-ready format
            summary = {
                "current_period": {
                    "date_range": data["metadata"]["current_period"],
                    "summary": data["current_period"]["summary"],
                },
                "previous_period": {
                    "date_range": data["metadata"]["previous_period"],
                    "summary": data["previous_period"]["summary"],
                },
                "change": data["change"],
                "resource_uri": f"google-ads://kpi/{cache_key}",
                # Add visualization-ready data
                "visualization": {
                    "comparison_chart": {
                        "title": f"Period Comparison for {customer_id}",
                        "subtitle": f"{data['metadata']['current_period']['start_date']} to {data['metadata']['current_period']['end_date']} vs. {data['metadata']['previous_period']['start_date']} to {data['metadata']['previous_period']['end_date']}",
                        "data": recharts_comparison_data,
                        "labels": {
                            "x": "Metric",
                            "y": "Value",
                            "current": f"{data['metadata']['current_period']['start_date']} to {data['metadata']['current_period']['end_date']}",
                            "previous": f"{data['metadata']['previous_period']['start_date']} to {data['metadata']['previous_period']['end_date']}"
                        },
                        "chartType": "barGroup"  # Recommend grouped bar chart for comparison
                    }
                }
            }
            
            # Add campaign visualization if available
            if data.get("campaign_changes"):
                # Get top campaigns by absolute change
                top_campaigns = sorted(
                    [c for c in data["campaign_changes"] if not c.get("is_new", False)],
                    key=lambda x: abs(x["changes"]["cost"]["absolute"]),
                    reverse=True
                )[:5]
                
                if top_campaigns:
                    campaign_data = []
                    for camp in top_campaigns:
                        campaign_data.append({
                            "name": camp["campaign_name"][:20] + ("..." if len(camp["campaign_name"]) > 20 else ""),
                            "Cost": camp["changes"]["cost"]["percentage"],
                            "Conversions": camp["changes"]["conversions"]["percentage"] if "conversions" in camp["changes"] else 0,
                            "Clicks": camp["changes"]["clicks"]["percentage"] if "clicks" in camp["changes"] else 0
                        })
                    
                    summary["visualization"]["campaign_changes"] = {
                        "title": "Top Campaign Changes",
                        "data": campaign_data,
                        "labels": {
                            "x": "Campaign",
                            "y": "% Change"
                        },
                        "chartType": "bar"
                    }
            
            # Notify clients that resources have changed
            await server.request_context.session.send_resource_list_changed()
            
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(summary, indent=2),
                )
            ]
            
        elif name == "clear-kpi-cache":
            # Clear the KPI cache
            success = client.clear_cache()
            
            # Notify clients that resources have changed
            await server.request_context.session.send_resource_list_changed()
            
            return [
                types.TextContent(
                    type="text",
                    text=f"KPI cache cleared {'successfully' if success else 'with errors'}.",
                )
            ]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except (ValueError, GoogleAdsClientError) as e:
        return [
            types.TextContent(
                type="text",
                text=f"Error: {str(e)}",
            )
        ]
    finally:
        # Ensure we close the client connection
        if client:
            client.close()

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="google-ads-mcp-server",
                server_version="0.1",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
```

## 4. Visualization Capabilities

The enhanced implementation provides several key visualization capabilities:

### 4.1 Time Series Visualization
- Daily performance metrics tracking
- Properly formatted for line charts
- Scaled and normalized metrics for better display
- Full date range coverage

### 4.2 Period Comparison Visualization
- Side-by-side comparison of current and previous periods
- Percentage change calculations
- Appropriate for bar charts or grouped bar charts
- Color-coding opportunities for positive/negative changes

### 4.3 Campaign Performance Visualization
- Top campaign performance metrics
- Campaign-level changes between periods
- Support for various chart types (bar, pie, etc.)
- Truncated campaign names for better display

### 4.4 Summary Metrics Visualization
- Aggregated account-level metrics
- Key performance indicators highlighted
- Formatted for quick dashboard-style displays

## 5. Deployment Considerations

When deploying this enhanced server implementation, consider the following:

1. **Environment Variables**:
   - Set all required Google Ads API credentials
   - Configure cache path and expiration settings
   - Set proper logging levels

2. **Testing**:
   - Run unit tests to ensure functionality
   - Test with real Google Ads accounts (small data sets first)
   - Verify visualizations render correctly in Claude Artifacts

3. **Production Readiness**:
   - Implement proper error logging
   - Consider rate limiting for Google Ads API calls
   - Monitor cache size and performance

4. **Documentation**:
   - Update README with visualization capabilities
   - Document environment variable requirements
   - Provide examples of visualization usage

## 6. Next Steps

With this enhancement completed, consider the following next steps:

1. **Additional Visualization Types**:
   - Add support for geo maps for location-based data
   - Implement heatmaps for campaign performance by day/hour
   - Create funnel visualizations for conversion paths

2. **Interactive Features**:
   - Enable drill-down capabilities in visualizations
   - Add filtering options within visualizations
   - Implement dynamic date range selection

3. **Performance Optimization**:
   - Further optimize caching strategy
   - Implement query result pagination for large datasets
   - Add background refresh for frequently accessed data

This implementation completes the visualization enhancement phase of the SAGE-Plan, providing a robust foundation for Google Ads KPI visualization through Claude Artifacts.
