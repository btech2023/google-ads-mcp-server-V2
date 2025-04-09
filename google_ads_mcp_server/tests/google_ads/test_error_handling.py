"""
Test error handling in Google Ads service modules.

This module tests that the Google Ads service modules correctly handle validation errors
and properly use the error handling utilities, including verification of request context ID in logs.
"""

import unittest
import logging
import io
from unittest import mock

from google_ads_mcp_server.utils.error_handler import (
    ErrorDetails,
    SEVERITY_WARNING,
    SEVERITY_ERROR,
    CATEGORY_VALIDATION,
    CATEGORY_API_ERROR,
    CATEGORY_BUSINESS_LOGIC
)
from google_ads_mcp_server.utils.logging import RequestContextFilter
from google_ads_mcp_server.google_ads.insights import InsightsService
from google_ads_mcp_server.google_ads.keywords import KeywordService
from google_ads_mcp_server.google_ads.search_terms import SearchTermService

# Mock context mechanism
_mock_request_context = {}
def mock_get_current_request_id():
    return _mock_request_context.get('id')

class TestErrorHandling(unittest.TestCase):
    """Test case for error handling in Google Ads service modules."""
    
    def setUp(self):
        """Set up test case with mocked Google Ads client and log capture."""
        # Create a mock Google Ads client
        self.mock_client = mock.MagicMock()
        
        # Initialize services with the mock client
        self.insights_service = InsightsService(self.mock_client)
        self.keyword_service = KeywordService(self.mock_client)
        self.search_term_service = SearchTermService(self.mock_client)
        
        # Set up log capture
        self.log_stream = io.StringIO()
        self.log_handler = logging.StreamHandler(self.log_stream)
        self.formatter = logging.Formatter("%(levelname)s:%(name)s:%(request_id)s:%(message)s")
        self.log_handler.setFormatter(self.formatter)
        
        # Get the loggers used by the service modules
        self.service_loggers = [
            logging.getLogger("google_ads_mcp_server.google_ads.insights"),
            logging.getLogger("google_ads_mcp_server.google_ads.keywords"),
            logging.getLogger("google_ads_mcp_server.google_ads.search_terms")
        ]
        
        self.context_filter = RequestContextFilter(mock_get_current_request_id)
        
        for logger in self.service_loggers:
            logger.setLevel(logging.DEBUG)
            for handler in logger.handlers[:]: logger.removeHandler(handler)
            logger.addHandler(self.log_handler)
            logger.addFilter(self.context_filter)
    
    def tearDown(self):
        """Clean up after the test."""
        for logger in self.service_loggers:
            logger.removeFilter(self.context_filter)
            logger.removeHandler(self.log_handler)
        _mock_request_context.clear()

    def test_insights_service_validation_errors(self):
        """Test that the InsightsService correctly handles validation errors."""
        test_id = "req-ins-val-001"
        _mock_request_context['id'] = test_id
        
        # Test with invalid customer ID
        with self.assertRaises(ValueError) as context:
            self.insights_service.get_performance_metrics(
                customer_id="invalid",  # Invalid format
                start_date="2023-01-01",
                end_date="2023-01-31"
            )
        
        # Verify error message contains validation error
        self.assertIn("Invalid customer ID", str(context.exception))
        
        # Verify log contains the request ID
        self.log_stream.seek(0)
        logs = self.log_stream.read()
        self.assertIn(f":{test_id}:Validation error", logs)
        _mock_request_context.clear()
        self.log_stream.truncate(0); self.log_stream.seek(0)
        
        # Test with invalid date range
        _mock_request_context['id'] = test_id
        with self.assertRaises(ValueError) as context:
            self.insights_service.get_performance_metrics(
                customer_id="123-456-7890",
                start_date="2023-01-31",
                end_date="2023-01-01"  # End date before start date
            )
        
        # Verify error message contains validation error
        self.assertIn("End date must be after start date", str(context.exception))
        self.log_stream.seek(0)
        logs = self.log_stream.read()
        self.assertIn(f":{test_id}:Validation error", logs)
        _mock_request_context.clear()
        self.log_stream.truncate(0); self.log_stream.seek(0)
        
        # Test with empty metrics
        _mock_request_context['id'] = test_id
        with self.assertRaises(ValueError) as context:
            self.insights_service.get_performance_metrics(
                customer_id="123-456-7890",
                start_date="2023-01-01",
                end_date="2023-01-31",
                metrics=[]  # Empty list
            )
        
        # Verify error message contains validation error
        self.assertIn("metrics list cannot be empty", str(context.exception))
        self.log_stream.seek(0)
        logs = self.log_stream.read()
        self.assertIn(f":{test_id}:Validation error", logs)
        _mock_request_context.clear()
    
    @mock.patch("google_ads_mcp_server.google_ads.insights.handle_exception")
    def test_insights_service_api_errors(self, mock_handle_exception):
        """Test that the InsightsService properly uses error_handler for API errors."""
        test_id = "req-ins-api-002"
        _mock_request_context['id'] = test_id
        
        # Set up the mock to return an error details object
        mock_error_details = ErrorDetails(
            "API Error",
            error_type="GoogleAdsException",
            severity=SEVERITY_ERROR,
            category=CATEGORY_API_ERROR
        )
        mock_handle_exception.return_value = mock_error_details
        
        # Configure the mock client to raise a GoogleAdsException
        # Use a different method call for clarity
        self.mock_client.search.side_effect = Exception("GoogleAdsException")
        
        # Call the method that uses search
        with self.assertRaises(RuntimeError) as context:
            self.insights_service.get_performance_metrics(
                customer_id="123-456-7890",
                start_date="2023-01-01",
                end_date="2023-01-31"
            )
        
        # Verify that handle_exception was called
        mock_handle_exception.assert_called_once()
        
        # Verify error message format
        self.assertIn("Operation failed", str(context.exception))
        
        # Verify log contains the request ID (assuming handle_exception logs)
        # Note: This requires handle_exception itself to use the filtered logger
        # We might need to mock the logger used by handle_exception instead
        # For simplicity, we check if the exception handler was called. 
        # A more robust test would capture logs from error_handler's logger.
        _mock_request_context.clear()
    
    def test_keyword_service_validation_errors(self):
        """Test that the KeywordService correctly handles validation errors."""
        test_id = "req-kw-val-003"
        _mock_request_context['id'] = test_id
        
        # Test with invalid keyword text
        with self.assertRaises(ValueError) as context:
            self.keyword_service.create_keywords(
                customer_id="123-456-7890",
                ad_group_id="123456789",
                keywords=[
                    {
                        "text": "",  # Empty text
                        "match_type": "EXACT"
                    }
                ]
            )
        
        # Verify error message contains validation error
        self.assertIn("keyword text", str(context.exception).lower())
        self.log_stream.seek(0)
        logs = self.log_stream.read()
        self.assertIn(f":{test_id}:Validation error", logs)
        _mock_request_context.clear()
        self.log_stream.truncate(0); self.log_stream.seek(0)
        
        # Test with invalid match type
        _mock_request_context['id'] = test_id
        with self.assertRaises(ValueError) as context:
            self.keyword_service.create_keywords(
                customer_id="123-456-7890",
                ad_group_id="123456789",
                keywords=[
                    {
                        "text": "test keyword",
                        "match_type": "INVALID"  # Invalid match type
                    }
                ]
            )
        
        # Verify error message contains validation error
        self.assertIn("match_type", str(context.exception).lower())
        self.log_stream.seek(0)
        logs = self.log_stream.read()
        self.assertIn(f":{test_id}:Validation error", logs)
        _mock_request_context.clear()
    
    @mock.patch("google_ads_mcp_server.google_ads.search_terms.handle_google_ads_exception")
    def test_search_term_service_google_ads_exception(self, mock_handle_google_ads_exception):
        """Test that the SearchTermService correctly handles GoogleAdsException."""
        test_id = "req-st-api-004"
        _mock_request_context['id'] = test_id
        
        # Set up the mock to return an error details object
        mock_error_details = ErrorDetails(
            "Google Ads API Error",
            error_type="GoogleAdsException",
            severity=SEVERITY_ERROR,
            category=CATEGORY_API_ERROR
        )
        mock_handle_google_ads_exception.return_value = mock_error_details
        
        # Configure the mock client to raise a GoogleAdsException
        self.mock_client.search_stream.side_effect = Exception("GoogleAdsException")
        
        # Call the method
        with self.assertRaises(RuntimeError) as context:
            self.search_term_service.get_search_terms(
                customer_id="123-456-7890",
                start_date="2023-01-01",
                end_date="2023-01-31"
            )
        
        # Verify that handle_google_ads_exception was called
        mock_handle_google_ads_exception.assert_called_once()
        
        # Verify error message format
        self.assertIn("Operation failed", str(context.exception))
        _mock_request_context.clear()
    
    def test_grouped_validation_errors(self):
        """Test that services collect multiple validation errors before failing."""
        test_id = "req-grouped-val-005"
        _mock_request_context['id'] = test_id
        
        # Call a method with multiple validation errors
        with self.assertRaises(ValueError) as context:
            self.insights_service.get_performance_by_device(
                customer_id="invalid",  # Invalid customer ID
                start_date="invalid",   # Invalid date format
                end_date="invalid"      # Invalid date format
            )
        
        # Verify that the error message contains all validation errors
        error_message = str(context.exception)
        self.assertIn("Invalid customer ID", error_message)
        self.assertIn("Invalid date format", error_message)
        
        # Verify that multiple errors are joined
        self.assertIn(";", error_message)  # Multiple errors should be delimited
        
        # Verify log contains the request ID
        self.log_stream.seek(0)
        logs = self.log_stream.read()
        self.assertIn(f":{test_id}:Validation error", logs)
        _mock_request_context.clear()


if __name__ == "__main__":
    unittest.main() 