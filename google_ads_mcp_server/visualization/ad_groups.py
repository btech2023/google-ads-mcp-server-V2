"""
Ad Group Visualization Module

This module provides functions for formatting ad group data for visualization.
"""

import logging
from typing import Dict, Any, List, Optional

from visualization.comparisons import format_bar_chart
from visualization.time_series import format_time_series

logger = logging.getLogger(__name__)

def format_ad_group_comparison(ad_groups: List[Dict[str, Any]], 
                             metrics: Optional[List[str]] = None,
                             title: str = "Ad Group Performance Comparison") -> Dict[str, Any]:
    """
    Format ad group data for bar chart comparison visualization.
    
    Args:
        ad_groups: List of ad group data dictionaries
        metrics: Optional list of metrics to include (defaults to impressions, clicks, cost)
        title: Chart title
        
    Returns:
        Formatted bar chart data for visualization
    """
    logger.info(f"Formatting ad group comparison visualization with {len(ad_groups)} ad groups")
    
    if not metrics:
        metrics = ["impressions", "clicks", "cost"]
    
    # Prepare data for visualization
    # Limit to top 10 ad groups by cost for better readability
    ad_groups_sorted = sorted(ad_groups, key=lambda x: x.get("cost", 0), reverse=True)[:10]
    
    # Format ad group names to include campaign info
    for ad_group in ad_groups_sorted:
        # Create a more descriptive name
        campaign_name = ad_group.get("campaign_name", "")
        if campaign_name:
            campaign_name = campaign_name[:15] + "..." if len(campaign_name) > 15 else campaign_name
            ad_group["display_name"] = f"{ad_group['name']} ({campaign_name})"
        else:
            ad_group["display_name"] = ad_group["name"]
    
    # Use custom formatting for ad groups
    visualization_data = format_bar_chart(
        data=ad_groups_sorted,
        metrics=metrics,
        category_key="display_name",
        title=title,
        subtitle=f"Top {len(ad_groups_sorted)} Ad Groups by Cost"
    )
    
    return visualization_data

def format_ad_group_performance_time_series(daily_stats: List[Dict[str, Any]],
                                         metrics: Optional[List[str]] = None,
                                         title: str = "Ad Group Performance Over Time") -> Dict[str, Any]:
    """
    Format ad group performance data for time series visualization.
    
    Args:
        daily_stats: List of daily performance data dictionaries
        metrics: Optional list of metrics to include
        title: Chart title
        
    Returns:
        Formatted time series data for visualization
    """
    logger.info(f"Formatting ad group time series visualization with {len(daily_stats)} data points")
    
    if not metrics:
        metrics = ["impressions", "clicks", "cost", "conversions"]
    
    # Use the time series formatter
    visualization_data = format_time_series(
        data=daily_stats,
        metrics=metrics,
        date_key="date",
        title=title
    )
    
    return visualization_data

def format_ad_group_status_distribution(ad_groups: List[Dict[str, Any]],
                                     title: str = "Ad Group Status Distribution") -> Dict[str, Any]:
    """
    Format ad group status data for pie chart visualization.
    
    Args:
        ad_groups: List of ad group data dictionaries
        title: Chart title
        
    Returns:
        Formatted pie chart data for visualization
    """
    logger.info(f"Formatting ad group status distribution visualization with {len(ad_groups)} ad groups")
    
    # Count ad groups by status
    status_counts = {}
    for ad_group in ad_groups:
        status = ad_group.get("status", "UNKNOWN")
        if status in status_counts:
            status_counts[status] += 1
        else:
            status_counts[status] = 1
    
    # Convert to list format for visualization
    status_data = [{"name": status, "count": count} for status, count in status_counts.items()]
    
    # Colors for different statuses
    status_colors = {
        "ENABLED": "#4CAF50",  # Green
        "PAUSED": "#FFC107",   # Amber
        "REMOVED": "#F44336",  # Red
        "UNKNOWN": "#9E9E9E"   # Grey
    }
    
    # Add colors to the data
    for item in status_data:
        item["color"] = status_colors.get(item["name"], "#9E9E9E")
    
    # Create visualization data
    visualization_data = {
        "chart_type": "pie",
        "title": title,
        "dataKey": "count",
        "nameKey": "name",
        "colorKey": "color",
        "data": status_data,
        "legend": True,
        "tooltip": True
    }
    
    return visualization_data 