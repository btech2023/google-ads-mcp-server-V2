"""
Unit tests for the validation utility module.
"""

import unittest
from datetime import datetime

from google_ads_mcp_server.utils.validation import (
    validate_customer_id,
    validate_date_format,
    validate_date_range,
    validate_enum,
    validate_numeric_range,
    validate_string_length,
    validate_regex,
    validate_all,
    validate_any,
    sanitize_input,
    validate_list,
    validate_dict,
    validate_non_empty_string,
    validate_list_not_empty,
    validate_list_of_strings,
    validate_list_of_dicts,
    validate_dict_keys,
    validate_non_negative_number
)

class TestValidationUtils(unittest.TestCase):
    """Test cases for validation utility functions."""

    def test_validate_customer_id(self):
        """Test customer ID validation."""
        # Test with valid input
        self.assertTrue(validate_customer_id("1234567890"))
        self.assertTrue(validate_customer_id("123-456-7890"))
        
        # Test with invalid input
        self.assertFalse(validate_customer_id(""))
        self.assertFalse(validate_customer_id(None))
        self.assertFalse(validate_customer_id("12345"))
        self.assertFalse(validate_customer_id("12345678901"))
        self.assertFalse(validate_customer_id("abcdefghij"))
    
    def test_validate_date_format(self):
        """Test date format validation."""
        # Test with valid input
        self.assertTrue(validate_date_format("2023-04-15"))
        
        # Test with invalid input
        self.assertFalse(validate_date_format(""))
        self.assertFalse(validate_date_format(None))
        self.assertFalse(validate_date_format("04/15/2023"))
        self.assertFalse(validate_date_format("2023-04-32"))  # Invalid day
        self.assertFalse(validate_date_format("2023-13-15"))  # Invalid month
    
    def test_validate_date_range(self):
        """Test date range validation."""
        # Test with valid input
        self.assertTrue(validate_date_range("2023-01-01", "2023-01-31"))
        self.assertTrue(validate_date_range("2023-01-01", "2023-01-01"))  # Same day
        
        # Test with invalid input
        self.assertFalse(validate_date_range("2023-01-31", "2023-01-01"))  # Start after end
        self.assertFalse(validate_date_range("2023-01-01", "invalid"))  # Invalid end date
        self.assertFalse(validate_date_range("invalid", "2023-01-01"))  # Invalid start date
        self.assertFalse(validate_date_range("", ""))  # Empty dates
    
    def test_validate_enum(self):
        """Test enum validation."""
        # Test with valid input
        self.assertTrue(validate_enum("apple", ["apple", "banana", "cherry"]))
        self.assertTrue(validate_enum("APPLE", ["apple", "banana", "cherry"], case_sensitive=False))
        
        # Test with invalid input
        self.assertFalse(validate_enum("orange", ["apple", "banana", "cherry"]))
        self.assertFalse(validate_enum("APPLE", ["apple", "banana", "cherry"], case_sensitive=True))
        self.assertFalse(validate_enum(None, ["apple", "banana", "cherry"]))
    
    def test_validate_numeric_range(self):
        """Test numeric range validation."""
        # Test with valid input
        self.assertTrue(validate_numeric_range(5, 1, 10))
        self.assertTrue(validate_numeric_range(1, 1, 10))  # Minimum
        self.assertTrue(validate_numeric_range(10, 1, 10))  # Maximum
        self.assertTrue(validate_numeric_range(5, min_value=1))  # Only min specified
        self.assertTrue(validate_numeric_range(5, max_value=10))  # Only max specified
        
        # Test with invalid input
        self.assertFalse(validate_numeric_range(0, 1, 10))  # Below min
        self.assertFalse(validate_numeric_range(11, 1, 10))  # Above max
        self.assertFalse(validate_numeric_range(None, 1, 10))  # None value
    
    def test_validate_string_length(self):
        """Test string length validation."""
        # Test with valid input
        self.assertTrue(validate_string_length("test", 1, 10))
        self.assertTrue(validate_string_length("t", 1, 10))  # Minimum length
        self.assertTrue(validate_string_length("testtest", 1, 10))  # Near maximum
        
        # Test with invalid input
        self.assertFalse(validate_string_length("", 1, 10))  # Empty string
        self.assertFalse(validate_string_length("testtesttest", 1, 10))  # Too long
        self.assertFalse(validate_string_length(None, 1, 10))  # None value
    
    def test_validate_regex(self):
        """Test regex validation."""
        # Test with valid input
        self.assertTrue(validate_regex("abc123", r"^[a-z]+[0-9]+$"))
        
        # Test with invalid input
        self.assertFalse(validate_regex("123abc", r"^[a-z]+[0-9]+$"))
        self.assertFalse(validate_regex("", r"^[a-z]+[0-9]+$"))
        self.assertFalse(validate_regex(None, r"^[a-z]+[0-9]+$"))
    
    def test_validate_all(self):
        """Test validate_all function."""
        # Create test validation tuples
        validations = [
            (validate_string_length, ["test"], {"min_length": 1, "max_length": 10}),
            (validate_regex, ["test"], {"pattern": r"^[a-z]+$"})
        ]
        
        # Test with all valid validations
        self.assertTrue(validate_all(validations))
        
        # Test with one invalid validation
        invalid_validations = [
            (validate_string_length, ["test"], {"min_length": 1, "max_length": 10}),
            (validate_regex, ["test123"], {"pattern": r"^[a-z]+$"})  # This will fail
        ]
        self.assertFalse(validate_all(invalid_validations))
    
    def test_validate_any(self):
        """Test validate_any function."""
        # Create test validation tuples
        validations = [
            (validate_string_length, ["test"], {"min_length": 1, "max_length": 10}),
            (validate_regex, ["test123"], {"pattern": r"^[a-z]+$"})  # This will fail
        ]
        
        # Test with at least one valid validation
        self.assertTrue(validate_any(validations))
        
        # Test with all invalid validations
        invalid_validations = [
            (validate_string_length, [""], {"min_length": 1, "max_length": 10}),  # This will fail
            (validate_regex, ["test123"], {"pattern": r"^[a-z]+$"})  # This will fail
        ]
        self.assertFalse(validate_any(invalid_validations))
    
    def test_sanitize_input(self):
        """Test input sanitization."""
        # Test with length limits
        self.assertEqual(sanitize_input("This is a long text", 10), "This is a ")
        
        # Test with allowed characters
        self.assertEqual(sanitize_input("abc123!@#", allowed_chars="abc123"), "abc123")
        
        # Test with both length and allowed characters
        self.assertEqual(sanitize_input("abc123!@#", max_length=4, allowed_chars="abc123"), "abc1")
        
        # Test with None input
        self.assertEqual(sanitize_input(None), "")
    
    def test_validate_list(self):
        """Test list validation with error collection."""
        # Initialize errors list
        errors = []
        
        # Test with valid input
        self.assertTrue(validate_list([1, 2, 3], "test_list", errors))
        self.assertEqual(len(errors), 0)
        
        # Test with None input
        errors = []
        self.assertFalse(validate_list(None, "test_list", errors))
        self.assertEqual(len(errors), 1)
        
        # Test with non-list input
        errors = []
        self.assertFalse(validate_list("not a list", "test_list", errors))
        self.assertEqual(len(errors), 1)
        
        # Test with empty list (not allowed by default)
        errors = []
        self.assertFalse(validate_list([], "test_list", errors))
        self.assertEqual(len(errors), 1)
        
        # Test with empty list (allowed)
        errors = []
        self.assertTrue(validate_list([], "test_list", errors, allow_empty=True))
        self.assertEqual(len(errors), 0)
    
    def test_validate_dict(self):
        """Test dictionary validation with error collection."""
        # Initialize errors list
        errors = []
        
        # Test with valid input
        self.assertTrue(validate_dict({"key": "value"}, "test_dict", errors))
        self.assertEqual(len(errors), 0)
        
        # Test with None input
        errors = []
        self.assertFalse(validate_dict(None, "test_dict", errors))
        self.assertEqual(len(errors), 1)
        
        # Test with non-dict input
        errors = []
        self.assertFalse(validate_dict("not a dict", "test_dict", errors))
        self.assertEqual(len(errors), 1)
        
        # Test with empty dict (not allowed by default)
        errors = []
        self.assertFalse(validate_dict({}, "test_dict", errors))
        self.assertEqual(len(errors), 1)
        
        # Test with empty dict (allowed)
        errors = []
        self.assertTrue(validate_dict({}, "test_dict", errors, allow_empty=True))
        self.assertEqual(len(errors), 0)
    
    def test_validate_non_empty_string(self):
        """Test non-empty string validation with error collection."""
        # Initialize errors list
        errors = []
        
        # Test with valid input
        self.assertTrue(validate_non_empty_string("test", "test_string", errors))
        self.assertEqual(len(errors), 0)
        
        # Test with None input
        errors = []
        self.assertFalse(validate_non_empty_string(None, "test_string", errors))
        self.assertEqual(len(errors), 1)
        
        # Test with empty string
        errors = []
        self.assertFalse(validate_non_empty_string("", "test_string", errors))
        self.assertEqual(len(errors), 1)
        
        # Test with non-string input
        errors = []
        self.assertFalse(validate_non_empty_string(123, "test_string", errors))
        self.assertEqual(len(errors), 1)
    
    def test_validate_list_not_empty(self):
        """Test non-empty list validation."""
        # Test with valid input
        self.assertTrue(validate_list_not_empty([1, 2, 3]))
        
        # Test with None input
        self.assertFalse(validate_list_not_empty(None))
        
        # Test with empty list
        self.assertFalse(validate_list_not_empty([]))
        
        # Test with non-list input
        self.assertFalse(validate_list_not_empty("not a list"))
    
    def test_validate_list_of_strings(self):
        """Test list of strings validation."""
        # Test with valid input
        self.assertTrue(validate_list_of_strings(["a", "b", "c"]))
        
        # Test with None input
        self.assertFalse(validate_list_of_strings(None))
        
        # Test with empty list (not allowed by default)
        self.assertFalse(validate_list_of_strings([]))
        
        # Test with empty list (allowed)
        self.assertTrue(validate_list_of_strings([], allow_empty=True))
        
        # Test with mixed types
        self.assertFalse(validate_list_of_strings(["a", 1, "c"]))
        
        # Test with non-list input
        self.assertFalse(validate_list_of_strings("not a list"))
    
    def test_validate_list_of_dicts(self):
        """Test list of dictionaries validation."""
        # Test with valid input
        self.assertTrue(validate_list_of_dicts([{"a": 1}, {"b": 2}]))
        
        # Test with None input
        self.assertFalse(validate_list_of_dicts(None))
        
        # Test with empty list (not allowed by default)
        self.assertFalse(validate_list_of_dicts([]))
        
        # Test with empty list (allowed)
        self.assertTrue(validate_list_of_dicts([], allow_empty=True))
        
        # Test with mixed types
        self.assertFalse(validate_list_of_dicts([{"a": 1}, "not a dict"]))
        
        # Test with non-list input
        self.assertFalse(validate_list_of_dicts("not a list"))
        
        # Test with required keys
        self.assertTrue(validate_list_of_dicts([{"id": 1, "name": "test"}], required_keys=["id"]))
        self.assertFalse(validate_list_of_dicts([{"name": "test"}], required_keys=["id"]))
    
    def test_validate_dict_keys(self):
        """Test dictionary keys validation."""
        # Test with valid input
        self.assertTrue(validate_dict_keys({"a": 1, "b": 2}, required_keys=["a", "b"]))
        self.assertTrue(validate_dict_keys({"a": 1, "b": 2, "c": 3}, required_keys=["a", "b"]))
        
        # Test with None input
        self.assertFalse(validate_dict_keys(None, required_keys=["a", "b"]))
        
        # Test with non-dict input
        self.assertFalse(validate_dict_keys("not a dict", required_keys=["a", "b"]))
        
        # Test with missing keys
        self.assertFalse(validate_dict_keys({"a": 1}, required_keys=["a", "b"]))
        
        # Test with empty dict and required keys
        self.assertFalse(validate_dict_keys({}, required_keys=["a", "b"]))
        
        # Test with empty required keys
        self.assertTrue(validate_dict_keys({"a": 1}, required_keys=[]))
    
    def test_validate_non_negative_number(self):
        """Test non-negative number validation with error collection."""
        # Initialize errors list
        errors = []
        
        # Test with valid input
        self.assertTrue(validate_non_negative_number(0, "test_number", errors))
        self.assertEqual(len(errors), 0)
        self.assertTrue(validate_non_negative_number(10, "test_number", errors))
        self.assertEqual(len(errors), 0)
        
        # Test with negative number
        errors = []
        self.assertFalse(validate_non_negative_number(-1, "test_number", errors))
        self.assertEqual(len(errors), 1)
        
        # Test with None input
        errors = []
        self.assertFalse(validate_non_negative_number(None, "test_number", errors))
        self.assertEqual(len(errors), 1)
        
        # Test with non-numeric input
        errors = []
        self.assertFalse(validate_non_negative_number("not a number", "test_number", errors))
        self.assertEqual(len(errors), 1)

if __name__ == "__main__":
    unittest.main() 