"""
Dashboard utility functions for Google Ads MCP Server.

This module provides utility functions for formatting account data for dashboard
visualization, supporting the dashboards.py module.
"""

import logging
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

def format_account_dashboard_data(
    account_summary: Dict[str, Any],
    campaign_data: List[Dict[str, Any]],
    date_range: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Format account data for dashboard visualization.
    
    Args:
        account_summary: Account summary metrics
        campaign_data: List of campaign performance data
        date_range: Optional date range dictionary with 'start_date' and 'end_date'
                   If not provided, uses the date range from account_summary
    
    Returns:
        Formatted dashboard data ready for visualization
    """
    logger.info("Formatting account dashboard data")
    
    # Use provided date range or extract from account summary
    if not date_range and 'date_range' in account_summary:
        date_range = account_summary['date_range']
    
    # Default date range if still not available
    if not date_range:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        date_range = {
            'start_date': start_date,
            'end_date': end_date
        }
    
    # Basic account metrics from summary
    dashboard_data = {
        'customer_id': account_summary.get('customer_id', 'Unknown'),
        'date_range': date_range,
        'metrics_summary': {
            'impressions': account_summary.get('total_impressions', 0),
            'clicks': account_summary.get('total_clicks', 0),
            'cost': account_summary.get('total_cost', 0),
            'conversions': account_summary.get('total_conversions', 0),
            'conversion_value': account_summary.get('total_conversion_value', 0),
            'ctr': account_summary.get('ctr', 0),
            'cpc': account_summary.get('cpc', 0),
            'conversion_rate': account_summary.get('conversion_rate', 0),
            'cost_per_conversion': account_summary.get('cost_per_conversion', 0)
        }
    }
    
    # Format campaign data for visualization
    if campaign_data:
        # Calculate campaign statistics for visualization
        campaign_stats = _calculate_campaign_statistics(campaign_data)
        dashboard_data['campaign_performance'] = {
            'data': _format_campaigns_for_visualization(campaign_data),
            'statistics': campaign_stats
        }
    
    logger.info(f"Dashboard data formatting complete, {len(campaign_data) if campaign_data else 0} campaigns included")
    return dashboard_data

def _calculate_campaign_statistics(campaign_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics about campaigns for the dashboard.
    
    Args:
        campaign_data: List of campaign performance data
    
    Returns:
        Dictionary of campaign statistics
    """
    if not campaign_data:
        return {
            'total_campaigns': 0,
            'active_campaigns': 0,
            'paused_campaigns': 0,
            'removed_campaigns': 0
        }
    
    # Count campaign statuses
    active_count = sum(1 for c in campaign_data if c.get('status') == 'ENABLED')
    paused_count = sum(1 for c in campaign_data if c.get('status') == 'PAUSED')
    removed_count = sum(1 for c in campaign_data if c.get('status') == 'REMOVED')
    
    # Calculate performance distributions using numpy
    if len(campaign_data) > 0:
        impressions = np.array([c.get('impressions', 0) for c in campaign_data])
        clicks = np.array([c.get('clicks', 0) for c in campaign_data])
        costs = np.array([c.get('cost', 0) for c in campaign_data])
        
        # Calculate performance percentiles
        impression_percentiles = {
            'min': float(np.min(impressions)),
            'p25': float(np.percentile(impressions, 25)),
            'median': float(np.median(impressions)),
            'p75': float(np.percentile(impressions, 75)),
            'max': float(np.max(impressions))
        }
        
        cost_percentiles = {
            'min': float(np.min(costs)),
            'p25': float(np.percentile(costs, 25)),
            'median': float(np.median(costs)),
            'p75': float(np.percentile(costs, 75)),
            'max': float(np.max(costs))
        }
    else:
        # Default values if no campaign data
        impression_percentiles = {'min': 0, 'p25': 0, 'median': 0, 'p75': 0, 'max': 0}
        cost_percentiles = {'min': 0, 'p25': 0, 'median': 0, 'p75': 0, 'max': 0}
    
    return {
        'total_campaigns': len(campaign_data),
        'active_campaigns': active_count,
        'paused_campaigns': paused_count,
        'removed_campaigns': removed_count,
        'impression_distribution': impression_percentiles,
        'cost_distribution': cost_percentiles
    }

def _format_campaigns_for_visualization(campaign_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format campaign data specifically for dashboard visualization.
    
    Args:
        campaign_data: List of campaign performance data
    
    Returns:
        Formatted campaign data ready for visualization
    """
    formatted_campaigns = []
    
    for campaign in campaign_data:
        # Calculate derived metrics
        impressions = campaign.get('impressions', 0)
        clicks = campaign.get('clicks', 0)
        cost = campaign.get('cost', 0)
        conversions = campaign.get('conversions', 0)
        
        # Avoid division by zero
        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        avg_cpc = cost / clicks if clicks > 0 else 0
        conv_rate = (conversions / clicks * 100) if clicks > 0 else 0
        cost_per_conv = cost / conversions if conversions > 0 else 0
        
        formatted_campaign = {
            'id': campaign.get('id', ''),
            'name': campaign.get('name', ''),
            'status': campaign.get('status', ''),
            'channel_type': campaign.get('channel_type', ''),
            'metrics': {
                'impressions': impressions,
                'clicks': clicks,
                'cost': cost,
                'conversions': conversions,
                'ctr': ctr,
                'avg_cpc': avg_cpc,
                'conversion_rate': conv_rate,
                'cost_per_conversion': cost_per_conv
            }
        }
        
        formatted_campaigns.append(formatted_campaign)
    
    # Sort by impressions (descending)
    formatted_campaigns.sort(key=lambda x: x['metrics']['impressions'], reverse=True)
    
    return formatted_campaigns 