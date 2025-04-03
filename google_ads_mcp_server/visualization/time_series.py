"""
Time Series Visualization Module

This module provides functions for formatting time series data for visualization.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

def format_time_series(data: List[Dict[str, Any]], metrics: Optional[List[str]] = None,
                     date_key: str = "date", title: str = "Time Series", 
                     subtitle: str = None) -> Dict[str, Any]:
    """
    Format data as a time series chart for visualization.
    
    Args:
        data: List of dictionaries containing time series data
        metrics: Optional list of metrics to include
        date_key: The key in data items that contains the date
        title: Chart title
        subtitle: Optional chart subtitle
        
    Returns:
        Formatted time series data for visualization
    """
    logger.info(f"Formatting time series visualization with {len(data)} data points")
    
    if not data:
        return {
            "chart_type": "time_series",
            "title": title,
            "subtitle": subtitle or "No data available",
            "axes": {},
            "series": [],
            "data": []
        }
    
    # If metrics not specified, use all numeric keys except the date key
    if not metrics:
        # Get sample item to determine metrics
        sample = data[0]
        metrics = []
        for key, value in sample.items():
            if key != date_key and isinstance(value, (int, float)):
                metrics.append(key)
    
    # Create series specifications
    series = []
    colors = ["#8884d8", "#82ca9d", "#ffc658", "#ff8042", "#a4de6c", "#d0ed57", "#8dd1e1", "#83a6ed"]
    
    metrics_config = {
        "impressions": {"name": "Impressions", "color": "#8884d8", "yAxisId": "impressions"},
        "clicks": {"name": "Clicks", "color": "#82ca9d", "yAxisId": "clicks"},
        "cost": {"name": "Cost", "color": "#ff8042", "yAxisId": "cost"},
        "conversions": {"name": "Conversions", "color": "#8dd1e1", "yAxisId": "conversions"},
        "ctr": {"name": "CTR", "color": "#a4de6c", "yAxisId": "percentage"},
        "cpc": {"name": "CPC", "color": "#d0ed57", "yAxisId": "cost"},
        "conversion_rate": {"name": "Conversion Rate", "color": "#ffc658", "yAxisId": "percentage"},
        "cost_per_conversion": {"name": "Cost per Conversion", "color": "#83a6ed", "yAxisId": "cost"}
    }
    
    for i, metric in enumerate(metrics):
        config = metrics_config.get(metric, {})
        name = config.get("name", metric.replace("_", " ").title())
        color = config.get("color", colors[i % len(colors)])
        y_axis_id = config.get("yAxisId", "default")
        
        series.append({
            "name": name,
            "dataKey": metric,
            "color": color,
            "type": "line",
            "yAxisId": y_axis_id
        })
    
    # Format the data to ensure dates are in consistent format
    for item in data:
        if date_key in item and item[date_key]:
            # Ensure date is in YYYY-MM-DD format
            date_str = str(item[date_key])
            if len(date_str) == 8:  # Format like YYYYMMDD
                item[date_key] = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    
    # Return the formatted time series data
    visualization_data = {
        "chart_type": "time_series",
        "title": title,
        "subtitle": subtitle,
        "data": data,
        "axes": {
            "x": {
                "label": "Date",
                "dataKey": date_key,
                "type": "category"
            },
            "y": {
                "label": "Value",
                "type": "number"
            }
        },
        "series": series,
        "legend": True,
        "grid": True,
        "tooltip": True
    }
    
    return visualization_data
