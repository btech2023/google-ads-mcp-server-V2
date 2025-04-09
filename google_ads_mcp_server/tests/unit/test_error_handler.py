"""
Unit tests for the error handler utility module.
"""

import unittest
from unittest.mock import patch, MagicMock

from google_ads_mcp_server.utils.error_handler import (
    ErrorDetails,
    handle_exception,
    classify_exception,
    handle_google_ads_exception,
    create_error_response,
    handle_and_respond,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    SEVERITY_ERROR,
    SEVERITY_CRITICAL,
    CATEGORY_VALIDATION,
    CATEGORY_AUTHENTICATION,
    CATEGORY_AUTHORIZATION,
    CATEGORY_API_ERROR,
    CATEGORY_DATABASE,
    CATEGORY_SERVER,
    CATEGORY_NETWORK
)

class TestErrorHandlerUtils(unittest.TestCase):
    """Test cases for error handler utility functions."""

    def test_error_details_init(self):
        """Test ErrorDetails initialization."""
        # Test basic initialization
        error = ErrorDetails("Test error message")
        self.assertEqual(error.message, "Test error message")
        self.assertEqual(error.severity, SEVERITY_ERROR)  # Default severity
        self.assertEqual(error.category, CATEGORY_SERVER)  # Default category
        
        # Test with exception
        exception = ValueError("Invalid value")
        error = ErrorDetails("Custom message", exception=exception)
        self.assertEqual(error.message, "Custom message")
        self.assertEqual(error.error_type, "ValueError")
        self.assertTrue(error.traceback is not None)
        
        # Test with custom severity and category
        error = ErrorDetails(
            "Auth error",
            severity=SEVERITY_CRITICAL,
            category=CATEGORY_AUTHENTICATION
        )
        self.assertEqual(error.severity, SEVERITY_CRITICAL)
        self.assertEqual(error.category, CATEGORY_AUTHENTICATION)
    
    def test_error_details_to_dict(self):
        """Test ErrorDetails to_dict method."""
        error = ErrorDetails(
            "Test error",
            error_type="TestError",
            severity=SEVERITY_WARNING,
            category=CATEGORY_VALIDATION,
            context={"param": "value"}
        )
        
        # Test without traceback
        error_dict = error.to_dict(include_traceback=False)
        self.assertEqual(error_dict["message"], "Test error")
        self.assertEqual(error_dict["error_type"], "TestError")
        self.assertEqual(error_dict["severity"], SEVERITY_WARNING)
        self.assertEqual(error_dict["category"], CATEGORY_VALIDATION)
        self.assertEqual(error_dict["context"], {"param": "value"})
        self.assertNotIn("traceback", error_dict)
        
        # Test with traceback
        error.traceback = "Fake traceback"
        error_dict = error.to_dict(include_traceback=True)
        self.assertEqual(error_dict["traceback"], "Fake traceback")
    
    @patch("google_ads_mcp_server.utils.error_handler.logger")
    def test_error_details_log(self, mock_logger):
        """Test ErrorDetails log method."""
        # Test error level
        error = ErrorDetails("Error message", severity=SEVERITY_ERROR)
        error.log()
        mock_logger.error.assert_called_once()
        
        # Test warning level
        mock_logger.reset_mock()
        error = ErrorDetails("Warning message", severity=SEVERITY_WARNING)
        error.log()
        mock_logger.warning.assert_called_once()
        
        # Test critical level
        mock_logger.reset_mock()
        error = ErrorDetails("Critical message", severity=SEVERITY_CRITICAL)
        error.log()
        mock_logger.critical.assert_called_once()
        
        # Test info level
        mock_logger.reset_mock()
        error = ErrorDetails("Info message", severity=SEVERITY_INFO)
        error.log()
        mock_logger.info.assert_called_once()
    
    @patch("google_ads_mcp_server.utils.error_handler.classify_exception")
    def test_handle_exception(self, mock_classify):
        """Test handle_exception function."""
        mock_error_details = MagicMock()
        mock_classify.return_value = mock_error_details
        
        exception = ValueError("Test error")
        context = {"test_param": "test_value"}
        
        # Test with defaults
        result = handle_exception(exception, context)
        mock_classify.assert_called_once_with(exception, context)
        mock_error_details.log.assert_called_once()
        self.assertEqual(result, mock_error_details)
        
        # Test with severity and category overrides
        mock_classify.reset_mock()
        mock_error_details.reset_mock()
        result = handle_exception(
            exception,
            context,
            severity=SEVERITY_CRITICAL,
            category=CATEGORY_AUTHENTICATION
        )
        self.assertEqual(mock_error_details.severity, SEVERITY_CRITICAL)
        self.assertEqual(mock_error_details.category, CATEGORY_AUTHENTICATION)
    
    def test_classify_exception(self):
        """Test classify_exception function."""
        # Test ValueError
        error_details = classify_exception(ValueError("Invalid value"))
        self.assertEqual(error_details.category, CATEGORY_VALIDATION)
        self.assertEqual(error_details.severity, SEVERITY_WARNING)
        
        # Test PermissionError
        error_details = classify_exception(PermissionError("Permission denied"))
        self.assertEqual(error_details.category, CATEGORY_SERVER)
        self.assertEqual(error_details.severity, SEVERITY_ERROR)
        
        # Test generic exception
        error_details = classify_exception(Exception("Generic error"))
        self.assertEqual(error_details.category, CATEGORY_SERVER)
        self.assertEqual(error_details.severity, SEVERITY_ERROR)
    
    def test_create_error_response(self):
        """Test create_error_response function."""
        error_details = ErrorDetails(
            "Test error",
            error_type="TestError",
            severity=SEVERITY_ERROR,
            category=CATEGORY_API_ERROR
        )
        
        # Test without traceback
        response = create_error_response(error_details, include_traceback=False)
        self.assertEqual(response["type"], "error")
        self.assertEqual(response["error"]["message"], "Test error")
        self.assertEqual(response["error"]["error_type"], "TestError")
        self.assertNotIn("traceback", response["error"])
        
        # Test with traceback
        error_details.traceback = "Fake traceback"
        response = create_error_response(error_details, include_traceback=True)
        self.assertEqual(response["error"]["traceback"], "Fake traceback")
    
    @patch("google_ads_mcp_server.utils.error_handler.handle_exception")
    def test_handle_and_respond(self, mock_handle_exception):
        """Test handle_and_respond function."""
        # Setup mock
        mock_error_details = MagicMock()
        mock_handle_exception.return_value = mock_error_details
        
        # Test successful execution
        def success_func(a, b):
            return a + b
        
        success, result = handle_and_respond(success_func, 1, 2)
        self.assertTrue(success)
        self.assertEqual(result, 3)
        mock_handle_exception.assert_not_called()
        
        # Test failed execution
        def failed_func():
            raise ValueError("Test error")
        
        mock_error_response = {"type": "error", "error": {"message": "Test error"}}
        mock_handle_exception.return_value = mock_error_details
        mock_error_details.to_dict.return_value = {"message": "Test error"}
        
        success, result = handle_and_respond(failed_func)
        self.assertFalse(success)
        self.assertEqual(result["type"], "error")
        mock_handle_exception.assert_called_once()

if __name__ == "__main__":
    unittest.main() 