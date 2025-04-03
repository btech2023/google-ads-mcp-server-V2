"""
Campaign Charts Visualization Module

This module provides functions for formatting campaign-specific chart data for visualization.
"""

import logging
from typing import Dict, Any, List, Optional
from visualization.comparisons import format_bar_chart, format_pie_chart
from visualization.time_series import format_time_series

logger = logging.getLogger(__name__)

def format_campaign_performance_chart(data: List[Dict[str, Any]], 
                                    metrics: Optional[List[str]] = None,
                                    chart_type: str = "bar",
                                    title: str = "Campaign Performance") -> Dict[str, Any]:
    """
    Format campaign performance data for visualization.
    
    Args:
        data: List of campaign data dictionaries
        metrics: Optional list of metrics to include
        chart_type: Type of chart to create (bar, pie)
        title: Chart title
        
    Returns:
        Formatted chart data for visualization
    """
    logger.info(f"Formatting campaign performance chart of type '{chart_type}' with {len(data)} campaigns")
    
    if not data:
        return {
            "chart_type": chart_type,
            "title": title,
            "subtitle": "No campaign data available",
            "data": []
        }
    
    # Set default metrics if not provided
    if not metrics:
        # For pie charts, we need a single metric
        if chart_type == "pie":
            metrics = ["cost"]
        else:
            metrics = ["clicks", "impressions", "cost"]
    
    # Create appropriate chart type
    if chart_type == "bar":
        return format_bar_chart(
            data=data,
            metrics=metrics,
            category_key="name",
            title=title,
            subtitle=f"Comparing {', '.join([m.replace('_', ' ').title() for m in metrics])} across campaigns"
        )
    elif chart_type == "pie":
        return format_pie_chart(
            data=data,
            metric=metrics[0] if metrics else "cost",
            category_key="name",
            title=title,
            subtitle=f"Campaign distribution by {metrics[0].replace('_', ' ').title() if metrics else 'Cost'}"
        )
    else:
        logger.warning(f"Unsupported chart type '{chart_type}' for campaign performance, falling back to bar chart")
        return format_bar_chart(
            data=data,
            metrics=metrics,
            category_key="name",
            title=title,
            subtitle=f"Comparing {', '.join([m.replace('_', ' ').title() for m in metrics])} across campaigns"
        )

def format_campaign_trend_chart(data: List[Dict[str, Any]], 
                             metrics: Optional[List[str]] = None,
                             date_key: str = "date",
                             title: str = "Campaign Performance Trend") -> Dict[str, Any]:
    """
    Format campaign trend data for visualization.
    
    Args:
        data: List of time-series campaign data dictionaries
        metrics: Optional list of metrics to include
        date_key: The key that contains date information
        title: Chart title
        
    Returns:
        Formatted time series chart data for visualization
    """
    logger.info(f"Formatting campaign trend chart with {len(data)} data points")
    
    if not data:
        return {
            "chart_type": "time_series",
            "title": title,
            "subtitle": "No trend data available",
            "data": []
        }
    
    # Set default metrics if not provided
    if not metrics:
        metrics = ["clicks", "impressions", "cost"]
    
    return format_time_series(
        data=data,
        metrics=metrics,
        date_key=date_key,
        title=title,
        subtitle=f"Daily performance from {data[0][date_key]} to {data[-1][date_key]}"
    )

def format_campaign_comparison_table(data: List[Dict[str, Any]], 
                                  metrics: Optional[List[str]] = None,
                                  title: str = "Campaign Comparison") -> Dict[str, Any]:
    """
    Format campaign comparison data as a table for visualization.
    
    Args:
        data: List of campaign data dictionaries
        metrics: Optional list of metrics to include
        title: Table title
        
    Returns:
        Formatted table data for visualization
    """
    logger.info(f"Formatting campaign comparison table with {len(data)} campaigns")
    
    if not data:
        return {
            "chart_type": "table",
            "title": title,
            "subtitle": "No campaign data available",
            "data": []
        }
    
    # Set default columns to display
    if not metrics:
        metrics = ["id", "name", "status", "impressions", "clicks", "cost", "ctr", "cpc", "conversions"]
    
    # Format as table
    from visualization.formatters import format_table
    return format_table(
        data=data,
        metrics=metrics,
        title=title,
        subtitle="Campaign performance comparison"
    )
