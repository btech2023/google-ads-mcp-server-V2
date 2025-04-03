"""
Comparison Charts Visualization Module

This module provides functions for formatting comparison charts data (bar and pie charts) for visualization.
"""

import logging
from typing import Dict, Any, List, Optional
import math

logger = logging.getLogger(__name__)

def format_bar_chart(data: List[Dict[str, Any]], metrics: Optional[List[str]] = None,
                   category_key: str = "name", title: str = "Bar Chart", 
                   subtitle: str = None) -> Dict[str, Any]:
    """
    Format data as a bar chart for visualization.
    
    Args:
        data: List of dictionaries containing data
        metrics: Optional list of metrics to include
        category_key: The key in data items for the category axis
        title: Chart title
        subtitle: Optional chart subtitle
        
    Returns:
        Formatted bar chart data for visualization
    """
    logger.info(f"Formatting bar chart visualization with {len(data)} data points")
    
    if not data:
        return {
            "chart_type": "bar",
            "title": title,
            "subtitle": subtitle or "No data available",
            "axes": {},
            "series": [],
            "data": []
        }
    
    # If metrics not specified, use first numeric value in the data
    if not metrics:
        # Get sample item to determine metrics
        sample = data[0]
        metrics = []
        for key, value in sample.items():
            if key != category_key and isinstance(value, (int, float)):
                metrics.append(key)
                if len(metrics) >= 3:  # Limit to 3 metrics for better readability
                    break
    
    # Create series specifications
    series = []
    colors = ["#8884d8", "#82ca9d", "#ffc658", "#ff8042", "#a4de6c", "#d0ed57", "#8dd1e1", "#83a6ed"]
    
    metrics_config = {
        "impressions": {"name": "Impressions", "color": "#8884d8"},
        "clicks": {"name": "Clicks", "color": "#82ca9d"},
        "cost": {"name": "Cost", "color": "#ff8042"},
        "conversions": {"name": "Conversions", "color": "#8dd1e1"},
        "ctr": {"name": "CTR", "color": "#a4de6c"},
        "cpc": {"name": "CPC", "color": "#d0ed57"},
        "conversion_rate": {"name": "Conversion Rate", "color": "#ffc658"},
        "cost_per_conversion": {"name": "Cost per Conversion", "color": "#83a6ed"}
    }
    
    for i, metric in enumerate(metrics):
        config = metrics_config.get(metric, {})
        name = config.get("name", metric.replace("_", " ").title())
        color = config.get("color", colors[i % len(colors)])
        
        series.append({
            "name": name,
            "dataKey": metric,
            "color": color,
            "type": "bar"
        })
    
    # Return the formatted bar chart data
    visualization_data = {
        "chart_type": "bar",
        "title": title,
        "subtitle": subtitle,
        "data": data,
        "axes": {
            "x": {
                "label": category_key.replace("_", " ").title(),
                "dataKey": category_key,
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

def format_pie_chart(data: List[Dict[str, Any]], metric: str = None,
                   category_key: str = "name", title: str = "Pie Chart", 
                   subtitle: str = None) -> Dict[str, Any]:
    """
    Format data as a pie chart for visualization.
    
    Args:
        data: List of dictionaries containing data
        metric: The metric to visualize (required for pie charts)
        category_key: The key in data items for categories
        title: Chart title
        subtitle: Optional chart subtitle
        
    Returns:
        Formatted pie chart data for visualization
    """
    logger.info(f"Formatting pie chart visualization with {len(data)} data points")
    
    if not data:
        return {
            "chart_type": "pie",
            "title": title,
            "subtitle": subtitle or "No data available",
            "data": []
        }
    
    # If metric not specified, use first numeric value in the data
    if not metric:
        # Get sample item to determine metric
        sample = data[0]
        for key, value in sample.items():
            if key != category_key and isinstance(value, (int, float)):
                metric = key
                break
    
    if not metric:
        logger.warning("No numeric metric found for pie chart")
        return {
            "chart_type": "pie",
            "title": title,
            "subtitle": "No suitable metric found for visualization",
            "data": []
        }
    
    # Create a color palette
    colors = ["#8884d8", "#82ca9d", "#ffc658", "#ff8042", "#a4de6c", "#d0ed57", "#8dd1e1", "#83a6ed"]
    
    # Prepare the data
    pie_data = []
    for i, item in enumerate(data):
        if category_key in item and metric in item:
            pie_data.append({
                "name": item[category_key],
                "value": item[metric],
                "color": colors[i % len(colors)]
            })
    
    # Sort by value descending
    pie_data.sort(key=lambda x: x["value"], reverse=True)
    
    # Return the formatted pie chart data
    visualization_data = {
        "chart_type": "pie",
        "title": title,
        "subtitle": subtitle or f"Showing {metric.replace('_', ' ').title()} by {category_key.replace('_', ' ').title()}",
        "dataKey": "value",
        "nameKey": "name",
        "colorKey": "color",
        "data": pie_data,
        "legend": True,
        "tooltip": True
    }
    
    return visualization_data

def _format_currency_micros(value_micros: int) -> float:
    """Format a micro-amount to standard currency units."""
    return value_micros / 1000000.0 if value_micros else 0.0

def _format_percentage(value: float) -> float:
    """Format a ratio as a percentage with 2 decimal places."""
    return round(value * 100, 2) if value is not None else 0.0

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

def create_comparison_bar_chart(entities: List[Dict[str, Any]], 
                              metrics: List[str], 
                              entity_name_key: str = "name",
                              title: str = "Performance Comparison") -> Dict[str, Any]:
    """
    Create a side-by-side bar chart comparing metrics across multiple entities.
    
    Args:
        entities: List of entity data (campaigns, ad groups, etc.)
        metrics: List of metrics to compare (e.g., 'cost_micros', 'clicks')
        entity_name_key: Key in entity data for the entity name
        title: Chart title
        
    Returns:
        Chart data structure compatible with Claude Artifacts
    """
    logger.info(f"Creating comparison bar chart for {len(entities)} entities")
    
    if not entities or not metrics:
        return {
            "type": "bar",
            "title": title,
            "data": {
                "labels": [],
                "datasets": []
            }
        }
    
    # Prepare chart structure
    chart_labels = [entity.get(entity_name_key, f"Entity {i+1}") for i, entity in enumerate(entities)]
    
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
        if metric not in metric_config:
            # Use default config for unknown metrics
            display_name = metric.replace("_", " ").title()
            format_type = "number"
            color = "rgba(128, 128, 128, 0.8)"
        else:
            display_name = metric_config[metric]["label"]
            format_type = metric_config[metric]["format"]
            color = metric_config[metric]["color"]
        
        # Extract and format values for this metric
        values = []
        for entity in entities:
            value = entity.get(metric, 0)
            
            # Apply appropriate formatting
            if format_type == "currency" and metric.endswith("_micros"):
                value = _format_currency_micros(value)
            elif format_type == "percentage":
                value = _format_percentage(value)
                
            values.append(value)
        
        datasets.append({
            "label": display_name,
            "data": values,
            "backgroundColor": color
        })
    
    # Create the final chart structure
    chart = {
        "type": "bar",
        "title": title,
        "data": {
            "labels": chart_labels,
            "datasets": datasets
        },
        "options": {
            "scales": {
                "y": {
                    "beginAtZero": True
                }
            },
            "indexAxis": "x",  # Vertical bars
            "barPercentage": 0.8,
            "categoryPercentage": 0.9,
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

def create_comparison_data_table(entities: List[Dict[str, Any]],
                               metrics: List[str],
                               entity_name_key: str = "name",
                               title: str = "Performance Comparison",
                               include_change: bool = True,
                               baseline_entity_index: int = 0) -> Dict[str, Any]:
    """
    Create a detailed data table showing metrics and their differences across entities.
    
    Args:
        entities: List of entity data (campaigns, ad groups, etc.)
        metrics: List of metrics to compare
        entity_name_key: Key in entity data for the entity name
        title: Table title
        include_change: Whether to include change calculation (absolute/relative diffs)
        baseline_entity_index: Index of the entity to use as baseline for change calculations
        
    Returns:
        Table data structure compatible with Claude Artifacts
    """
    logger.info(f"Creating comparison data table for {len(entities)} entities")
    
    if not entities or not metrics:
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
    
    # Build headers: Metric name followed by entity names 
    headers = ["Metric"]
    for entity in entities:
        headers.append(entity.get(entity_name_key, "Unknown entity"))
    
    if include_change and len(entities) > 1:
        headers.append("Change (vs " + entities[baseline_entity_index].get(entity_name_key, "Baseline") + ")")
    
    # Generate rows for each metric
    rows = []
    for metric in metrics:
        # Get metric display info
        if metric in metric_config:
            display_name = metric_config[metric]["label"]
            format_type = metric_config[metric]["format"]
            tooltip = metric_config[metric]["tooltip"]
        else:
            display_name = metric.replace("_", " ").title()
            format_type = "number"
            tooltip = ""
        
        row = [display_name]
        
        # Get values for each entity
        values = []
        for entity in entities:
            value = entity.get(metric, 0)
            
            # Apply appropriate formatting
            if format_type == "currency" and metric.endswith("_micros"):
                value = _format_currency_micros(value)
                formatted_value = f"${value:.2f}"
            elif format_type == "percentage":
                value = _format_percentage(value)
                formatted_value = f"{value:.2f}%"
            else:
                formatted_value = f"{value:,}"
            
            values.append(value)  # Store the raw value
            row.append(formatted_value)  # Add the formatted value to the row
        
        # Add change column if requested and we have multiple entities
        if include_change and len(entities) > 1:
            baseline_value = values[baseline_entity_index]
            
            # Calculate average change against baseline for other entities
            changes = []
            for i, val in enumerate(values):
                if i != baseline_entity_index:
                    changes.append(_calculate_change(val, baseline_value))
            
            # Check if we have any changes to calculate
            if changes:
                # Calculate average change
                avg_pct_change = sum(c["percentage"] for c in changes) / len(changes)
                
                # Format the change
                if format_type == "currency":
                    change_display = f"{avg_pct_change:+.2f}%"
                elif format_type == "percentage":
                    change_display = f"{avg_pct_change:+.2f}pp"  # percentage points
                else:
                    change_display = f"{avg_pct_change:+.2f}%"
                
                row.append(change_display)
            else:
                row.append("N/A")
        
        rows.append(row)
    
    # Create the final table structure
    table = {
        "title": title,
        "headers": headers,
        "rows": rows
    }
    
    return table

def create_comparison_radar_chart(entities: List[Dict[str, Any]], 
                                metrics: List[str],
                                entity_name_key: str = "name",
                                title: str = "Multi-Metric Comparison") -> Dict[str, Any]:
    """
    Create a radar chart for comparing multiple metrics across entities.
    Radar charts are good for visualizing the relative strengths/weaknesses of 
    entities across multiple dimensions.
    
    Args:
        entities: List of entity data (campaigns, ad groups, etc.)
        metrics: List of metrics to compare (ideally 3-6 metrics for readability)
        entity_name_key: Key in entity data for the entity name
        title: Chart title
        
    Returns:
        Radar chart data structure compatible with Claude Artifacts
    """
    logger.info(f"Creating comparison radar chart for {len(entities)} entities and {len(metrics)} metrics")
    
    if not entities or not metrics:
        return {
            "type": "radar",
            "title": title,
            "data": {
                "labels": [],
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
    
    # Prepare metric labels for the chart axes
    metric_labels = []
    for metric in metrics:
        if metric in metric_config:
            metric_labels.append(metric_config[metric]["label"])
        else:
            metric_labels.append(metric.replace("_", " ").title())
    
    # Find the maximum value for each metric to normalize values
    max_values = {}
    for metric in metrics:
        values = [entity.get(metric, 0) for entity in entities]
        
        # Skip if all values are zero
        if all(v == 0 for v in values):
            max_values[metric] = 1  # Avoid division by zero
        else:
            max_values[metric] = max(values)
    
    # Define colors for each entity
    colors = [
        "rgba(66, 133, 244, 0.7)", "rgba(219, 68, 55, 0.7)", "rgba(15, 157, 88, 0.7)", 
        "rgba(244, 180, 0, 0.7)", "rgba(180, 0, 244, 0.7)", "rgba(0, 244, 180, 0.7)"
    ]
    
    # Create datasets for each entity
    datasets = []
    for i, entity in enumerate(entities):
        entity_name = entity.get(entity_name_key, f"Entity {i+1}")
        color = colors[i % len(colors)]
        border_color = color.replace("0.7", "1.0")
        
        # Normalize values to a 0-100 scale
        normalized_values = []
        for metric in metrics:
            raw_value = entity.get(metric, 0)
            
            # For inverse metrics (like CPCs or CPAs), lower is better
            if metric in ["average_cpc", "cost_per_conversion"]:
                # For inverse metrics, if the value is 0, just show 0
                if raw_value == 0:
                    normalized_value = 0
                else:
                    # Invert the normalization: smaller value = higher score
                    max_val = max_values[metric]
                    if max_val > 0:
                        normalized_value = (1 - (raw_value / max_val)) * 100
                    else:
                        normalized_value = 0
            else:
                # Standard normalization: larger value = higher score
                max_val = max_values[metric]
                if max_val > 0:
                    normalized_value = (raw_value / max_val) * 100
                else:
                    normalized_value = 0
            
            normalized_values.append(normalized_value)
        
        datasets.append({
            "label": entity_name,
            "data": normalized_values,
            "backgroundColor": color,
            "borderColor": border_color,
            "pointBackgroundColor": border_color,
            "pointRadius": 4
        })
    
    # Create the final radar chart structure
    chart = {
        "type": "radar",
        "title": title,
        "data": {
            "labels": metric_labels,
            "datasets": datasets
        },
        "options": {
            "plugins": {
                "legend": {
                    "position": "top"
                },
                "tooltip": {
                    "callbacks": {
                        "label": "function(context) { return context.dataset.label + ': ' + context.formattedValue + '%'; }"
                    }
                }
            },
            "scales": {
                "r": {
                    "min": 0,
                    "max": 100,
                    "beginAtZero": True,
                    "angleLines": {
                        "display": True
                    },
                    "ticks": {
                        "display": False
                    }
                }
            }
        }
    }
    
    return chart

def format_comparison_visualization(comparison_data: Dict[str, Any], 
                                  metrics: Optional[List[str]] = None,
                                  title: str = "Performance Comparison") -> Dict[str, Any]:
    """
    Create a comprehensive comparison visualization.
    
    This combines multiple visualization components:
    - Side-by-side bar chart for primary metrics
    - Data table showing absolute and relative differences
    - Optional radar chart for multi-metric overview
    
    Args:
        comparison_data: Comparison data containing entities to compare
        metrics: Optional list of metrics to include
        title: Title for the visualizations
        
    Returns:
        Complete visualization data structure for Claude Artifacts
    """
    logger.info("Creating comprehensive comparison visualization")
    
    # Extract entities from comparison data
    entities = comparison_data.get("campaigns", [])
    if not entities:
        entities = comparison_data.get("ad_groups", [])
    
    if not entities:
        return {
            "charts": [],
            "tables": [{
                "title": title,
                "headers": ["No data available"],
                "rows": []
            }]
        }
    
    # If metrics not provided, use the ones in the comparison data
    if not metrics:
        metrics = comparison_data.get("metrics", [])
    
    if not metrics and entities:
        # Try to infer metrics from the first entity
        sample = entities[0]
        for key, value in sample.items():
            if key not in ["id", "name", "status"] and isinstance(value, (int, float)):
                metrics.append(key)
    
    # Create visualizations
    charts = []
    tables = []
    
    # 1. Bar chart for primary metrics (limit to top 3 for readability)
    primary_metrics = metrics[:3] if len(metrics) > 3 else metrics
    bar_chart = create_comparison_bar_chart(
        entities=entities,
        metrics=primary_metrics,
        title=f"{title} - Key Metrics"
    )
    charts.append(bar_chart)
    
    # 2. Data table showing all metrics with comparisons
    data_table = create_comparison_data_table(
        entities=entities,
        metrics=metrics,
        title=f"{title} - Detailed Comparison"
    )
    tables.append(data_table)
    
    # 3. If we have enough metrics (>= 3), add a radar chart
    if len(metrics) >= 3:
        radar_chart = create_comparison_radar_chart(
            entities=entities,
            metrics=metrics,
            title=f"{title} - Multi-Metric Overview"
        )
        charts.append(radar_chart)
    
    # Compile the visualization
    visualization = {
        "charts": charts,
        "tables": tables
    }
    
    return visualization
