"""
Visualization Formatters Module

This module provides functions for formatting data for visualization.
"""

import logging
from typing import Dict, Any, List, Optional
import importlib

# Import utility modules
from google_ads_mcp_server.utils.formatting import (
    micros_to_currency,
    format_percentage,
    format_number,
    format_date,
    truncate_string
)
from google_ads_mcp_server.utils.validation import (
    validate_list,
    validate_dict,
    validate_non_empty_string,
    validate_enum
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

# Lazy-loaded module cache to avoid redundant imports
_MODULE_CACHE = {}

def _get_formatter_module(module_name):
    """
    Lazily load a formatter module to avoid redundant imports.
    
    Args:
        module_name: Name of the module to load
        
    Returns:
        The loaded module
    """
    try:
        if module_name not in _MODULE_CACHE:
            _MODULE_CACHE[module_name] = importlib.import_module(f"visualization.{module_name}")
        return _MODULE_CACHE[module_name]
    except ImportError as e:
        logger.error(f"Failed to import visualization module '{module_name}': {str(e)}")
        raise

def format_for_visualization(data: Any, chart_type: str, **kwargs) -> Dict[str, Any]:
    """
    Format data for visualization in Claude Artifacts.
    
    Args:
        data: Raw data to format
        chart_type: Type of chart (time_series, bar, pie, table, kpi_cards)
        **kwargs: Additional chart-specific parameters
        
    Returns:
        Formatted data for visualization
    """
    try:
        # Validate inputs
        validation_errors = []
        validate_non_empty_string(chart_type, "chart_type", validation_errors)
        
        valid_chart_types = [
            "time_series", "bar", "pie", "table", "kpi_cards",
            "ad_group_comparison", "ad_group_time_series", "ad_group_status",
            "keyword_table", "keyword_status", "keyword_performance",
            "search_term_table", "search_term_cloud", "search_term_analysis"
        ]
        
        validate_enum(chart_type, "chart_type", valid_chart_types, validation_errors)
        
        if validation_errors:
            error_message = f"Validation errors in visualization formatting: {', '.join(validation_errors)}"
            logger.warning(error_message)
            # Return a minimal visualization with error
            return {
                "chart_type": "message",
                "title": "Visualization Error",
                "message": error_message
            }
        
        logger.info(f"Formatting visualization data for chart type: {chart_type}")
        
        # Map chart types to modules and functions
        chart_config = {
            "time_series": ("time_series", "format_time_series"),
            "bar": ("comparisons", "format_bar_chart"),
            "pie": ("comparisons", "format_pie_chart"),
            "table": None,  # Handle directly in this module
            "kpi_cards": None,  # Handle directly in this module
            "ad_group_comparison": ("ad_groups", "format_ad_group_comparison"),
            "ad_group_time_series": ("ad_groups", "format_ad_group_performance_time_series"),
            "ad_group_status": ("ad_groups", "format_ad_group_status_distribution"),
            "keyword_table": ("keywords", "format_keyword_comparison_table"),
            "keyword_status": ("keywords", "format_keyword_status_distribution"),
            "keyword_performance": ("keywords", "format_keyword_performance_metrics"),
            "search_term_table": ("search_terms", "format_search_term_table"),
            "search_term_cloud": ("search_terms", "format_search_term_word_cloud"),
            "search_term_analysis": ("search_terms", "format_search_term_analysis")
        }
        
        # Use local functions for basic formatting
        if chart_type == "table":
            return format_table(data, **kwargs)
        elif chart_type == "kpi_cards":
            return format_kpi_cards(data, **kwargs)
        
        # Use the chart configuration to lazily load the appropriate formatter
        formatter_config = chart_config.get(chart_type)
        
        if formatter_config:
            module_name, function_name = formatter_config
            module = _get_formatter_module(module_name)
            formatter_func = getattr(module, function_name)
            return formatter_func(data, **kwargs)
        else:
            logger.warning(f"Unsupported chart type: {chart_type}, falling back to table format")
            return format_table(data, **kwargs)
            
    except Exception as e:
        # Handle exceptions using the error handler utility
        error_details = handle_exception(
            e, 
            context={"chart_type": chart_type},
            severity=SEVERITY_WARNING,
            category=CATEGORY_VISUALIZATION
        )
        
        logger.error(f"Error formatting visualization data: {error_details.message}")
        
        # Return a minimal visualization with error
        return {
            "chart_type": "message",
            "title": "Visualization Error",
            "message": error_details.message
        }

def format_table(data: List[Dict[str, Any]], metrics: Optional[List[str]] = None, 
               title: str = "Data Table", subtitle: str = None) -> Dict[str, Any]:
    """
    Format data as a table for visualization.
    
    Args:
        data: List of dictionaries containing the data
        metrics: Optional list of metrics/columns to include
        title: Table title
        subtitle: Optional table subtitle
        
    Returns:
        Formatted table data for visualization
    """
    try:
        # Validate inputs
        validation_errors = []
        validate_list(data, "data", validation_errors, allow_empty=True)
        validate_non_empty_string(title, "title", validation_errors)
        
        if validation_errors:
            error_message = f"Validation errors in table formatting: {', '.join(validation_errors)}"
            logger.warning(error_message)
            return {
                "chart_type": "table",
                "title": title,
                "subtitle": "Error: Invalid input data",
                "columns": [],
                "data": []
            }
            
        logger.info(f"Formatting table visualization with {len(data)} rows")
        
        if not data:
            return {
                "chart_type": "table",
                "title": title,
                "subtitle": subtitle or "No data available",
                "columns": [],
                "data": []
            }
        
        # If metrics not specified, use all keys from the first data item
        if not metrics:
            metrics = list(data[0].keys())
        
        # Faster column width calculation using pre-computation
        # Define common format types and their default widths
        format_types = {
            "currency": ["cost", "conversion_value", "value", "budget", "cpc", "cpa", "roas"],
            "percent": ["ctr", "rate", "conversion_rate", "percentage"],
            "number": ["impressions", "clicks", "conversions"]
        }
        
        # Pre-compute column specifications in a single pass
        columns = []
        
        for metric in metrics:
            # Determine column width based on metric name (with limit)
            display_name = metric.replace("_", " ").title()
            width = min(max(len(display_name) * 8, 80), 250)  # Min 80px, max 250px
            
            # Determine format type quickly using pre-defined patterns
            format_type = "text"  # Default format
            metric_lower = metric.lower()
            
            # Check format type using fast lookups
            if any(pattern in metric_lower for pattern in format_types["currency"]):
                format_type = "currency"
            elif any(pattern in metric_lower for pattern in format_types["percent"]):
                format_type = "percent"
            elif any(pattern in metric_lower for pattern in format_types["number"]):
                format_type = "number"
            else:
                # Only check the first item in the data if needed
                sample_value = data[0].get(metric) if data else None
                if isinstance(sample_value, (int, float)):
                    format_type = "number"
            
            columns.append({
                "title": display_name,
                "dataKey": metric,
                "width": width,
                "format": format_type
            })
        
        # Format the actual data values based on their column type
        formatted_data = []
        for row in data:
            formatted_row = {}
            for column in columns:
                key = column["dataKey"]
                value = row.get(key)
                
                if value is not None:
                    # Apply appropriate formatting based on column type
                    if column["format"] == "currency" and isinstance(value, (int, float)):
                        # Convert to micros if needed (assuming direct value, not micros)
                        formatted_row[key] = micros_to_currency(value * 1000000)
                    elif column["format"] == "percent" and isinstance(value, (int, float)):
                        formatted_row[key] = format_percentage(value)
                    elif column["format"] == "number" and isinstance(value, (int, float)):
                        formatted_row[key] = format_number(value)
                    elif isinstance(value, str) and len(value) > 50:
                        formatted_row[key] = truncate_string(value, 50)
                    else:
                        formatted_row[key] = value
                else:
                    formatted_row[key] = None
            
            formatted_data.append(formatted_row)
        
        # Return the formatted table data
        visualization_data = {
            "chart_type": "table",
            "title": title,
            "subtitle": subtitle,
            "columns": columns,
            "data": formatted_data,
            "pagination": True,
            "sortable": True,
            "defaultSort": metrics[0],
            "defaultSortDirection": "asc"
        }
        
        return visualization_data
        
    except Exception as e:
        # Handle exceptions using the error handler utility
        error_details = handle_exception(
            e, 
            context={"data_rows": len(data) if data else 0, "metrics": metrics},
            severity=SEVERITY_WARNING,
            category=CATEGORY_VISUALIZATION
        )
        
        logger.error(f"Error formatting table data: {error_details.message}")
        
        return {
            "chart_type": "table",
            "title": title,
            "subtitle": f"Error: {error_details.message}",
            "columns": [],
            "data": []
        }

def format_kpi_cards(data: Dict[str, Any], cards: Optional[List[Dict[str, Any]]] = None,
                   title: str = "Key Metrics", layout: str = "horizontal") -> Dict[str, Any]:
    """
    Format KPI cards for visualization.
    
    Args:
        data: Dictionary containing the data
        cards: Optional list of card specifications
        title: Cards title
        layout: Card layout (horizontal or vertical)
        
    Returns:
        Formatted KPI cards for visualization
    """
    try:
        # Validate inputs
        validation_errors = []
        validate_dict(data, "data", validation_errors, allow_empty=True)
        validate_non_empty_string(title, "title", validation_errors)
        validate_enum(layout, "layout", ["horizontal", "vertical"], validation_errors)
        
        if validation_errors:
            error_message = f"Validation errors in KPI cards formatting: {', '.join(validation_errors)}"
            logger.warning(error_message)
            return {
                "chart_type": "kpi_cards",
                "title": title,
                "subtitle": "Error: Invalid input data",
                "data": []
            }
            
        logger.info("Formatting KPI cards visualization")
        
        # If cards not specified, create them from data
        if not cards:
            cards = []
            metrics_config = {
                "impressions": {"title": "Impressions", "format": "number", "color": "#8884d8"},
                "clicks": {"title": "Clicks", "format": "number", "color": "#82ca9d"},
                "cost": {"title": "Cost", "format": "currency", "color": "#ff8042"},
                "conversions": {"title": "Conversions", "format": "number", "color": "#8dd1e1"},
                "ctr": {"title": "CTR", "format": "percent", "color": "#a4de6c"},
                "cpc": {"title": "CPC", "format": "currency", "color": "#d0ed57"},
                "conversion_rate": {"title": "Conv. Rate", "format": "percent", "color": "#ffc658"},
                "cost_per_conversion": {"title": "Cost per Conv.", "format": "currency", "color": "#ff8042"}
            }
            
            for metric, config in metrics_config.items():
                if metric in data:
                    # Get raw value
                    value = data[metric]
                    
                    # Format the value based on the metric type
                    if config["format"] == "currency" and isinstance(value, (int, float)):
                        # Assuming direct value, not micros
                        formatted_value = micros_to_currency(value * 1000000)
                    elif config["format"] == "percent" and isinstance(value, (int, float)):
                        formatted_value = format_percentage(value)
                    elif config["format"] == "number" and isinstance(value, (int, float)):
                        formatted_value = format_number(value)
                    else:
                        formatted_value = value
                    
                    cards.append({
                        "title": config["title"],
                        "value": formatted_value,
                        "raw_value": value,  # Keep the raw value for sorting/calculations
                        "format": config["format"],
                        "color": config["color"]
                    })
        
        # Return the formatted KPI cards
        visualization_data = {
            "chart_type": "kpi_cards",
            "title": title,
            "data": cards,
            "layout": layout,
            "card_width": 200,
            "card_height": 120
        }
        
        return visualization_data
        
    except Exception as e:
        # Handle exceptions using the error handler utility
        error_details = handle_exception(
            e, 
            context={"metrics_count": len(data) if data else 0},
            severity=SEVERITY_WARNING,
            category=CATEGORY_VISUALIZATION
        )
        
        logger.error(f"Error formatting KPI cards: {error_details.message}")
        
        return {
            "chart_type": "kpi_cards",
            "title": title,
            "subtitle": f"Error: {error_details.message}",
            "data": []
        }
