"""
Time Series Visualization Module

This module provides functions for formatting time series data for visualization.
"""

import logging
from typing import Dict, Any, List, Optional

# Import utility modules
from google_ads_mcp_server.utils.formatting import (
    format_date,
    truncate_string,
    format_number,
    format_percentage,
    micros_to_currency
)
from google_ads_mcp_server.utils.validation import (
    validate_list,
    validate_non_empty_string
)
from google_ads_mcp_server.utils.error_handler import (
    handle_exception,
    ErrorDetails,
    SEVERITY_WARNING,
    CATEGORY_VISUALIZATION
)
from google_ads_mcp_server.utils.logging import get_logger

# Get a logger instance using the utility function
logger = get_logger(__name__)

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
    try:
        # Validate inputs
        validation_errors = []
        validate_list(data, "data", validation_errors, allow_empty=True)
        validate_non_empty_string(date_key, "date_key", validation_errors)
        validate_non_empty_string(title, "title", validation_errors)
        
        if validation_errors:
            error_message = f"Validation errors in time series formatting: {', '.join(validation_errors)}"
            logger.warning(error_message)
            # Return a minimal chart with error message
            return {
                "chart_type": "time_series",
                "title": title,
                "subtitle": "Error: Invalid input data",
                "axes": {},
                "series": [],
                "data": []
            }
        
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
        formatted_data = []
        for item in data:
            formatted_item = {}
            
            # Process each field using appropriate formatters
            for key, value in item.items():
                if key == date_key and value:
                    # Format date using the utility function
                    formatted_item[key] = format_date(value)
                elif key in metrics:
                    # Format metrics according to their type
                    if key == "cost" or "cost_" in key or key == "cpc":
                        # Handle cost values in micros
                        formatted_item[key] = value
                    elif "ctr" in key or "rate" in key or "percentage" in key:
                        # Keep raw values for proper charting, formatting happens in tooltip
                        formatted_item[key] = value
                    elif isinstance(value, (int, float)):
                        # Keep raw values for proper charting, formatting happens in tooltip
                        formatted_item[key] = value
                    else:
                        formatted_item[key] = value
                else:
                    formatted_item[key] = value
            
            formatted_data.append(formatted_item)
        
        # Return the formatted time series data
        visualization_data = {
            "chart_type": "time_series",
            "title": title,
            "subtitle": subtitle,
            "data": formatted_data,
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
            "tooltip": True,
            "tooltip_formatter": {
                "cost": lambda x: micros_to_currency(x),
                "cpc": lambda x: micros_to_currency(x),
                "cost_per_conversion": lambda x: micros_to_currency(x),
                "ctr": lambda x: format_percentage(x),
                "conversion_rate": lambda x: format_percentage(x),
                "impressions": lambda x: format_number(x),
                "clicks": lambda x: format_number(x),
                "conversions": lambda x: format_number(x, 2)
            }
        }
        
        return visualization_data
        
    except Exception as e:
        # Handle exceptions using the error handler utility
        error_details = handle_exception(
            e, 
            context={"data_points": len(data) if data else 0, "metrics": metrics},
            severity=SEVERITY_WARNING,
            category=CATEGORY_VISUALIZATION
        )
        
        logger.error(f"Error formatting time series data: {error_details.message}")
        
        # Return a minimal chart with error message
        return {
            "chart_type": "time_series",
            "title": title,
            "subtitle": f"Error: {error_details.message}",
            "axes": {},
            "series": [],
            "data": []
        }
