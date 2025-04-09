"""
Formatting Utility Module

This module provides helper functions for formatting data in the Google Ads MCP Server,
including date formatting, currency conversion, and general data transformations.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple

logger = logging.getLogger(__name__)

def format_customer_id(customer_id: str) -> str:
    """
    Format a Google Ads customer ID with dashes for display.
    
    Args:
        customer_id: Raw customer ID (with or without dashes)
        
    Returns:
        Formatted customer ID (XXX-XXX-XXXX)
    """
    # Remove any existing dashes
    clean_id = customer_id.replace("-", "")
    
    # Validate that the ID is 10 digits
    if not clean_id.isdigit() or len(clean_id) != 10:
        logger.warning(f"Invalid customer ID format: {customer_id}")
        return customer_id  # Return original if invalid
    
    # Format with dashes
    return f"{clean_id[:3]}-{clean_id[3:6]}-{clean_id[6:]}"

def clean_customer_id(customer_id: str) -> str:
    """
    Remove dashes from a Google Ads customer ID.
    
    Args:
        customer_id: Customer ID potentially containing dashes
        
    Returns:
        Clean customer ID without dashes
    """
    return customer_id.replace("-", "")

def micros_to_currency(micros: Union[int, float], currency_symbol: str = "$", decimal_places: int = 2) -> str:
    """
    Convert micros (millionths) to a formatted currency string.
    
    Args:
        micros: The amount in micros (1/1,000,000 of the currency unit)
        currency_symbol: The currency symbol to prepend (default: $)
        decimal_places: Number of decimal places to display (default: 2)
        
    Returns:
        Formatted currency string (e.g., "$123.45")
    """
    if micros is None:
        return f"{currency_symbol}0.00"
    
    dollars = micros / 1_000_000
    return f"{currency_symbol}{dollars:,.{decimal_places}f}"

def currency_to_micros(amount: Union[str, float]) -> int:
    """
    Convert a currency amount to micros.
    
    Args:
        amount: String with currency symbol or float
        
    Returns:
        Amount in micros (integer)
    """
    if isinstance(amount, str):
        # Remove currency symbol and commas
        clean_amount = re.sub(r'[^\d.]', '', amount)
        amount = float(clean_amount)
    
    # Convert to micros (round to prevent floating point errors)
    return round(amount * 1_000_000)

def format_percentage(value: Union[float, int], decimal_places: int = 2) -> str:
    """
    Format a value as a percentage string.
    
    Args:
        value: The value to format (0.01 = 1%)
        decimal_places: Number of decimal places to display
        
    Returns:
        Formatted percentage string (e.g., "12.34%")
    """
    if value is None:
        return "0.00%"
    
    # Convert to percentage
    percentage = value * 100
    return f"{percentage:.{decimal_places}f}%"

def format_date(date_obj: Optional[Union[datetime, str]] = None, format_str: str = "%Y-%m-%d") -> str:
    """
    Format a date object or string consistently.
    
    Args:
        date_obj: Date object or string to format (defaults to today)
        format_str: Format string (default: YYYY-MM-DD)
        
    Returns:
        Formatted date string
    """
    if date_obj is None:
        # Default to today
        date_obj = datetime.now()
    
    if isinstance(date_obj, str):
        # Parse string to datetime if needed
        try:
            # Try common formats
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
                try:
                    date_obj = datetime.strptime(date_obj, fmt)
                    break
                except ValueError:
                    continue
            else:
                logger.warning(f"Could not parse date string: {date_obj}")
                return date_obj  # Return original if parsing fails
        except Exception as e:
            logger.error(f"Error parsing date string: {e}")
            return date_obj  # Return original if parsing fails
    
    # Format the datetime object
    return date_obj.strftime(format_str)

def get_date_range(date_range_str: str) -> Tuple[str, str]:
    """
    Convert a date range string to start and end dates.
    
    Args:
        date_range_str: String like "LAST_30_DAYS", "LAST_7_DAYS", "THIS_MONTH"
        
    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    today = datetime.now()
    end_date = today.strftime("%Y-%m-%d")
    
    if date_range_str == "LAST_7_DAYS":
        start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    elif date_range_str == "LAST_14_DAYS":
        start_date = (today - timedelta(days=14)).strftime("%Y-%m-%d")
    elif date_range_str == "LAST_30_DAYS":
        start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    elif date_range_str == "LAST_90_DAYS":
        start_date = (today - timedelta(days=90)).strftime("%Y-%m-%d")
    elif date_range_str == "THIS_MONTH":
        start_date = datetime(today.year, today.month, 1).strftime("%Y-%m-%d")
    elif date_range_str == "LAST_MONTH":
        last_month = today.month - 1 if today.month > 1 else 12
        last_month_year = today.year if today.month > 1 else today.year - 1
        start_date = datetime(last_month_year, last_month, 1).strftime("%Y-%m-%d")
        # Last day of last month
        if last_month == 12:
            end_date = datetime(last_month_year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(last_month_year, last_month + 1, 1) - timedelta(days=1)
        end_date = end_date.strftime("%Y-%m-%d")
    else:
        # Default to last 30 days
        logger.warning(f"Unknown date range string: {date_range_str}, defaulting to LAST_30_DAYS")
        start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    
    return start_date, end_date

def format_number(value: Union[int, float], decimal_places: int = 0) -> str:
    """
    Format a number with thousand separators.
    
    Args:
        value: The number to format
        decimal_places: Number of decimal places to display
        
    Returns:
        Formatted number string (e.g., "1,234" or "1,234.56")
    """
    if value is None:
        return "0"
    
    format_str = f"{{:,.{decimal_places}f}}"
    return format_str.format(value)

def truncate_string(text: str, max_length: int = 30, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length and add a suffix if truncated.
    
    Args:
        text: The string to truncate
        max_length: Maximum length of the result string (including suffix)
        suffix: String to append if truncated
        
    Returns:
        Truncated string
    """
    if not text or len(text) <= max_length:
        return text
    
    # Calculate truncation point
    truncate_at = max_length - len(suffix)
    return text[:truncate_at] + suffix
