"""
Search Term Visualization Module

This module provides formatting functions for visualizing search term data.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def format_search_term_table(search_terms_data: List[Dict[str, Any]], 
                            title: str = "Search Term Performance") -> Dict[str, Any]:
    """
    Format search term data for table visualization.
    
    Args:
        search_terms_data: List of search term dictionaries from SearchTermService.get_search_terms
        title: Title for the visualization
        
    Returns:
        Dictionary formatted for Claude Artifacts table visualization
    """
    if not search_terms_data:
        return {
            "chart_type": "table",
            "title": title,
            "columns": [],
            "data": []
        }
    
    logger.info(f"Formatting {len(search_terms_data)} search terms for table visualization")
    
    # Define columns for the table visualization
    columns = [
        {"key": "search_term", "name": "Search Term", "type": "string"},
        {"key": "ad_group_name", "name": "Ad Group", "type": "string"},
        {"key": "campaign_name", "name": "Campaign", "type": "string"},
        {"key": "impressions", "name": "Impressions", "type": "number", "format": "comma"},
        {"key": "clicks", "name": "Clicks", "type": "number", "format": "comma"},
        {"key": "cost", "name": "Cost", "type": "number", "format": "currency"},
        {"key": "ctr", "name": "CTR", "type": "number", "format": "percent"},
        {"key": "conversions", "name": "Conversions", "type": "number", "format": "decimal"},
        {"key": "conversion_value", "name": "Conv. Value", "type": "number", "format": "currency"},
        {"key": "cpc", "name": "CPC", "type": "number", "format": "currency"},
        {"key": "cost_per_conversion", "name": "Cost/Conv.", "type": "number", "format": "currency"},
        {"key": "roas", "name": "ROAS", "type": "number", "format": "decimal"}
    ]
    
    # Format the data for visualization
    formatted_data = []
    for term in search_terms_data:
        formatted_term = {
            "search_term": term.get("search_term", ""),
            "ad_group_name": term.get("ad_group_name", ""),
            "campaign_name": term.get("campaign_name", ""),
            "impressions": term.get("impressions", 0),
            "clicks": term.get("clicks", 0),
            "cost": term.get("cost", 0),
            "ctr": term.get("ctr", 0),
            "conversions": term.get("conversions", 0),
            "conversion_value": term.get("conversion_value", 0),
            "cpc": term.get("cpc", 0),
            "cost_per_conversion": term.get("cost_per_conversion", 0),
            "roas": term.get("roas", 0)
        }
        formatted_data.append(formatted_term)
    
    # Sort data by cost (descending) by default
    formatted_data = sorted(formatted_data, key=lambda x: x.get("cost", 0), reverse=True)
    
    return {
        "chart_type": "table",
        "title": title,
        "columns": columns,
        "data": formatted_data
    }

def format_search_term_word_cloud(search_terms_data: List[Dict[str, Any]], 
                                 weight_metric: str = "cost",
                                 title: str = None,
                                 min_frequency: int = 1) -> Dict[str, Any]:
    """
    Format search term data for word cloud visualization.
    
    Args:
        search_terms_data: List of search term dictionaries from SearchTermService.get_search_terms
        weight_metric: Metric to use for word size (cost, clicks, impressions, etc.)
        title: Title for the visualization (defaults to "Search Term Cloud by [Metric]")
        min_frequency: Minimum value of the weight metric to include in the cloud
        
    Returns:
        Dictionary formatted for Claude Artifacts word cloud visualization
    """
    if not search_terms_data:
        return {
            "chart_type": "word_cloud",
            "title": title or f"Search Term Cloud by {weight_metric.capitalize()}",
            "data": []
        }
    
    # Set default title if not provided
    if not title:
        title = f"Search Term Cloud by {weight_metric.capitalize()}"
    
    logger.info(f"Formatting {len(search_terms_data)} search terms for word cloud visualization")
    
    # Aggregate search terms by weight metric
    term_weights = {}
    for term in search_terms_data:
        search_term = term.get("search_term", "")
        weight = term.get(weight_metric, 0)
        
        if search_term in term_weights:
            term_weights[search_term] += weight
        else:
            term_weights[search_term] = weight
    
    # Filter out terms below the minimum frequency
    term_weights = {k: v for k, v in term_weights.items() if v >= min_frequency}
    
    # Format the data for visualization
    word_cloud_data = [
        {"text": term, "value": weight}
        for term, weight in term_weights.items()
    ]
    
    # Sort by weight (descending)
    word_cloud_data = sorted(word_cloud_data, key=lambda x: x["value"], reverse=True)
    
    # Limit to top 100 terms to avoid overwhelming visualization
    word_cloud_data = word_cloud_data[:100]
    
    return {
        "chart_type": "word_cloud",
        "title": title,
        "data": word_cloud_data
    }

def format_search_term_analysis(analysis: Dict[str, Any],
                              title: str = "Search Term Analysis") -> Dict[str, Any]:
    """
    Format search term analysis for visualization.
    
    Args:
        analysis: Dictionary from SearchTermService.analyze_search_terms
        title: Title for the visualization
        
    Returns:
        Dictionary formatted for Claude Artifacts visualization
    """
    if not analysis or analysis.get("total_search_terms", 0) == 0:
        return {
            "chart_type": "composite",
            "title": title,
            "components": []
        }
    
    logger.info("Formatting search term analysis for visualization")
    
    # Format summary metrics
    summary_data = {
        "chart_type": "metrics",
        "title": "Summary Metrics",
        "metrics": [
            {"name": "Total Search Terms", "value": analysis.get("total_search_terms", 0), "format": "number"},
            {"name": "Total Impressions", "value": analysis.get("total_impressions", 0), "format": "comma"},
            {"name": "Total Clicks", "value": analysis.get("total_clicks", 0), "format": "comma"},
            {"name": "Total Cost", "value": analysis.get("total_cost", 0), "format": "currency"},
            {"name": "Total Conversions", "value": analysis.get("total_conversions", 0), "format": "decimal"},
            {"name": "Average CTR", "value": analysis.get("average_ctr", 0), "format": "percent"},
            {"name": "Average CPC", "value": analysis.get("average_cpc", 0), "format": "currency"},
            {"name": "Average Conv. Rate", "value": analysis.get("average_conversion_rate", 0), "format": "percent"}
        ]
    }
    
    # Format top performing terms table
    top_terms_columns = [
        {"key": "search_term", "name": "Search Term", "type": "string"},
        {"key": "conversions", "name": "Conversions", "type": "number", "format": "decimal"},
        {"key": "ctr", "name": "CTR", "type": "number", "format": "percent"},
        {"key": "cost", "name": "Cost", "type": "number", "format": "currency"}
    ]
    
    top_terms_data = [
        {
            "search_term": term.get("search_term", ""),
            "conversions": term.get("conversions", 0),
            "ctr": term.get("ctr", 0),
            "cost": term.get("cost", 0)
        }
        for term in analysis.get("top_performing_terms", [])
    ]
    
    top_terms_table = {
        "chart_type": "table",
        "title": "Top Performing Search Terms",
        "columns": top_terms_columns,
        "data": top_terms_data
    }
    
    # Format low performing terms table
    low_terms_columns = [
        {"key": "search_term", "name": "Search Term", "type": "string"},
        {"key": "cost", "name": "Cost", "type": "number", "format": "currency"},
        {"key": "clicks", "name": "Clicks", "type": "number", "format": "comma"},
        {"key": "conversions", "name": "Conversions", "type": "number", "format": "decimal"}
    ]
    
    low_terms_data = [
        {
            "search_term": term.get("search_term", ""),
            "cost": term.get("cost", 0),
            "clicks": term.get("clicks", 0),
            "conversions": term.get("conversions", 0)
        }
        for term in analysis.get("low_performing_terms", [])
    ]
    
    low_terms_table = {
        "chart_type": "table",
        "title": "Low Performing Search Terms",
        "columns": low_terms_columns,
        "data": low_terms_data
    }
    
    # Format potential negative keywords table
    negative_columns = [
        {"key": "search_term", "name": "Search Term", "type": "string"},
        {"key": "impressions", "name": "Impressions", "type": "number", "format": "comma"},
        {"key": "clicks", "name": "Clicks", "type": "number", "format": "comma"},
        {"key": "ctr", "name": "CTR", "type": "number", "format": "percent"},
        {"key": "conversions", "name": "Conversions", "type": "number", "format": "decimal"}
    ]
    
    negative_data = [
        {
            "search_term": term.get("search_term", ""),
            "impressions": term.get("impressions", 0),
            "clicks": term.get("clicks", 0),
            "ctr": term.get("ctr", 0),
            "conversions": term.get("conversions", 0)
        }
        for term in analysis.get("potential_negative_keywords", [])
    ]
    
    negative_table = {
        "chart_type": "table",
        "title": "Potential Negative Keywords",
        "columns": negative_columns,
        "data": negative_data
    }
    
    # Combine all components
    return {
        "chart_type": "composite",
        "title": title,
        "components": [
            summary_data,
            top_terms_table,
            low_terms_table,
            negative_table
        ]
    } 