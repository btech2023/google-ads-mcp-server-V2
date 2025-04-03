"""
Insights Visualization Module

This module provides visualization formatting functions for Google Ads insights,
including anomaly detection, optimization suggestions, and opportunity discovery.
"""

from typing import Dict, List, Any, Optional
import json

def format_anomalies_visualization(anomalies_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format anomaly detection data for visualization.
    
    Args:
        anomalies_data: Dictionary containing detected anomalies
        
    Returns:
        Dictionary with formatted visualization data for anomalies
    """
    anomalies = anomalies_data.get("anomalies", [])
    metadata = anomalies_data.get("metadata", {})
    
    if not anomalies:
        return {
            "type": "text",
            "content": "No anomalies detected in the selected time period."
        }
    
    # Group anomalies by entity
    entity_anomalies = {}
    for anomaly in anomalies:
        entity_id = anomaly.get("entity_id", "unknown")
        if entity_id not in entity_anomalies:
            entity_anomalies[entity_id] = {
                "entity_id": entity_id,
                "entity_name": anomaly.get("entity_name", "Unknown"),
                "entity_type": anomaly.get("entity_type", "UNKNOWN"),
                "anomalies": []
            }
        
        entity_anomalies[entity_id]["anomalies"].append(anomaly)
    
    # Create visualization components
    visualizations = []
    
    # 1. Summary card
    summary_card = {
        "type": "card",
        "title": "Anomaly Detection Summary",
        "content": [
            {
                "type": "keyValue",
                "key": "Date Range",
                "value": f"{metadata.get('start_date', 'unknown')} to {metadata.get('end_date', 'unknown')}"
            },
            {
                "type": "keyValue",
                "key": "Entity Type",
                "value": metadata.get("entity_type", "Unknown")
            },
            {
                "type": "keyValue",
                "key": "Total Entities Analyzed",
                "value": str(metadata.get("total_entities_analyzed", 0))
            },
            {
                "type": "keyValue",
                "key": "Anomalies Detected",
                "value": str(metadata.get("anomalies_detected", 0))
            }
        ]
    }
    visualizations.append(summary_card)
    
    # 2. Anomaly bar chart
    if len(anomalies) > 0:
        # Count anomalies by metric
        metric_counts = {}
        for anomaly in anomalies:
            metric = anomaly.get("metric", "unknown")
            if metric not in metric_counts:
                metric_counts[metric] = 0
            metric_counts[metric] += 1
        
        # Prepare data for bar chart
        bar_data = [
            {"metric": metric, "count": count}
            for metric, count in metric_counts.items()
        ]
        
        bar_chart = {
            "type": "bar",
            "title": "Anomalies by Metric",
            "description": f"Distribution of {len(anomalies)} detected anomalies across metrics",
            "data": bar_data,
            "xAxis": "metric",
            "yAxis": "count",
            "labels": {"xAxis": "Metric", "yAxis": "Number of Anomalies"}
        }
        visualizations.append(bar_chart)
    
    # 3. Top anomalies table
    top_anomalies = sorted(
        anomalies, 
        key=lambda x: (0 if x.get("severity") == "HIGH" else 1, abs(x.get("percent_change", 0))),
        reverse=True
    )[:10]  # Get top 10 anomalies
    
    if top_anomalies:
        # Format table rows
        table_rows = []
        for anomaly in top_anomalies:
            entity_name = anomaly.get("entity_name", "Unknown")
            metric = anomaly.get("metric", "unknown")
            current = anomaly.get("current_value", 0)
            previous = anomaly.get("comparison_value", 0)
            percent_change = anomaly.get("percent_change", 0)
            direction = anomaly.get("direction", "")
            severity = anomaly.get("severity", "")
            
            # Format values
            if metric.lower() in ["cost", "conversion_value"]:
                current_formatted = f"${current:.2f}"
                previous_formatted = f"${previous:.2f}"
            elif metric.lower() in ["ctr", "cvr", "conversion_rate"]:
                current_formatted = f"{current:.2%}"
                previous_formatted = f"{previous:.2%}"
            else:
                current_formatted = f"{current:,.0f}" if current >= 10 else f"{current:.2f}"
                previous_formatted = f"{previous:,.0f}" if previous >= 10 else f"{previous:.2f}"
            
            # Create row
            row = {
                "entity": entity_name,
                "metric": metric.replace("_", " ").title(),
                "current": current_formatted,
                "previous": previous_formatted,
                "change": f"{'+' if percent_change > 0 else ''}{percent_change:.1f}%",
                "severity": severity
            }
            table_rows.append(row)
        
        # Create table component
        anomalies_table = {
            "type": "table",
            "title": "Top Anomalies",
            "description": "Most significant changes in performance metrics",
            "columns": [
                {"key": "entity", "label": "Entity"},
                {"key": "metric", "label": "Metric"},
                {"key": "current", "label": "Current"},
                {"key": "previous", "label": "Previous"},
                {"key": "change", "label": "Change"},
                {"key": "severity", "label": "Severity"}
            ],
            "rows": table_rows
        }
        visualizations.append(anomalies_table)
    
    return {
        "type": "artifact",
        "format": "json",
        "content": visualizations
    }

def format_optimization_suggestions_visualization(suggestions_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format optimization suggestions data for visualization.
    
    Args:
        suggestions_data: Dictionary containing optimization suggestions
        
    Returns:
        Dictionary with formatted visualization data for suggestions
    """
    suggestions = suggestions_data.get("suggestions", {})
    metadata = suggestions_data.get("metadata", {})
    
    total_suggestions = metadata.get("total_suggestions", 0)
    
    if total_suggestions == 0:
        return {
            "type": "text",
            "content": "No optimization suggestions available for the selected criteria."
        }
    
    # Flatten suggestions for easier processing
    all_suggestions = []
    for category, category_suggestions in suggestions.items():
        for suggestion in category_suggestions:
            suggestion["category"] = category
            all_suggestions.append(suggestion)
    
    # Sort suggestions by impact
    all_suggestions = sorted(
        all_suggestions,
        key=lambda x: 0 if x.get("impact") == "HIGH" else (1 if x.get("impact") == "MEDIUM" else 2)
    )
    
    # Create visualization components
    visualizations = []
    
    # 1. Summary card
    summary_card = {
        "type": "card",
        "title": "Optimization Suggestions Summary",
        "content": [
            {
                "type": "keyValue",
                "key": "Date Range",
                "value": f"{metadata.get('start_date', 'unknown')} to {metadata.get('end_date', 'unknown')}"
            },
            {
                "type": "keyValue",
                "key": "Total Suggestions",
                "value": str(total_suggestions)
            }
        ]
    }
    
    # Add category counts
    for category, category_suggestions in suggestions.items():
        if category_suggestions:
            formatted_category = category.replace("_", " ").title()
            summary_card["content"].append({
                "type": "keyValue",
                "key": formatted_category,
                "value": str(len(category_suggestions))
            })
    
    visualizations.append(summary_card)
    
    # 2. Suggestions by category pie chart
    category_counts = {
        category.replace("_", " ").title(): len(category_suggestions)
        for category, category_suggestions in suggestions.items()
        if category_suggestions
    }
    
    if category_counts:
        pie_data = [
            {"category": category, "count": count}
            for category, count in category_counts.items()
        ]
        
        pie_chart = {
            "type": "pie",
            "title": "Suggestions by Category",
            "description": "Distribution of optimization suggestions across categories",
            "data": pie_data,
            "value": "count",
            "label": "category"
        }
        visualizations.append(pie_chart)
    
    # 3. High impact suggestions table
    high_impact_suggestions = [s for s in all_suggestions if s.get("impact") == "HIGH"]
    if high_impact_suggestions:
        # Format table rows
        table_rows = []
        for suggestion in high_impact_suggestions[:10]:  # Limit to top 10
            entity_type = suggestion.get("entity_type", "").title()
            entity_name = suggestion.get("entity_name", suggestion.get("entity_text", "Unknown"))
            category = suggestion.get("category", "").replace("_", " ").title()
            suggestion_text = suggestion.get("suggestion", "")
            
            # Create row
            row = {
                "entity": f"{entity_type}: {entity_name}",
                "category": category,
                "suggestion": suggestion_text,
                "impact": suggestion.get("impact", "")
            }
            table_rows.append(row)
        
        # Create table component
        high_impact_table = {
            "type": "table",
            "title": "High Impact Optimization Suggestions",
            "description": "Suggestions that could significantly improve performance",
            "columns": [
                {"key": "entity", "label": "Entity"},
                {"key": "category", "label": "Category"},
                {"key": "suggestion", "label": "Suggestion"},
                {"key": "impact", "label": "Impact"}
            ],
            "rows": table_rows
        }
        visualizations.append(high_impact_table)
    
    # 4. All suggestions grouped by category (accordion/expandable sections)
    category_sections = []
    
    for category, category_suggestions in suggestions.items():
        if not category_suggestions:
            continue
            
        formatted_category = category.replace("_", " ").title()
        
        suggestion_items = []
        for suggestion in category_suggestions:
            entity_type = suggestion.get("entity_type", "").title()
            entity_name = suggestion.get("entity_name", suggestion.get("entity_text", "Unknown"))
            suggestion_text = suggestion.get("suggestion", "")
            action = suggestion.get("action", "")
            impact = suggestion.get("impact", "MEDIUM")
            
            suggestion_item = {
                "type": "listItem",
                "title": f"{entity_type}: {entity_name}",
                "description": suggestion_text,
                "subtitle": f"Impact: {impact}",
                "content": action
            }
            suggestion_items.append(suggestion_item)
        
        category_section = {
            "type": "section",
            "title": formatted_category,
            "content": suggestion_items
        }
        category_sections.append(category_section)
    
    if category_sections:
        all_suggestions_component = {
            "type": "accordion",
            "title": "All Optimization Suggestions",
            "sections": category_sections
        }
        visualizations.append(all_suggestions_component)
    
    return {
        "type": "artifact",
        "format": "json",
        "content": visualizations
    }

def format_opportunities_visualization(opportunities_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format opportunity discovery data for visualization.
    
    Args:
        opportunities_data: Dictionary containing identified opportunities
        
    Returns:
        Dictionary with formatted visualization data for opportunities
    """
    opportunities = opportunities_data.get("opportunities", {})
    metadata = opportunities_data.get("metadata", {})
    
    total_opportunities = metadata.get("total_opportunities", 0)
    
    if total_opportunities == 0:
        return {
            "type": "text",
            "content": "No growth opportunities identified for the selected criteria."
        }
    
    # Create visualization components
    visualizations = []
    
    # 1. Summary card
    summary_card = {
        "type": "card",
        "title": "Growth Opportunities Summary",
        "content": [
            {
                "type": "keyValue",
                "key": "Date Range",
                "value": f"{metadata.get('start_date', 'unknown')} to {metadata.get('end_date', 'unknown')}"
            },
            {
                "type": "keyValue",
                "key": "Total Opportunities",
                "value": str(total_opportunities)
            }
        ]
    }
    
    # Add category counts
    for category, category_opportunities in opportunities.items():
        if category_opportunities:
            formatted_category = category.replace("_", " ").title()
            summary_card["content"].append({
                "type": "keyValue",
                "key": formatted_category,
                "value": str(len(category_opportunities))
            })
    
    visualizations.append(summary_card)
    
    # 2. Opportunities by category pie chart
    category_counts = {
        category.replace("_", " ").title(): len(category_opportunities)
        for category, category_opportunities in opportunities.items()
        if category_opportunities
    }
    
    if category_counts:
        pie_data = [
            {"category": category, "count": count}
            for category, count in category_counts.items()
        ]
        
        pie_chart = {
            "type": "pie",
            "title": "Opportunities by Category",
            "description": "Distribution of growth opportunities across categories",
            "data": pie_data,
            "value": "count",
            "label": "category"
        }
        visualizations.append(pie_chart)
    
    # 3. Process each category of opportunities
    for category, category_opportunities in opportunities.items():
        if not category_opportunities:
            continue
            
        formatted_category = category.replace("_", " ").title()
        
        # Create section for this category
        if category == "keyword_expansion" and category_opportunities:
            # For keyword expansion, create a table of search terms to add
            table_rows = []
            for opportunity in category_opportunities[:10]:  # Limit to top 10
                search_term = opportunity.get("search_term", "")
                match_type = opportunity.get("suggested_match_type", "")
                ad_group = opportunity.get("ad_group_name", "Unknown")
                impressions = opportunity.get("impressions", 0)
                clicks = opportunity.get("clicks", 0)
                conversions = opportunity.get("conversions", 0)
                
                # Create row
                row = {
                    "term": search_term,
                    "match_type": match_type,
                    "ad_group": ad_group,
                    "impressions": f"{impressions:,}",
                    "clicks": f"{clicks:,}",
                    "conversions": f"{conversions:,}"
                }
                table_rows.append(row)
            
            if table_rows:
                keyword_table = {
                    "type": "table",
                    "title": "Keyword Expansion Opportunities",
                    "description": "High-performing search terms that could be added as keywords",
                    "columns": [
                        {"key": "term", "label": "Search Term"},
                        {"key": "match_type", "label": "Match Type"},
                        {"key": "ad_group", "label": "Ad Group"},
                        {"key": "impressions", "label": "Impressions"},
                        {"key": "clicks", "label": "Clicks"},
                        {"key": "conversions", "label": "Conversions"}
                    ],
                    "rows": table_rows
                }
                visualizations.append(keyword_table)
                
        elif category == "ad_variation" and category_opportunities:
            # For ad variations, create a list of ad groups needing variations
            ad_items = []
            for opportunity in category_opportunities:
                entity_name = opportunity.get("entity_name", "Unknown")
                campaign_name = opportunity.get("campaign_name", "Unknown")
                opportunity_text = opportunity.get("opportunity", "")
                action = opportunity.get("action", "")
                impact = opportunity.get("impact", "MEDIUM")
                
                ad_item = {
                    "type": "listItem",
                    "title": entity_name,
                    "description": opportunity_text,
                    "subtitle": f"Campaign: {campaign_name} | Impact: {impact}",
                    "content": action
                }
                ad_items.append(ad_item)
            
            if ad_items:
                ad_variations_component = {
                    "type": "list",
                    "title": "Ad Variation Opportunities",
                    "description": "Ad groups that would benefit from additional ad variations",
                    "items": ad_items
                }
                visualizations.append(ad_variations_component)
                
        elif category == "structure" and category_opportunities:
            # For structure opportunities, create a list
            structure_items = []
            for opportunity in category_opportunities:
                entity_name = opportunity.get("entity_name", "Unknown")
                entity_type = opportunity.get("entity_type", "").title()
                campaign_name = opportunity.get("campaign_name", "Unknown")
                opportunity_text = opportunity.get("opportunity", "")
                action = opportunity.get("action", "")
                impact = opportunity.get("impact", "MEDIUM")
                
                structure_item = {
                    "type": "listItem",
                    "title": f"{entity_type}: {entity_name}",
                    "description": opportunity_text,
                    "subtitle": f"Campaign: {campaign_name} | Impact: {impact}",
                    "content": action
                }
                structure_items.append(structure_item)
            
            if structure_items:
                structure_component = {
                    "type": "list",
                    "title": "Account Structure Opportunities",
                    "description": "Suggestions for restructuring your account for better performance",
                    "items": structure_items
                }
                visualizations.append(structure_component)
        
        # Add other category-specific visualizations as needed
    
    return {
        "type": "artifact",
        "format": "json",
        "content": visualizations
    }

def format_insights_visualization(
    anomalies_data: Optional[Dict[str, Any]] = None,
    suggestions_data: Optional[Dict[str, Any]] = None,
    opportunities_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format combined insights data for visualization.
    
    Args:
        anomalies_data: Optional dictionary containing detected anomalies
        suggestions_data: Optional dictionary containing optimization suggestions
        opportunities_data: Optional dictionary containing identified opportunities
        
    Returns:
        Dictionary with formatted visualization data for combined insights
    """
    # Create visualization components
    visualizations = []
    
    # 1. Summary card
    total_anomalies = len(anomalies_data.get("anomalies", [])) if anomalies_data else 0
    total_suggestions = suggestions_data.get("metadata", {}).get("total_suggestions", 0) if suggestions_data else 0
    total_opportunities = opportunities_data.get("metadata", {}).get("total_opportunities", 0) if opportunities_data else 0
    
    summary_card = {
        "type": "card",
        "title": "Account Insights Summary",
        "content": [
            {
                "type": "keyValue",
                "key": "Performance Anomalies",
                "value": str(total_anomalies)
            },
            {
                "type": "keyValue",
                "key": "Optimization Suggestions",
                "value": str(total_suggestions)
            },
            {
                "type": "keyValue",
                "key": "Growth Opportunities",
                "value": str(total_opportunities)
            }
        ]
    }
    visualizations.append(summary_card)
    
    # 2. Tabs for different insight types
    tabs = []
    
    # Anomalies tab
    if anomalies_data and anomalies_data.get("anomalies"):
        anomalies_viz = format_anomalies_visualization(anomalies_data)
        if anomalies_viz.get("type") == "artifact":
            anomalies_tab = {
                "title": "Performance Anomalies",
                "content": anomalies_viz.get("content", [])
            }
            tabs.append(anomalies_tab)
    
    # Suggestions tab
    if suggestions_data and suggestions_data.get("metadata", {}).get("total_suggestions", 0) > 0:
        suggestions_viz = format_optimization_suggestions_visualization(suggestions_data)
        if suggestions_viz.get("type") == "artifact":
            suggestions_tab = {
                "title": "Optimization Suggestions",
                "content": suggestions_viz.get("content", [])
            }
            tabs.append(suggestions_tab)
    
    # Opportunities tab
    if opportunities_data and opportunities_data.get("metadata", {}).get("total_opportunities", 0) > 0:
        opportunities_viz = format_opportunities_visualization(opportunities_data)
        if opportunities_viz.get("type") == "artifact":
            opportunities_tab = {
                "title": "Growth Opportunities",
                "content": opportunities_viz.get("content", [])
            }
            tabs.append(opportunities_tab)
    
    # Add tabs component if there are any tabs
    if tabs:
        tabs_component = {
            "type": "tabs",
            "tabs": tabs
        }
        visualizations.append(tabs_component)
    
    return {
        "type": "artifact",
        "format": "json",
        "content": visualizations
    } 