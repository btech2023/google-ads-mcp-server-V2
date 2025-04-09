"""
Unit tests for the formatting utility module.
"""

import unittest
from datetime import datetime, timedelta

from google_ads_mcp_server.utils.formatting import (
    format_customer_id,
    clean_customer_id,
    micros_to_currency,
    currency_to_micros,
    format_percentage,
    format_date,
    get_date_range,
    format_number,
    truncate_string
)

class TestFormattingUtils(unittest.TestCase):
    """Test cases for formatting utility functions."""

    def test_format_customer_id(self):
        """Test customer ID formatting."""
        # Test with valid input
        self.assertEqual(format_customer_id("1234567890"), "123-456-7890")
        
        # Test with already formatted input
        self.assertEqual(format_customer_id("123-456-7890"), "123-456-7890")
        
        # Test with invalid input
        self.assertEqual(format_customer_id("123"), "123")  # Returns original if invalid
        self.assertEqual(format_customer_id("12345678901"), "12345678901")  # Too long
        self.assertEqual(format_customer_id("abcdefghij"), "abcdefghij")  # Not digits
    
    def test_clean_customer_id(self):
        """Test removing dashes from customer ID."""
        self.assertEqual(clean_customer_id("123-456-7890"), "1234567890")
        self.assertEqual(clean_customer_id("1234567890"), "1234567890")
    
    def test_micros_to_currency(self):
        """Test conversion from micros to currency string."""
        # Test with positive values
        self.assertEqual(micros_to_currency(1000000), "$1.00")
        self.assertEqual(micros_to_currency(1234567), "$1.23")
        self.assertEqual(micros_to_currency(1234567, "€"), "€1.23")
        self.assertEqual(micros_to_currency(1234567, "$", 3), "$1.235")
        
        # Test with zero
        self.assertEqual(micros_to_currency(0), "$0.00")
        
        # Test with None
        self.assertEqual(micros_to_currency(None), "$0.00")
        
        # Test with large values (thousands separator)
        self.assertEqual(micros_to_currency(1234567890), "$1,234.57")
    
    def test_currency_to_micros(self):
        """Test conversion from currency to micros."""
        # Test with numeric values
        self.assertEqual(currency_to_micros(1.23), 1230000)
        
        # Test with string values
        self.assertEqual(currency_to_micros("1.23"), 1230000)
        self.assertEqual(currency_to_micros("$1.23"), 1230000)
        self.assertEqual(currency_to_micros("€1.23"), 1230000)
        
        # Test with formatted values
        self.assertEqual(currency_to_micros("$1,234.56"), 1234560000)
    
    def test_format_percentage(self):
        """Test percentage formatting."""
        # Test with decimal values
        self.assertEqual(format_percentage(0.1234), "12.34%")
        self.assertEqual(format_percentage(0.1), "10.00%")
        
        # Test with zero
        self.assertEqual(format_percentage(0), "0.00%")
        
        # Test with None
        self.assertEqual(format_percentage(None), "0.00%")
        
        # Test with custom decimal places
        self.assertEqual(format_percentage(0.12345, 3), "12.345%")
    
    def test_format_date(self):
        """Test date formatting."""
        # Test with datetime object
        test_date = datetime(2023, 4, 15)
        self.assertEqual(format_date(test_date), "2023-04-15")
        self.assertEqual(format_date(test_date, "%m/%d/%Y"), "04/15/2023")
        
        # Test with date string
        self.assertEqual(format_date("2023-04-15"), "2023-04-15")
        
        # Test with different format strings
        self.assertEqual(format_date("04/15/2023"), "2023-04-15")
        self.assertEqual(format_date("15/04/2023"), "2023-04-15")
        
        # Test with default (current date)
        # This test may fail if run exactly at midnight when the date changes
        today = datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(format_date(), today)
    
    def test_get_date_range(self):
        """Test date range generation."""
        today = datetime.now()
        
        # Test LAST_7_DAYS
        start, end = get_date_range("LAST_7_DAYS")
        expected_start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        expected_end = today.strftime("%Y-%m-%d")
        self.assertEqual(start, expected_start)
        self.assertEqual(end, expected_end)
        
        # Test LAST_30_DAYS
        start, end = get_date_range("LAST_30_DAYS")
        expected_start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        self.assertEqual(start, expected_start)
        self.assertEqual(end, expected_end)
        
        # Test THIS_MONTH
        start, end = get_date_range("THIS_MONTH")
        expected_start = datetime(today.year, today.month, 1).strftime("%Y-%m-%d")
        self.assertEqual(start, expected_start)
        self.assertEqual(end, expected_end)
        
        # Test unknown range (defaults to LAST_30_DAYS)
        start, end = get_date_range("UNKNOWN_RANGE")
        expected_start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        self.assertEqual(start, expected_start)
        self.assertEqual(end, expected_end)
    
    def test_format_number(self):
        """Test number formatting."""
        # Test with integers
        self.assertEqual(format_number(1234), "1,234")
        self.assertEqual(format_number(0), "0")
        
        # Test with None
        self.assertEqual(format_number(None), "0")
        
        # Test with decimal places
        self.assertEqual(format_number(1234.5678, 2), "1,234.57")
    
    def test_truncate_string(self):
        """Test string truncation."""
        # Test with short string (no truncation)
        self.assertEqual(truncate_string("Short text", 20), "Short text")
        
        # Test with long string (truncation)
        self.assertEqual(truncate_string("This is a long text that should be truncated", 20), "This is a long te...")
        
        # Test with custom suffix
        self.assertEqual(truncate_string("This is a long text", 10, "...more"), "This is...more")
        
        # Test with empty string
        self.assertEqual(truncate_string("", 10), "")
        
        # Test with None
        self.assertEqual(truncate_string(None, 10), None)

if __name__ == "__main__":
    unittest.main() 