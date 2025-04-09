"""
Test error handling in MCP tools.

This module tests that MCP tools correctly handle validation errors and 
properly generate error responses using the error handling utilities,
including verification of request context ID in logs.
"""

import unittest
import logging
import io
from unittest import mock
import json

from google_ads_mcp_server.utils.error_handler import (
    ErrorDetails,
    SEVERITY_WARNING,
    SEVERITY_ERROR,
    CATEGORY_VALIDATION,
    CATEGORY_API_ERROR,
    CATEGORY_BUSINESS_LOGIC
)
from google_ads_mcp_server.utils.logging import RequestContextFilter, get_logger
from google_ads_mcp_server.mcp.tools.campaign import get_campaigns
from google_ads_mcp_server.mcp.tools.ad_group import get_ad_groups
from google_ads_mcp_server.mcp.tools.keyword import create_keywords
from google_ads_mcp_server.mcp.tools.insights import get_performance_insights

# Mock context mechanism
_mock_request_context = {}
def mock_get_current_request_id():
    return _mock_request_context.get('id')

class TestMCPToolErrorHandling(unittest.TestCase):
    """Test case for error handling in MCP tools."""
    
    def setUp(self):
        """Set up test case with mock context and log capture."""
        # Create a mock MCP context object
        self.mock_context = mock.MagicMock()
        self.mock_context.request_id = "test-request-id" # Set a default for context object itself
        
        # Set up the mock Google Ads service
        self.mock_google_ads_service = mock.MagicMock()
        
        # Patch the function that gets the Google Ads service from context
        # Note: Need to patch for each tool module tested if they import it separately
        self.campaign_patcher = mock.patch(
            'google_ads_mcp_server.mcp.tools.campaign.get_google_ads_service',
            return_value=self.mock_google_ads_service
        )
        self.ad_group_patcher = mock.patch(
            'google_ads_mcp_server.mcp.tools.ad_group.get_google_ads_service',
            return_value=self.mock_google_ads_service
        )
        self.keyword_patcher = mock.patch(
            'google_ads_mcp_server.mcp.tools.keyword.get_google_ads_service',
            return_value=self.mock_google_ads_service
        )
        self.insights_patcher = mock.patch(
            'google_ads_mcp_server.mcp.tools.insights.get_google_ads_service',
            return_value=self.mock_google_ads_service
        )
        self.campaign_patcher.start()
        self.ad_group_patcher.start()
        self.keyword_patcher.start()
        self.insights_patcher.start()
        
        # Set up log capture
        self.log_stream = io.StringIO()
        self.log_handler = logging.StreamHandler(self.log_stream)
        # Use a formatter that includes the request_id
        self.formatter = logging.Formatter("%(levelname)s:%(name)s:%(request_id)s:%(message)s")
        self.log_handler.setFormatter(self.formatter)
        
        # Get the loggers used by the tool modules and add the handler
        # Adjust logger names based on actual usage in tool modules
        self.tool_loggers = [
            logging.getLogger("google_ads_mcp_server.mcp.tools.campaign"),
            logging.getLogger("google_ads_mcp_server.mcp.tools.ad_group"),
            logging.getLogger("google_ads_mcp_server.mcp.tools.keyword"),
            logging.getLogger("google_ads_mcp_server.mcp.tools.insights")
        ]
        
        self.context_filter = RequestContextFilter(mock_get_current_request_id)
        
        for logger in self.tool_loggers:
            logger.setLevel(logging.DEBUG)
            # Clear existing handlers to avoid duplicates in test runs
            for handler in logger.handlers[:]: logger.removeHandler(handler)
            logger.addHandler(self.log_handler)
            # Ensure filter is applied
            logger.addFilter(self.context_filter)
    
    def tearDown(self):
        """Clean up after the test."""
        self.campaign_patcher.stop()
        self.ad_group_patcher.stop()
        self.keyword_patcher.stop()
        self.insights_patcher.stop()
        
        # Clean up logging handlers and filters
        for logger in self.tool_loggers:
            logger.removeFilter(self.context_filter)
            logger.removeHandler(self.log_handler)
        _mock_request_context.clear() # Clear mock context
    
    def test_campaign_tool_validation_error(self):
        """Test that the get_campaigns tool handles validation errors correctly."""
        test_id = "req-camp-val-123"
        _mock_request_context['id'] = test_id # Set mock request ID
        
        # Configure the service to raise a validation error
        self.mock_google_ads_service.get_campaigns.side_effect = ValueError(
            "Invalid customer ID format: invalid"
        )
        
        # Call the tool function with invalid data
        response = get_campaigns(params={"customer_id": "invalid"}, context=self.mock_context)
        
        # Verify tool returned an error response
        self.assertEqual(response["type"], "error")
        self.assertIn("Invalid customer ID", response["error"]["message"])
        self.assertEqual(response["error"]["category"], CATEGORY_VALIDATION)
        
        # Verify log contains the correct request ID
        self.log_stream.seek(0)
        logs = self.log_stream.read()
        self.assertIn(f":{test_id}:Validation error", logs)
        self.assertIn("Invalid customer ID format", logs)
        _mock_request_context.clear() # Clear mock context
    
    def test_ad_group_tool_api_error(self):
        """Test that the get_ad_groups tool handles API errors correctly."""
        test_id = "req-adg-api-456"
        _mock_request_context['id'] = test_id
        
        # Configure the service to raise a RuntimeError (simulating a wrapped API error)
        self.mock_google_ads_service.get_ad_groups.side_effect = RuntimeError(
            "Operation failed: API request error: Invalid authentication"
        )
        
        # Call the tool function
        response = get_ad_groups(
            params={"customer_id": "123-456-7890", "campaign_id": "123456789"},
            context=self.mock_context
        )
        
        # Verify tool returned an error response
        self.assertEqual(response["type"], "error")
        self.assertIn("API request error", response["error"]["message"])
        self.assertEqual(response["error"]["category"], CATEGORY_API_ERROR)
        
        # Verify log contains the correct request ID
        self.log_stream.seek(0)
        logs = self.log_stream.read()
        self.assertIn(f":{test_id}:Error executing get_ad_groups", logs)
        self.assertIn("API request error: Invalid authentication", logs)
        _mock_request_context.clear()
    
    def test_keyword_tool_validation_error_with_list(self):
        """Test that the create_keywords tool collects multiple validation errors."""
        test_id = "req-kw-val-789"
        _mock_request_context['id'] = test_id
        
        # Mock the keyword service to collect and raise validation errors
        self.mock_google_ads_service.create_keywords.side_effect = ValueError(
            "Invalid keyword text: empty text; Invalid match type: INVALID"
        )
        
        # Call the tool function with invalid data
        response = create_keywords(
            params={
                "customer_id": "123-456-7890",
                "ad_group_id": "123456789",
                "keywords": [
                    {"text": "", "match_type": "INVALID"}
                ]
            },
            context=self.mock_context
        )
        
        # Verify tool returned an error response with all validation errors
        self.assertEqual(response["type"], "error")
        self.assertIn("Invalid keyword text", response["error"]["message"])
        self.assertIn("Invalid match type", response["error"]["message"])
        self.assertEqual(response["error"]["category"], CATEGORY_VALIDATION)
        
        # Verify log contains the correct request ID
        self.log_stream.seek(0)
        logs = self.log_stream.read()
        self.assertIn(f":{test_id}:Validation error in create_keywords", logs)
        self.assertIn("Invalid keyword text", logs)
        self.assertIn("Invalid match type", logs)
        _mock_request_context.clear()
    
    def test_insights_tool_different_severity_levels(self):
        """Test that tools handle errors with different severity levels."""
        test_id_warn = "req-ins-warn-111"
        test_id_err = "req-ins-err-222"
        
        # Test with warning
        _mock_request_context['id'] = test_id_warn
        self.mock_google_ads_service.get_performance_insights.side_effect = ValueError(
            "No data available for the specified period"
        )
        
        response = get_performance_insights(
            params={"customer_id": "123-456-7890", "start_date": "2023-01-01", "end_date": "2023-01-31"},
            context=self.mock_context
        )
        
        # Warning errors should still return error responses
        self.assertEqual(response["type"], "error")
        self.assertIn("No data available", response["error"]["message"])
        self.assertEqual(response["error"]["severity"], SEVERITY_WARNING)
        
        # Verify warning log contains the correct request ID
        self.log_stream.seek(0)
        logs_warn = self.log_stream.read()
        self.assertIn(f":{test_id_warn}:Validation error in get_performance_insights", logs_warn)
        self.assertIn("No data available", logs_warn)
        _mock_request_context.clear()
        self.log_stream.truncate(0)
        self.log_stream.seek(0)
        
        # Test with error
        _mock_request_context['id'] = test_id_err
        self.mock_google_ads_service.get_performance_insights.side_effect = RuntimeError(
            "Operation failed: Database connection error"
        )
        
        response = get_performance_insights(
            params={"customer_id": "123-456-7890", "start_date": "2023-01-01", "end_date": "2023-01-31"},
            context=self.mock_context
        )
        
        # Critical errors should have appropriate severity
        self.assertEqual(response["type"], "error")
        self.assertIn("Database connection error", response["error"]["message"])
        self.assertEqual(response["error"]["severity"], SEVERITY_ERROR)
        
        # Verify error log contains the correct request ID
        self.log_stream.seek(0)
        logs_err = self.log_stream.read()
        self.assertIn(f":{test_id_err}:Error executing get_performance_insights", logs_err)
        self.assertIn("Database connection error", logs_err)
        _mock_request_context.clear()
    
    def test_error_response_structure(self):
        """Test that error responses have the correct structure."""
        test_id = "req-struct-333"
        _mock_request_context['id'] = test_id
        
        # Configure the service to raise an error
        self.mock_google_ads_service.get_campaigns.side_effect = ValueError("Test structure error")
        
        # Call the tool function
        response = get_campaigns(params={"customer_id": "invalid"}, context=self.mock_context)
        
        # Verify response structure
        self.assertIn("type", response)
        self.assertEqual(response["type"], "error")
        self.assertIn("error", response)
        self.assertIn("message", response["error"])
        self.assertIn("category", response["error"])
        self.assertIn("severity", response["error"])
        self.assertEqual(response["error"]["message"], "Test structure error")
        _mock_request_context.clear()
    
    def test_error_logging_includes_request_id(self):
        """Test that errors logged during tool execution include the request ID."""
        test_id = "req-log-444"
        _mock_request_context['id'] = test_id
        
        # Mock the logger within the specific tool module being tested
        # Using campaign module logger as an example
        with mock.patch('google_ads_mcp_server.mcp.tools.campaign.logger') as mock_tool_logger:
            # Configure the service to raise an error
            self.mock_google_ads_service.get_campaigns.side_effect = ValueError("Test logging error")
            
            # Call the tool function
            response = get_campaigns(params={"customer_id": "invalid"}, context=self.mock_context)
            
            # Verify that the error was logged via the mock
            # Note: This checks the direct call to the logger mock, not the captured stream
            mock_tool_logger.warning.assert_called_once()
            log_message = mock_tool_logger.warning.call_args[0][0]
            self.assertIn("Test logging error", log_message)
            
            # Verify captured log stream also contains the ID
            self.log_stream.seek(0)
            logs = self.log_stream.read()
            self.assertIn(f":{test_id}:Validation error", logs) # Check for request ID in stream
            self.assertIn("Test logging error", logs)
        _mock_request_context.clear()

if __name__ == "__main__":
    unittest.main() 