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

# Import utility modules
from ..utils.logging import get_logger
from ..utils.validation import (
    validate_customer_id,
    validate_date_format,
    validate_date_range,
    validate_dict_keys
)
from ..utils.error_handler import (
    handle_exception,
    create_error_response,
    ErrorDetails,
    CATEGORY_BUSINESS_LOGIC,
    CATEGORY_VALIDATION,
    SEVERITY_ERROR,
    SEVERITY_WARNING
)
from ..utils.formatting import format_customer_id, clean_customer_id

# Initialize logger
logger = get_logger(__name__)

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
    context = {
        "account_id": account_summary.get("customer_id", "Unknown"),
        "campaign_count": len(campaign_data) if campaign_data else 0,
        "method": "format_account_dashboard_data"
    }
    
    try:
        # Validate inputs
        validation_errors = []
        
        if not isinstance(account_summary, dict):
            validation_errors.append("account_summary must be a dictionary")
        
        if campaign_data is not None and not isinstance(campaign_data, list):
            validation_errors.append("campaign_data must be a list or None")
            
        if date_range is not None:
            if not isinstance(date_range, dict):
                validation_errors.append("date_range must be a dictionary if provided")
            elif not validate_dict_keys(date_range, required_keys=["start_date", "end_date"]):
                validation_errors.append("date_range must contain 'start_date' and 'end_date' keys")
            elif not validate_date_format(date_range.get("start_date", "")):
                validation_errors.append(f"Invalid start_date format in date_range: {date_range.get('start_date', '')}")
            elif not validate_date_format(date_range.get("end_date", "")):
                validation_errors.append(f"Invalid end_date format in date_range: {date_range.get('end_date', '')}")
            elif not validate_date_range(date_range.get("start_date", ""), date_range.get("end_date", "")):
                validation_errors.append(f"Invalid date range: {date_range.get('start_date', '')} to {date_range.get('end_date', '')}")
                
        # If validation errors found, raise ValueError
        if validation_errors:
            raise ValueError("; ".join(validation_errors))
        
        customer_id = account_summary.get('customer_id', 'Unknown')
        # If valid customer_id, format it for display
        if validate_customer_id(customer_id):
            formatted_customer_id = format_customer_id(clean_customer_id(customer_id))
            context["account_id"] = formatted_customer_id
            logger.info(f"Formatting account dashboard data for customer {formatted_customer_id}")
        else:
            logger.info("Formatting account dashboard data for unknown customer")
        
        # Use provided date range or extract from account summary
        effective_date_range = date_range
        if not effective_date_range and 'date_range' in account_summary:
            effective_date_range = account_summary['date_range']
        
        # Default date range if still not available
        if not effective_date_range:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            effective_date_range = {
                'start_date': start_date,
                'end_date': end_date
            }
            
        context["date_range"] = effective_date_range
        
        # Basic account metrics from summary - use safe access with defaults
        dashboard_data = {
            'customer_id': customer_id,
            'date_range': effective_date_range,
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
            try:
                # Calculate campaign statistics for visualization
                campaign_stats = _calculate_campaign_statistics(campaign_data)
                dashboard_data['campaign_performance'] = {
                    'data': _format_campaigns_for_visualization(campaign_data),
                    'statistics': campaign_stats
                }
            except Exception as e:
                # Handle errors in campaign data processing without failing the entire operation
                error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
                logger.warning(f"Error processing campaign data for dashboard: {error_details.message}")
                dashboard_data['campaign_performance'] = {
                    'data': [],
                    'statistics': {
                        'total_campaigns': len(campaign_data),
                        'active_campaigns': 0,
                        'paused_campaigns': 0,
                        'removed_campaigns': 0,
                        'error': error_details.message
                    }
                }
        
        logger.info(f"Dashboard data formatting complete, {len(campaign_data) if campaign_data else 0} campaigns included")
        return dashboard_data
        
    except ValueError as ve:
        error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
        logger.warning(f"Validation error formatting dashboard data: {error_details.message}")
        raise ve
    except Exception as e:
        error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
        logger.error(f"Error formatting dashboard data: {error_details.message}")
        # Return a basic response instead of failing completely
        return {
            'customer_id': context.get("account_id", "Unknown"),
            'error': error_details.message,
            'date_range': date_range or {'start_date': '', 'end_date': ''},
            'metrics_summary': {
                'impressions': 0,
                'clicks': 0,
                'cost': 0,
                'conversions': 0,
                'conversion_value': 0,
                'ctr': 0,
                'cpc': 0,
                'conversion_rate': 0,
                'cost_per_conversion': 0
            }
        }

def _calculate_campaign_statistics(campaign_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics about campaigns for the dashboard.
    
    Args:
        campaign_data: List of campaign performance data
    
    Returns:
        Dictionary of campaign statistics
    """
    context = {"method": "_calculate_campaign_statistics", "campaign_count": len(campaign_data) if campaign_data else 0}
    
    try:
        # Validate input
        if not isinstance(campaign_data, list):
            raise ValueError("campaign_data must be a list")
            
        if not campaign_data:
            return {
                'total_campaigns': 0,
                'active_campaigns': 0,
                'paused_campaigns': 0,
                'removed_campaigns': 0
            }
        
        # Count campaign statuses - safely access status with .get() and default
        active_count = sum(1 for c in campaign_data if c.get('status') == 'ENABLED')
        paused_count = sum(1 for c in campaign_data if c.get('status') == 'PAUSED')
        removed_count = sum(1 for c in campaign_data if c.get('status') == 'REMOVED')
        
        # Calculate performance distributions using numpy - with defensive programming
        try:
            # Use .get() with default 0 for safe access
            impressions = np.array([c.get('impressions', 0) for c in campaign_data])
            clicks = np.array([c.get('clicks', 0) for c in campaign_data])
            costs = np.array([c.get('cost', 0) for c in campaign_data])
            
            # Handle empty arrays or NaN values
            if len(impressions) == 0 or np.isnan(impressions).any():
                impression_percentiles = {'min': 0, 'p25': 0, 'median': 0, 'p75': 0, 'max': 0}
            else:
                impression_percentiles = {
                    'min': float(np.min(impressions)),
                    'p25': float(np.percentile(impressions, 25)),
                    'median': float(np.median(impressions)),
                    'p75': float(np.percentile(impressions, 75)),
                    'max': float(np.max(impressions))
                }
            
            if len(costs) == 0 or np.isnan(costs).any():
                cost_percentiles = {'min': 0, 'p25': 0, 'median': 0, 'p75': 0, 'max': 0}
            else:
                cost_percentiles = {
                    'min': float(np.min(costs)),
                    'p25': float(np.percentile(costs, 25)),
                    'median': float(np.median(costs)),
                    'p75': float(np.percentile(costs, 75)),
                    'max': float(np.max(costs))
                }
        except Exception as np_error:
            # Handle numpy calculation errors gracefully
            logger.warning(f"Error calculating statistics distributions: {str(np_error)}")
            impression_percentiles = {'min': 0, 'p25': 0, 'median': 0, 'p75': 0, 'max': 0, 'error': str(np_error)}
            cost_percentiles = {'min': 0, 'p25': 0, 'median': 0, 'p75': 0, 'max': 0, 'error': str(np_error)}
        
        return {
            'total_campaigns': len(campaign_data),
            'active_campaigns': active_count,
            'paused_campaigns': paused_count,
            'removed_campaigns': removed_count,
            'impression_distribution': impression_percentiles,
            'cost_distribution': cost_percentiles
        }
        
    except ValueError as ve:
        error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
        logger.warning(f"Validation error calculating campaign statistics: {error_details.message}")
        raise ve
    except Exception as e:
        error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
        logger.error(f"Error calculating campaign statistics: {error_details.message}")
        # Return default values on error
        return {
            'total_campaigns': len(campaign_data) if isinstance(campaign_data, list) else 0,
            'active_campaigns': 0,
            'paused_campaigns': 0,
            'removed_campaigns': 0,
            'error': error_details.message
        }

def _format_campaigns_for_visualization(campaign_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format campaign data specifically for dashboard visualization.
    
    Args:
        campaign_data: List of campaign performance data
    
    Returns:
        Formatted campaign data ready for visualization
    """
    context = {"method": "_format_campaigns_for_visualization", "campaign_count": len(campaign_data) if campaign_data else 0}
    
    try:
        # Validate input
        if not isinstance(campaign_data, list):
            raise ValueError("campaign_data must be a list")
            
        formatted_campaigns = []
        
        for index, campaign in enumerate(campaign_data):
            try:
                # Calculate derived metrics - with safe access using .get() with defaults
                impressions = campaign.get('impressions', 0)
                clicks = campaign.get('clicks', 0)
                cost = campaign.get('cost', 0)
                conversions = campaign.get('conversions', 0)
                
                # Calculate derived metrics with division by zero protection
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
            except Exception as campaign_error:
                # Skip problematic campaigns rather than failing the entire operation
                error_details = handle_exception(campaign_error, context={**context, "campaign_index": index}, category=CATEGORY_BUSINESS_LOGIC)
                logger.warning(f"Error formatting campaign at index {index}: {error_details.message}")
                continue
        
        # Sort by impressions (descending)
        formatted_campaigns.sort(key=lambda x: x['metrics']['impressions'], reverse=True)
        
        return formatted_campaigns
        
    except ValueError as ve:
        error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
        logger.warning(f"Validation error formatting campaigns: {error_details.message}")
        raise ve
    except Exception as e:
        error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
        logger.error(f"Error formatting campaigns: {error_details.message}")
        return [] # Return empty list on error 