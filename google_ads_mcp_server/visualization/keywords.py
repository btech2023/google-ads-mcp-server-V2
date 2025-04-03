"""
Keyword Visualization Module

This module provides formatting functions for visualizing keyword data.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def format_keyword_comparison_table(keywords_data: List[Dict[str, Any]], 
                                   title: str = "Keyword Performance") -> Dict[str, Any]:
    """
    Format keyword data for table visualization.
    
    Args:
        keywords_data: List of keyword dictionaries from KeywordService.get_keywords
        title: Title for the visualization
        
    Returns:
        Dictionary formatted for Claude Artifacts table visualization
    """
    if not keywords_data:
        return {
            "chart_type": "table",
            "title": title,
            "columns": [],
            "data": []
        }
    
    logger.info(f"Formatting {len(keywords_data)} keywords for table visualization")
    
    # Define columns for the table visualization
    columns = [
        {"key": "id", "name": "ID", "type": "string"},
        {"key": "text", "name": "Keyword", "type": "string"},
        {"key": "match_type", "name": "Match Type", "type": "string"},
        {"key": "status", "name": "Status", "type": "string"},
        {"key": "ad_group_name", "name": "Ad Group", "type": "string"},
        {"key": "campaign_name", "name": "Campaign", "type": "string"},
        {"key": "impressions", "name": "Impressions", "type": "number", "format": "comma"},
        {"key": "clicks", "name": "Clicks", "type": "number", "format": "comma"},
        {"key": "cost", "name": "Cost", "type": "number", "format": "currency"},
        {"key": "ctr", "name": "CTR", "type": "number", "format": "percent"},
        {"key": "conversions", "name": "Conversions", "type": "number", "format": "decimal"},
        {"key": "conversion_value", "name": "Conv. Value", "type": "number", "format": "currency"},
        {"key": "cost_per_conversion", "name": "Cost/Conv.", "type": "number", "format": "currency"},
        {"key": "roas", "name": "ROAS", "type": "number", "format": "decimal"}
    ]
    
    # Format the data for visualization
    formatted_data = []
    for keyword in keywords_data:
        formatted_keyword = {
            "id": str(keyword.get("id", "")),
            "text": keyword.get("text", ""),
            "match_type": keyword.get("match_type", ""),
            "status": keyword.get("status", ""),
            "ad_group_name": keyword.get("ad_group_name", ""),
            "campaign_name": keyword.get("campaign_name", ""),
            "impressions": keyword.get("impressions", 0),
            "clicks": keyword.get("clicks", 0),
            "cost": keyword.get("cost", 0),
            "ctr": keyword.get("ctr", 0),
            "conversions": keyword.get("conversions", 0),
            "conversion_value": keyword.get("conversion_value", 0),
            "cost_per_conversion": keyword.get("cost_per_conversion", 0),
            "roas": keyword.get("roas", 0)
        }
        formatted_data.append(formatted_keyword)
    
    # Sort data by cost (descending) by default
    formatted_data = sorted(formatted_data, key=lambda x: x.get("cost", 0), reverse=True)
    
    return {
        "chart_type": "table",
        "title": title,
        "columns": columns,
        "data": formatted_data
    }

def format_keyword_status_distribution(keywords_data: List[Dict[str, Any]], 
                                     title: str = "Keyword Status Distribution") -> Dict[str, Any]:
    """
    Format keyword data for status distribution pie chart.
    
    Args:
        keywords_data: List of keyword dictionaries from KeywordService.get_keywords
        title: Title for the visualization
        
    Returns:
        Dictionary formatted for Claude Artifacts pie chart visualization
    """
    if not keywords_data:
        return {
            "chart_type": "pie",
            "title": title,
            "labels": [],
            "values": []
        }
    
    logger.info(f"Formatting {len(keywords_data)} keywords for status distribution visualization")
    
    # Count keywords by status
    status_counts = {}
    for keyword in keywords_data:
        status = keyword.get("status", "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Format the data for visualization
    labels = list(status_counts.keys())
    values = list(status_counts.values())
    
    return {
        "chart_type": "pie",
        "title": title,
        "labels": labels,
        "values": values,
        "colors": ["#4285F4", "#EA4335", "#FBBC05", "#34A853", "#7F7F7F"]  # Google colors + gray
    }

def format_keyword_performance_metrics(keywords_data: List[Dict[str, Any]], 
                                     metric: str = "clicks",
                                     title: str = None,
                                     limit: int = 10) -> Dict[str, Any]:
    """
    Format keyword data for horizontal bar chart showing top keywords by a specific metric.
    
    Args:
        keywords_data: List of keyword dictionaries from KeywordService.get_keywords
        metric: Metric to sort and display (clicks, cost, conversions, etc.)
        title: Title for the visualization (defaults to "Top Keywords by [Metric]")
        limit: Maximum number of keywords to include
        
    Returns:
        Dictionary formatted for Claude Artifacts bar chart visualization
    """
    if not keywords_data:
        return {
            "chart_type": "bar",
            "title": title or f"Top Keywords by {metric.capitalize()}",
            "axis_x": {"name": metric.capitalize()},
            "axis_y": {"name": "Keyword"},
            "labels": [],
            "values": []
        }
    
    # Set default title if not provided
    if not title:
        title = f"Top Keywords by {metric.capitalize()}"
    
    logger.info(f"Formatting top {limit} keywords by {metric} for bar chart visualization")
    
    # Sort keywords by the specified metric
    sorted_keywords = sorted(keywords_data, key=lambda x: x.get(metric, 0), reverse=True)[:limit]
    
    # Format the data for visualization
    labels = [keyword.get("text", "Unknown") for keyword in sorted_keywords]
    values = [keyword.get(metric, 0) for keyword in sorted_keywords]
    
    # Format the chart configuration
    result = {
        "chart_type": "bar",
        "orientation": "horizontal",
        "title": title,
        "axis_x": {"name": metric.capitalize()},
        "axis_y": {"name": "Keyword"},
        "labels": labels,
        "values": values
    }
    
    # Add appropriate formatting based on metric type
    if metric == "cost":
        result["format"] = "currency"
    elif metric == "ctr" or metric.endswith("_rate"):
        result["format"] = "percent"
    elif metric in ["clicks", "impressions"]:
        result["format"] = "comma"
    
    return result 