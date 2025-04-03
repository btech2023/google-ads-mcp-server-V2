"""
Visualization Formatters Module

This module provides functions for formatting data for visualization.
"""

import logging
from typing import Dict, Any, List, Optional
import importlib

logger = logging.getLogger(__name__)

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
    if module_name not in _MODULE_CACHE:
        _MODULE_CACHE[module_name] = importlib.import_module(f"visualization.{module_name}")
    return _MODULE_CACHE[module_name]

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
    
    # Return the formatted table data
    visualization_data = {
        "chart_type": "table",
        "title": title,
        "subtitle": subtitle,
        "columns": columns,
        "data": data,
        "pagination": True,
        "sortable": True,
        "defaultSort": metrics[0],
        "defaultSortDirection": "asc"
    }
    
    return visualization_data

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
                cards.append({
                    "title": config["title"],
                    "value": data[metric],
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
