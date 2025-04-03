"""
Dashboard visualization functions for Google Ads MCP Server.

This module contains functions for generating dashboard visualizations including:
- Account-level dashboards with KPIs, trends, and top performers
- Campaign-level dashboards with detailed performance metrics
"""

from typing import Dict, List, Any, Optional, Union
import json
from datetime import datetime, timedelta


def _format_currency(value_micros: int) -> float:
    """Format a micro-amount to standard currency units."""
    return value_micros / 1000000.0


def _format_percentage(value: float) -> float:
    """Format a ratio as a percentage with 2 decimal places."""
    return round(value * 100, 2)


def _calculate_change(current: float, previous: float) -> Dict[str, Any]:
    """Calculate the change between current and previous values."""
    if previous == 0:
        # Avoid division by zero
        if current == 0:
            change_pct = 0
        else:
            change_pct = 100  # Represents infinity (∞)
    else:
        change_pct = ((current - previous) / previous) * 100
    
    return {
        "absolute": current - previous,
        "percentage": round(change_pct, 2),
        "direction": "up" if change_pct > 0 else "down" if change_pct < 0 else "unchanged"
    }


def create_kpi_cards(metrics: Dict[str, Any], 
                    comparison_metrics: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Create KPI cards with comparison indicators if comparison data is provided.
    
    Args:
        metrics: Dictionary containing current period metrics
        comparison_metrics: Optional dictionary containing comparison period metrics
    
    Returns:
        List of KPI card data structures
    """
    kpi_cards = []
    
    # Define the KPIs to display
    kpi_definitions = [
        {
            "key": "cost_micros",
            "name": "Cost",
            "format": "currency",
            "description": "Total spend for the period"
        },
        {
            "key": "impressions",
            "name": "Impressions",
            "format": "number",
            "description": "Total ad impressions"
        },
        {
            "key": "clicks",
            "name": "Clicks",
            "format": "number",
            "description": "Total clicks on ads"
        },
        {
            "key": "conversions",
            "name": "Conversions",
            "format": "number",
            "description": "Total conversions"
        },
        {
            "key": "ctr",
            "name": "CTR",
            "format": "percentage",
            "description": "Click-through rate"
        },
        {
            "key": "average_cpc",
            "name": "Avg. CPC",
            "format": "currency",
            "description": "Average cost per click"
        },
        {
            "key": "conversion_rate",
            "name": "Conv. Rate",
            "format": "percentage",
            "description": "Conversion rate"
        },
        {
            "key": "cost_per_conversion",
            "name": "Cost/Conv.",
            "format": "currency",
            "description": "Average cost per conversion"
        }
    ]
    
    for kpi in kpi_definitions:
        # Skip if this KPI isn't in the data
        if kpi["key"] not in metrics and kpi["key"] not in ["ctr", "average_cpc", "conversion_rate", "cost_per_conversion"]:
            continue
            
        # Handle derived metrics
        value = None
        if kpi["key"] == "ctr" and "clicks" in metrics and "impressions" in metrics:
            value = metrics["clicks"] / metrics["impressions"] if metrics["impressions"] > 0 else 0
        elif kpi["key"] == "average_cpc" and "cost_micros" in metrics and "clicks" in metrics:
            value = _format_currency(metrics["cost_micros"]) / metrics["clicks"] if metrics["clicks"] > 0 else 0
        elif kpi["key"] == "conversion_rate" and "conversions" in metrics and "clicks" in metrics:
            value = metrics["conversions"] / metrics["clicks"] if metrics["clicks"] > 0 else 0
        elif kpi["key"] == "cost_per_conversion" and "cost_micros" in metrics and "conversions" in metrics:
            value = _format_currency(metrics["cost_micros"]) / metrics["conversions"] if metrics["conversions"] > 0 else 0
        else:
            # Direct metrics
            value = metrics.get(kpi["key"])
            if kpi["format"] == "currency" and value is not None:
                value = _format_currency(value)
        
        if value is None:
            continue
            
        # Format the value for display
        if kpi["format"] == "percentage":
            display_value = f"{_format_percentage(value)}%"
        elif kpi["format"] == "currency":
            display_value = f"${value:.2f}"
        else:
            display_value = f"{value:,}"
            
        kpi_card = {
            "name": kpi["name"],
            "value": value,
            "display_value": display_value,
            "description": kpi["description"]
        }
        
        # Add comparison data if available
        if comparison_metrics:
            comparison_value = None
            if kpi["key"] == "ctr" and "clicks" in comparison_metrics and "impressions" in comparison_metrics:
                comparison_value = comparison_metrics["clicks"] / comparison_metrics["impressions"] if comparison_metrics["impressions"] > 0 else 0
            elif kpi["key"] == "average_cpc" and "cost_micros" in comparison_metrics and "clicks" in comparison_metrics:
                comparison_value = _format_currency(comparison_metrics["cost_micros"]) / comparison_metrics["clicks"] if comparison_metrics["clicks"] > 0 else 0
            elif kpi["key"] == "conversion_rate" and "conversions" in comparison_metrics and "clicks" in comparison_metrics:
                comparison_value = comparison_metrics["conversions"] / comparison_metrics["clicks"] if comparison_metrics["clicks"] > 0 else 0
            elif kpi["key"] == "cost_per_conversion" and "cost_micros" in comparison_metrics and "conversions" in comparison_metrics:
                comparison_value = _format_currency(comparison_metrics["cost_micros"]) / comparison_metrics["conversions"] if comparison_metrics["conversions"] > 0 else 0
            else:
                comparison_value = comparison_metrics.get(kpi["key"])
                if kpi["format"] == "currency" and comparison_value is not None:
                    comparison_value = _format_currency(comparison_value)
            
            if comparison_value is not None:
                change = _calculate_change(value, comparison_value)
                
                if kpi["format"] == "percentage":
                    change_display = f"{change['percentage']:+.2f}pp"  # percentage points
                elif kpi["format"] == "currency":
                    change_display = f"${change['absolute']:+.2f}"
                else:
                    change_display = f"{change['absolute']:+,}"
                
                kpi_card["comparison"] = {
                    "value": comparison_value,
                    "change": change,
                    "change_display": change_display
                }
        
        kpi_cards.append(kpi_card)
            
    return kpi_cards


def create_trend_chart(time_series_data: List[Dict[str, Any]], 
                      metrics: List[str],
                      title: str = "Performance Trends") -> Dict[str, Any]:
    """
    Create a trend line chart showing selected metrics over time.
    
    Args:
        time_series_data: List of data points with date and metrics
        metrics: List of metric names to include in the chart
        title: Chart title
        
    Returns:
        Chart data structure compatible with Claude Artifacts
    """
    # Map of metric names to user-friendly labels and formats
    metric_config = {
        "cost_micros": {"label": "Cost", "format": "currency", "color": "rgba(66, 133, 244, 1)"},
        "impressions": {"label": "Impressions", "format": "number", "color": "rgba(15, 157, 88, 1)"},
        "clicks": {"label": "Clicks", "format": "number", "color": "rgba(244, 180, 0, 1)"},
        "conversions": {"label": "Conversions", "format": "number", "color": "rgba(219, 68, 55, 1)"},
        "ctr": {"label": "CTR", "format": "percentage", "color": "rgba(180, 0, 244, 1)"},
        "average_cpc": {"label": "Avg. CPC", "format": "currency", "color": "rgba(0, 244, 180, 1)"},
        "conversion_rate": {"label": "Conv. Rate", "format": "percentage", "color": "rgba(66, 220, 244, 1)"},
        "cost_per_conversion": {"label": "Cost/Conv.", "format": "currency", "color": "rgba(244, 66, 161, 1)"}
    }
    
    # Extract dates from time series data
    labels = [entry["date"] for entry in time_series_data]
    
    # Create datasets for each requested metric
    datasets = []
    for metric in metrics:
        if metric not in metric_config:
            continue
            
        # Prepare data values based on format
        data = []
        for entry in time_series_data:
            if metric in entry:
                if metric_config[metric]["format"] == "currency":
                    data.append(_format_currency(entry[metric]))
                elif metric_config[metric]["format"] == "percentage":
                    data.append(_format_percentage(entry[metric]))
                else:
                    data.append(entry[metric])
            elif metric == "ctr" and "clicks" in entry and "impressions" in entry:
                value = entry["clicks"] / entry["impressions"] if entry["impressions"] > 0 else 0
                data.append(_format_percentage(value))
            elif metric == "average_cpc" and "cost_micros" in entry and "clicks" in entry:
                value = _format_currency(entry["cost_micros"]) / entry["clicks"] if entry["clicks"] > 0 else 0
                data.append(value)
            elif metric == "conversion_rate" and "conversions" in entry and "clicks" in entry:
                value = entry["conversions"] / entry["clicks"] if entry["clicks"] > 0 else 0
                data.append(_format_percentage(value))
            elif metric == "cost_per_conversion" and "cost_micros" in entry and "conversions" in entry:
                value = _format_currency(entry["cost_micros"]) / entry["conversions"] if entry["conversions"] > 0 else 0
                data.append(value)
            else:
                data.append(None)  # Use None for missing data points
                
        # Create dataset
        datasets.append({
            "label": metric_config[metric]["label"],
            "data": data,
            "borderColor": metric_config[metric]["color"],
            "backgroundColor": metric_config[metric]["color"].replace("1)", "0.1)"),
            "tension": 0.4  # Adds slight curve to lines
        })
    
    # Create chart
    chart = {
        "type": "line",
        "title": title,
        "data": {
            "labels": labels,
            "datasets": datasets
        },
        "options": {
            "scales": {
                "y": {
                    "beginAtZero": True
                }
            }
        }
    }
    
    return chart


def create_top_performers_table(entities: List[Dict[str, Any]], 
                               entity_type: str,
                               metric: str,
                               title: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a table showing top performing entities by a given metric.
    
    Args:
        entities: List of entity data
        entity_type: Type of entity (campaigns, ad_groups, keywords)
        metric: Metric to sort by
        title: Optional table title
        
    Returns:
        Table data structure compatible with Claude Artifacts
    """
    # Define headers based on entity type
    if entity_type == "campaigns":
        headers = ["Campaign", "Budget", "Status", metric.replace("_", " ").title()]
    elif entity_type == "ad_groups":
        headers = ["Ad Group", "Campaign", "Status", metric.replace("_", " ").title()]
    elif entity_type == "keywords":
        headers = ["Keyword", "Match Type", "Ad Group", metric.replace("_", " ").title()]
    else:
        headers = ["Name", "Status", metric.replace("_", " ").title()]
    
    # Sort entities by the specified metric (descending)
    sorted_entities = sorted(entities, key=lambda x: x.get(metric, 0), reverse=True)
    
    # Prepare table rows
    rows = []
    for entity in sorted_entities[:10]:  # Limit to top 10
        if entity_type == "campaigns":
            # Format currency values if needed
            metric_value = entity.get(metric, 0)
            if metric.endswith("_micros"):
                metric_value = _format_currency(metric_value)
            
            rows.append([
                entity.get("name", "Unknown"),
                f"${_format_currency(entity.get('budget_amount_micros', 0)):.2f}",
                entity.get("status", "Unknown"),
                f"${metric_value:.2f}" if metric.endswith("_micros") else f"{metric_value:,}"
            ])
        elif entity_type == "ad_groups":
            metric_value = entity.get(metric, 0)
            if metric.endswith("_micros"):
                metric_value = _format_currency(metric_value)
                
            rows.append([
                entity.get("name", "Unknown"),
                entity.get("campaign_name", "Unknown"),
                entity.get("status", "Unknown"),
                f"${metric_value:.2f}" if metric.endswith("_micros") else f"{metric_value:,}"
            ])
        elif entity_type == "keywords":
            metric_value = entity.get(metric, 0)
            if metric.endswith("_micros"):
                metric_value = _format_currency(metric_value)
                
            rows.append([
                entity.get("text", "Unknown"),
                entity.get("match_type", "Unknown"),
                entity.get("ad_group_name", "Unknown"),
                f"${metric_value:.2f}" if metric.endswith("_micros") else f"{metric_value:,}"
            ])
    
    # Create table
    if title is None:
        title = f"Top {entity_type.title()} by {metric.replace('_', ' ').title()}"
        
    table = {
        "title": title,
        "headers": headers,
        "rows": rows
    }
    
    return table


def create_donut_chart(data: List[Dict[str, Any]], 
                      category_key: str,
                      value_key: str,
                      title: str) -> Dict[str, Any]:
    """
    Create a donut chart showing distribution of a value across categories.
    
    Args:
        data: List of data objects containing categories and values
        category_key: Key for category names
        value_key: Key for values
        title: Chart title
        
    Returns:
        Chart data structure compatible with Claude Artifacts
    """
    categories = []
    values = []
    
    # Extract category names and values
    for item in data:
        categories.append(item.get(category_key, "Unknown"))
        
        value = item.get(value_key, 0)
        if value_key.endswith("_micros"):
            value = _format_currency(value)
            
        values.append(value)
    
    # List of colors for the chart segments
    colors = [
        "rgba(66, 133, 244, 0.8)",
        "rgba(15, 157, 88, 0.8)",
        "rgba(244, 180, 0, 0.8)",
        "rgba(219, 68, 55, 0.8)",
        "rgba(180, 0, 244, 0.8)",
        "rgba(0, 244, 180, 0.8)",
        "rgba(66, 220, 244, 0.8)",
        "rgba(244, 66, 161, 0.8)",
        "rgba(183, 183, 183, 0.8)",
        "rgba(124, 124, 124, 0.8)"
    ]
    
    # Create chart
    chart = {
        "type": "doughnut",
        "title": title,
        "data": {
            "labels": categories,
            "datasets": [{
                "data": values,
                "backgroundColor": colors[:len(values)],
                "hoverOffset": 4
            }]
        },
        "options": {
            "plugins": {
                "legend": {
                    "position": "right"
                }
            }
        }
    }
    
    return chart


def create_account_dashboard_visualization(account_data: Dict[str, Any],
                                          comparison_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a comprehensive account dashboard visualization.
    
    Args:
        account_data: Account performance data including metrics, time series, and entities
        comparison_data: Optional comparison period data
        
    Returns:
        Complete dashboard visualization data structure for Claude Artifacts
    """
    # Initialize dashboard components
    charts = []
    tables = []
    
    # 1. Create KPI Cards
    kpi_cards = create_kpi_cards(
        account_data.get("metrics", {}),
        comparison_data.get("metrics", {}) if comparison_data else None
    )
    
    # Add KPI cards as a specialized table
    kpi_table = {
        "title": "Account Performance",
        "type": "kpi_cards",
        "cards": kpi_cards
    }
    tables.append(kpi_table)
    
    # 2. Create Trend Charts
    if "time_series" in account_data:
        # Cost trend
        cost_trend = create_trend_chart(
            account_data["time_series"],
            ["cost_micros"],
            "Cost Trend"
        )
        charts.append(cost_trend)
        
        # Clicks, Impressions trend
        engagement_trend = create_trend_chart(
            account_data["time_series"],
            ["clicks", "impressions"],
            "Engagement Trend"
        )
        charts.append(engagement_trend)
        
        # Conversions trend
        conversion_trend = create_trend_chart(
            account_data["time_series"],
            ["conversions", "conversion_rate"],
            "Conversion Trend"
        )
        charts.append(conversion_trend)
    
    # 3. Top Performers Tables
    if "campaigns" in account_data:
        # Table for top campaigns by cost
        top_campaigns_cost = create_top_performers_table(
            account_data["campaigns"],
            "campaigns",
            "cost_micros",
            "Top Campaigns by Spend"
        )
        tables.append(top_campaigns_cost)
        
        # Table for top campaigns by conversions
        if any("conversions" in campaign for campaign in account_data["campaigns"]):
            top_campaigns_conv = create_top_performers_table(
                account_data["campaigns"],
                "campaigns",
                "conversions",
                "Top Campaigns by Conversions"
            )
            tables.append(top_campaigns_conv)
            
        # Donut chart for cost distribution by campaign
        campaign_cost_distribution = create_donut_chart(
            account_data["campaigns"][:8],  # Limit to top 8 campaigns
            "name",
            "cost_micros",
            "Cost Distribution by Campaign"
        )
        charts.append(campaign_cost_distribution)
    
    if "ad_groups" in account_data:
        # Table for top ad groups by cost
        top_ad_groups = create_top_performers_table(
            account_data["ad_groups"],
            "ad_groups",
            "cost_micros",
            "Top Ad Groups by Spend"
        )
        tables.append(top_ad_groups)
    
    # Compile dashboard
    dashboard = {
        "charts": charts,
        "tables": tables
    }
    
    return dashboard


def create_campaign_dashboard_visualization(campaign_data: Dict[str, Any],
                                           comparison_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a comprehensive single campaign dashboard visualization.
    
    Args:
        campaign_data: Campaign performance data including metrics, time series, and child entities
        comparison_data: Optional comparison period data
        
    Returns:
        Complete dashboard visualization data structure for Claude Artifacts
    """
    # Initialize dashboard components
    charts = []
    tables = []
    
    # Extract campaign metadata
    campaign_info = {
        "title": f"Campaign: {campaign_data.get('name', 'Unknown')}",
        "headers": ["Property", "Value"],
        "rows": [
            ["ID", str(campaign_data.get("id", "Unknown"))],
            ["Status", campaign_data.get("status", "Unknown")],
            ["Budget", f"${_format_currency(campaign_data.get('budget_amount_micros', 0)):.2f}"],
            ["Budget Utilization", f"{_format_percentage(campaign_data.get('budget_utilization', 0))}%"],
            ["Type", campaign_data.get("type", "Unknown")],
            ["Start Date", campaign_data.get("start_date", "Unknown")],
            ["End Date", campaign_data.get("end_date", "Not set") if campaign_data.get("end_date") else "Not set"]
        ]
    }
    tables.append(campaign_info)
    
    # 1. Create KPI Cards
    kpi_cards = create_kpi_cards(
        campaign_data.get("metrics", {}),
        comparison_data.get("metrics", {}) if comparison_data else None
    )
    
    # Add KPI cards as a specialized table
    kpi_table = {
        "title": "Campaign Performance",
        "type": "kpi_cards",
        "cards": kpi_cards
    }
    tables.append(kpi_table)
    
    # 2. Create Trend Charts
    if "time_series" in campaign_data:
        # Cost & Conversions trend
        performance_trend = create_trend_chart(
            campaign_data["time_series"],
            ["cost_micros", "conversions"],
            "Performance Trend"
        )
        charts.append(performance_trend)
        
        # CTR & Conv Rate trend
        rate_trend = create_trend_chart(
            campaign_data["time_series"],
            ["ctr", "conversion_rate"],
            "Rate Metrics Trend"
        )
        charts.append(rate_trend)
    
    # 3. Ad Group breakdown
    if "ad_groups" in campaign_data and campaign_data["ad_groups"]:
        # Table of ad groups
        ad_groups_table = create_top_performers_table(
            campaign_data["ad_groups"],
            "ad_groups",
            "cost_micros",
            "Ad Groups"
        )
        tables.append(ad_groups_table)
        
        # Donut chart for cost distribution by ad group
        ad_group_distribution = create_donut_chart(
            campaign_data["ad_groups"],
            "name",
            "cost_micros",
            "Cost Distribution by Ad Group"
        )
        charts.append(ad_group_distribution)
    
    # 4. Device breakdown
    if "device_performance" in campaign_data and campaign_data["device_performance"]:
        # Donut chart for cost by device
        device_distribution = create_donut_chart(
            campaign_data["device_performance"],
            "device",
            "cost_micros",
            "Cost by Device"
        )
        charts.append(device_distribution)
        
        # Table with device performance
        device_table = {
            "title": "Performance by Device",
            "headers": ["Device", "Cost", "Clicks", "Impressions", "CTR", "Conversions", "Conv. Rate"],
            "rows": []
        }
        
        for device in campaign_data["device_performance"]:
            ctr = device.get("clicks", 0) / device.get("impressions", 1) * 100
            conv_rate = device.get("conversions", 0) / device.get("clicks", 1) * 100
            
            device_table["rows"].append([
                device.get("device", "Unknown"),
                f"${_format_currency(device.get('cost_micros', 0)):.2f}",
                f"{device.get('clicks', 0):,}",
                f"{device.get('impressions', 0):,}",
                f"{ctr:.2f}%",
                f"{device.get('conversions', 0):,}",
                f"{conv_rate:.2f}%"
            ])
            
        tables.append(device_table)
    
    # 5. Top keywords if available
    if "keywords" in campaign_data and campaign_data["keywords"]:
        keywords_table = create_top_performers_table(
            campaign_data["keywords"],
            "keywords",
            "cost_micros",
            "Top Keywords"
        )
        tables.append(keywords_table)
    
    # Compile dashboard
    dashboard = {
        "charts": charts,
        "tables": tables
    }
    
    return dashboard 