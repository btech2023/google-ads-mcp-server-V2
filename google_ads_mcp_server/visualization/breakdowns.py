"""
Breakdown Visualization Module

This module provides functions for creating visualizations showing performance breakdowns by different 
dimensions (e.g., device, network, geo, time).
"""

import logging
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def _format_currency_micros(value_micros: int) -> float:
    """Format a micro-amount to standard currency units."""
    return value_micros / 1000000.0 if value_micros else 0.0

def _format_percentage(value: float) -> float:
    """Format a ratio as a percentage with 2 decimal places."""
    return round(value * 100, 2) if value is not None else 0.0

def create_stacked_bar_chart(data: List[Dict[str, Any]], 
                           dimension_key: str,
                           metrics: List[str],
                           title: str = "Performance Breakdown") -> Dict[str, Any]:
    """
    Create a stacked bar chart showing metric contribution by segment.
    
    Args:
        data: List of segment data points
        dimension_key: The key for the dimension being broken down (e.g., 'device', 'network')
        metrics: List of metrics to include (e.g., 'cost_micros', 'clicks')
        title: Chart title
        
    Returns:
        Chart data structure compatible with Claude Artifacts
    """
    logger.info(f"Creating stacked bar chart for dimension {dimension_key}")
    
    if not data or not metrics:
        return {
            "type": "bar",
            "title": title,
            "data": {
                "labels": [],
                "datasets": []
            }
        }
    
    # Extract dimension values (labels for x-axis)
    dimension_values = [item.get(dimension_key, "Unknown") for item in data]
    
    # Configure metrics with appropriate display formatting
    metric_config = {
        "cost_micros": {"label": "Cost", "format": "currency", "color": "rgba(66, 133, 244, 0.8)"},
        "impressions": {"label": "Impressions", "format": "number", "color": "rgba(15, 157, 88, 0.8)"},
        "clicks": {"label": "Clicks", "format": "number", "color": "rgba(244, 180, 0, 0.8)"},
        "conversions": {"label": "Conversions", "format": "number", "color": "rgba(219, 68, 55, 0.8)"},
        "ctr": {"label": "CTR", "format": "percentage", "color": "rgba(180, 0, 244, 0.8)"},
        "average_cpc": {"label": "Avg. CPC", "format": "currency", "color": "rgba(0, 244, 180, 0.8)"},
        "conversion_rate": {"label": "Conv. Rate", "format": "percentage", "color": "rgba(66, 220, 244, 0.8)"},
        "cost_per_conversion": {"label": "Cost/Conv.", "format": "currency", "color": "rgba(244, 66, 161, 0.8)"}
    }
    
    # Create datasets for each metric
    datasets = []
    for metric in metrics:
        # Get display info for the metric
        if metric in metric_config:
            display_name = metric_config[metric]["label"]
            format_type = metric_config[metric]["format"]
            color = metric_config[metric]["color"]
        else:
            display_name = metric.replace("_", " ").title()
            format_type = "number"
            color = "rgba(128, 128, 128, 0.8)"
        
        # Extract and format values for this metric
        values = []
        for item in data:
            value = item.get(metric, 0)
            
            # Apply appropriate formatting
            if format_type == "currency" and metric.endswith("_micros"):
                value = _format_currency_micros(value)
            elif format_type == "percentage":
                value = _format_percentage(value)
                
            values.append(value)
        
        datasets.append({
            "label": display_name,
            "data": values,
            "backgroundColor": color,
            "stack": "Stack 0"  # Group all metrics into a single stack
        })
    
    # Create the final chart structure
    chart = {
        "type": "bar",
        "title": title,
        "data": {
            "labels": dimension_values,
            "datasets": datasets
        },
        "options": {
            "scales": {
                "x": {
                    "stacked": True,
                    "title": {
                        "display": True,
                        "text": dimension_key.replace("_", " ").title()
                    }
                },
                "y": {
                    "stacked": True,
                    "beginAtZero": True,
                    "title": {
                        "display": True,
                        "text": "Value"
                    }
                }
            },
            "plugins": {
                "legend": {
                    "position": "top"
                },
                "tooltip": {
                    "mode": "index",
                    "intersect": False
                }
            }
        }
    }
    
    return chart

def create_breakdown_table(data: List[Dict[str, Any]],
                         dimension_key: str,
                         metrics: List[str],
                         title: str = "Performance Breakdown Table") -> Dict[str, Any]:
    """
    Create a detailed table showing performance breakdown by dimension.
    
    Args:
        data: List of segment data points
        dimension_key: The key for the dimension being broken down
        metrics: List of metrics to include
        title: Table title
        
    Returns:
        Table data structure compatible with Claude Artifacts
    """
    logger.info(f"Creating breakdown table for dimension {dimension_key}")
    
    if not data or not metrics:
        return {
            "title": title,
            "headers": ["No data available"],
            "rows": []
        }
    
    # Configure metrics with appropriate display formatting
    metric_config = {
        "cost_micros": {"label": "Cost", "format": "currency", "tooltip": "Total spend"},
        "impressions": {"label": "Impressions", "format": "number", "tooltip": "Ad impressions"},
        "clicks": {"label": "Clicks", "format": "number", "tooltip": "Total clicks"},
        "conversions": {"label": "Conversions", "format": "number", "tooltip": "Total conversions"},
        "ctr": {"label": "CTR", "format": "percentage", "tooltip": "Click-through rate"},
        "average_cpc": {"label": "Avg. CPC", "format": "currency", "tooltip": "Average cost per click"},
        "conversion_rate": {"label": "Conv. Rate", "format": "percentage", "tooltip": "Conversion rate"},
        "cost_per_conversion": {"label": "Cost/Conv.", "format": "currency", "tooltip": "Cost per conversion"}
    }
    
    # Build headers
    dimension_label = dimension_key.replace("_", " ").title()
    headers = [dimension_label]
    
    for metric in metrics:
        if metric in metric_config:
            headers.append(metric_config[metric]["label"])
        else:
            headers.append(metric.replace("_", " ").title())
    
    # Calculate percentage/share of total for relevant metrics
    total_values = {}
    for metric in metrics:
        if metric not in ["ctr", "average_cpc", "conversion_rate", "cost_per_conversion"]:
            total_values[metric] = sum(item.get(metric, 0) for item in data)
    
    # Generate rows
    rows = []
    for item in data:
        row = [item.get(dimension_key, "Unknown")]
        
        for metric in metrics:
            value = item.get(metric, 0)
            
            # Format based on metric type
            if metric in metric_config:
                format_type = metric_config[metric]["format"]
            else:
                format_type = "number"
            
            # Apply formatting
            if format_type == "currency" and metric.endswith("_micros"):
                value_formatted = _format_currency_micros(value)
                display_value = f"${value_formatted:.2f}"
                
                # Add percentage if applicable
                if metric in total_values and total_values[metric] > 0:
                    share = (value / total_values[metric]) * 100
                    display_value += f" ({share:.1f}%)"
            elif format_type == "percentage":
                value_formatted = _format_percentage(value)
                display_value = f"{value_formatted:.2f}%"
            else:
                display_value = f"{value:,}"
                
                # Add percentage if applicable
                if metric in total_values and total_values[metric] > 0:
                    share = (value / total_values[metric]) * 100
                    display_value += f" ({share:.1f}%)"
            
            row.append(display_value)
        
        rows.append(row)
    
    # Sort rows by the first non-dimension metric (typically cost or impressions)
    if len(metrics) > 0 and len(rows) > 0:
        # Try to get a value-based metric for sorting (prefer cost or impressions)
        sort_metric = "cost_micros"
        if sort_metric not in metrics:
            sort_metric = "impressions"
        if sort_metric not in metrics:
            sort_metric = metrics[0]  # Fallback to first metric
        
        # Get the index of the sort metric in the row
        sort_index = metrics.index(sort_metric) + 1  # +1 for dimension column
        
        # Extract raw values for sorting
        def extract_sort_value(row):
            # Extract numeric value, ignoring percentage in parentheses
            raw_val = row[sort_index].split(" ")[0]
            if raw_val.startswith("$"):
                raw_val = raw_val[1:]
            try:
                return float(raw_val.replace(",", ""))
            except (ValueError, TypeError):
                return 0
        
        # Sort rows by extracted values (descending)
        rows.sort(key=extract_sort_value, reverse=True)
    
    # Create the final table structure
    table = {
        "title": title,
        "headers": headers,
        "rows": rows
    }
    
    return table

def create_treemap_chart(data: List[Dict[str, Any]],
                       dimension_key: str,
                       size_metric: str = "cost_micros",
                       color_metric: str = "conversions",
                       title: str = "Performance Breakdown Treemap") -> Dict[str, Any]:
    """
    Create a treemap chart showing the breakdown of a metric by dimension.
    
    Args:
        data: List of segment data points
        dimension_key: The key for the dimension being broken down
        size_metric: Metric to determine box size (typically cost or impressions)
        color_metric: Metric to determine box color (e.g., conversions, CTR)
        title: Chart title
        
    Returns:
        Chart data structure compatible with Claude Artifacts
    """
    logger.info(f"Creating treemap chart for dimension {dimension_key}")
    
    if not data:
        return {
            "type": "treemap",
            "title": title,
            "data": {
                "datasets": []
            }
        }
    
    # Configure metrics with appropriate display formatting
    metric_config = {
        "cost_micros": {"label": "Cost", "format": "currency"},
        "impressions": {"label": "Impressions", "format": "number"},
        "clicks": {"label": "Clicks", "format": "number"},
        "conversions": {"label": "Conversions", "format": "number"},
        "ctr": {"label": "CTR", "format": "percentage"},
        "average_cpc": {"label": "Avg. CPC", "format": "currency"},
        "conversion_rate": {"label": "Conv. Rate", "format": "percentage"},
        "cost_per_conversion": {"label": "Cost/Conv.", "format": "currency"}
    }
    
    # Process and prepare data
    treemap_data = []
    for item in data:
        dimension_value = item.get(dimension_key, "Unknown")
        size_value = item.get(size_metric, 0)
        color_value = item.get(color_metric, 0)
        
        # Format size value if needed
        if size_metric.endswith("_micros"):
            size_value = _format_currency_micros(size_value)
        
        # Format color value if needed
        if color_metric.endswith("_micros"):
            color_value = _format_currency_micros(color_value)
        elif color_metric in ["ctr", "conversion_rate"]:
            color_value = _format_percentage(color_value)
        
        treemap_data.append({
            "name": dimension_value,
            "value": size_value,
            "colorValue": color_value
        })
    
    # Get labels for the metrics
    size_label = metric_config.get(size_metric, {}).get("label", size_metric.replace("_", " ").title())
    color_label = metric_config.get(color_metric, {}).get("label", color_metric.replace("_", " ").title())
    
    # Create the treemap chart structure
    chart = {
        "type": "treemap",
        "title": title,
        "data": {
            "datasets": [{
                "tree": treemap_data,
                "key": "value",
                "groups": ["name"],
                "spacing": 2,
                "borderWidth": 1,
                "borderColor": "rgba(255,255,255,0.5)",
                "colorValue": "colorValue"
            }]
        },
        "options": {
            "plugins": {
                "title": {
                    "display": True,
                    "text": f"Size: {size_label}, Color: {color_label}"
                },
                "tooltip": {
                    "callbacks": {
                        "title": "function(context) { return context[0].raw.name; }",
                        "label": f"function(context) {{ return '{size_label}: ' + context.raw.value + ', {color_label}: ' + context.raw.colorValue; }}"
                    }
                }
            }
        }
    }
    
    return chart

def create_time_breakdown_chart(data: List[Dict[str, Any]],
                              time_key: str,
                              metrics: List[str],
                              title: str = "Performance Over Time") -> Dict[str, Any]:
    """
    Create a line chart showing performance over time.
    
    Args:
        data: List of time-based data points
        time_key: The key for the time dimension ('date', 'week', 'month')
        metrics: List of metrics to include
        title: Chart title
        
    Returns:
        Chart data structure compatible with Claude Artifacts
    """
    logger.info(f"Creating time breakdown chart for time dimension {time_key}")
    
    if not data or not metrics:
        return {
            "type": "line",
            "title": title,
            "data": {
                "labels": [],
                "datasets": []
            }
        }
    
    # Sort data by time
    data_sorted = sorted(data, key=lambda x: x.get(time_key, ""))
    
    # Extract time values (labels for x-axis)
    time_values = [item.get(time_key, "") for item in data_sorted]
    
    # Configure metrics with appropriate display formatting
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
    
    # Create datasets for each metric
    datasets = []
    for metric in metrics:
        # Get display info for the metric
        if metric in metric_config:
            display_name = metric_config[metric]["label"]
            format_type = metric_config[metric]["format"]
            color = metric_config[metric]["color"]
        else:
            display_name = metric.replace("_", " ").title()
            format_type = "number"
            color = "rgba(128, 128, 128, 1)"
        
        # Extract and format values for this metric
        values = []
        for item in data_sorted:
            value = item.get(metric, 0)
            
            # Apply appropriate formatting
            if format_type == "currency" and metric.endswith("_micros"):
                value = _format_currency_micros(value)
            elif format_type == "percentage":
                value = _format_percentage(value)
                
            values.append(value)
        
        datasets.append({
            "label": display_name,
            "data": values,
            "borderColor": color,
            "backgroundColor": color.replace("1)", "0.1)"),
            "tension": 0.4  # Adds slight curve to lines
        })
    
    # Create the final chart structure
    chart = {
        "type": "line",
        "title": title,
        "data": {
            "labels": time_values,
            "datasets": datasets
        },
        "options": {
            "scales": {
                "y": {
                    "beginAtZero": True
                }
            },
            "plugins": {
                "legend": {
                    "position": "top"
                },
                "tooltip": {
                    "mode": "index",
                    "intersect": False
                }
            }
        }
    }
    
    return chart

def format_breakdown_visualization(breakdown_data: Dict[str, Any], 
                                 title: str = "Performance Breakdown") -> Dict[str, Any]:
    """
    Create a comprehensive breakdown visualization.
    
    This creates appropriate visualizations based on the dimension:
    - Time dimensions: Line charts showing trends
    - Categorical dimensions: Stacked bar charts + tables + treemaps
    
    Args:
        breakdown_data: Breakdown data containing dimension segments
        title: Title for the visualizations
        
    Returns:
        Complete visualization data structure for Claude Artifacts
    """
    logger.info("Creating comprehensive breakdown visualization")
    
    # Initialize visualization containers
    charts = []
    tables = []
    
    # Extract information from breakdown data
    entity_type = breakdown_data.get("entity_type", "unknown")
    entity_name = breakdown_data.get("entity_name", "Unknown")
    display_title = f"{entity_name} {title}" if entity_name and entity_name != "Unknown" else title
    
    # Process each dimension's data
    for dimension_data in breakdown_data.get("data", []):
        dimension = dimension_data.get("dimension", "unknown")
        segments = dimension_data.get("segments", [])
        
        if not segments:
            continue
        
        # Determine available metrics by examining the first segment
        available_metrics = []
        if segments:
            sample = segments[0]
            for key, value in sample.items():
                if key not in ["id", "name", "date", "week", "month", "device", "network", "geo", "country", "region"] and \
                   isinstance(value, (int, float)):
                    available_metrics.append(key)
        
        # Different visualization types based on dimension
        dimension_title = f"{display_title} by {dimension.title()}"
        
        # For time-based dimensions
        if dimension in ["day", "week", "month"]:
            # Time series chart
            time_chart = create_time_breakdown_chart(
                data=segments,
                time_key=dimension,
                metrics=available_metrics[:3],  # Limit to 3 metrics for readability
                title=dimension_title
            )
            charts.append(time_chart)
            
            # Table for detailed time data
            time_table = create_breakdown_table(
                data=segments,
                dimension_key=dimension,
                metrics=available_metrics,
                title=f"{dimension_title} - Details"
            )
            tables.append(time_table)
        
        # For categorical dimensions
        elif dimension in ["device", "network", "geo"]:
            # Stacked bar chart for a few key metrics
            primary_metrics = []
            for metric in ["cost_micros", "clicks", "conversions"]:
                if metric in available_metrics:
                    primary_metrics.append(metric)
            
            if primary_metrics:
                stacked_chart = create_stacked_bar_chart(
                    data=segments,
                    dimension_key=dimension,
                    metrics=primary_metrics,
                    title=dimension_title
                )
                charts.append(stacked_chart)
            
            # Detailed table for all metrics
            detail_table = create_breakdown_table(
                data=segments,
                dimension_key=dimension,
                metrics=available_metrics,
                title=f"{dimension_title} - Details"
            )
            tables.append(detail_table)
            
            # Treemap for cost/conversions overview
            if "cost_micros" in available_metrics and len(segments) >= 3:
                # Determine color metric (preferably conversions or CTR)
                color_metric = "cost_micros"  # Default
                for metric in ["conversions", "conversion_rate", "ctr"]:
                    if metric in available_metrics:
                        color_metric = metric
                        break
                
                treemap = create_treemap_chart(
                    data=segments,
                    dimension_key=dimension,
                    size_metric="cost_micros",
                    color_metric=color_metric,
                    title=f"{dimension_title} - Distribution"
                )
                charts.append(treemap)
    
    # Compile the visualization
    visualization = {
        "charts": charts,
        "tables": tables
    }
    
    return visualization 