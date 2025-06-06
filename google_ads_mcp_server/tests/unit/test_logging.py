"""
Unit tests for the logging utility module.
"""

import unittest
import logging
import os
import json
import tempfile
import sys
import io
from unittest.mock import patch, MagicMock

from google_ads_mcp_server.utils.logging import (
    JsonFormatter,
    RequestContextFilter,
    configure_logging,
    get_logger,
    add_request_context,
    log_api_call,
    log_mcp_request
)

# Mock for server.set_request_context if direct import is problematic
_mock_request_context = {}
async def mock_set_request_context(request_id):
    class MockContextManager:
        async def __aenter__(self):
            _mock_request_context['id'] = request_id
        async def __aexit__(self, exc_type, exc, tb):
            _mock_request_context.pop('id', None)
    return MockContextManager()

def mock_get_current_request_id():
    return _mock_request_context.get('id')

class TestLoggingUtils(unittest.TestCase):
    """Test cases for logging utility functions."""

    def setUp(self):
        """Set up test environment."""
        # Clear all handlers to avoid interference between tests
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        root_logger.setLevel(logging.INFO)

        # Create a log stream to capture output for assertions
        self.log_stream = io.StringIO()
        stream_handler = logging.StreamHandler(self.log_stream)
        stream_handler.setFormatter(logging.Formatter(":%(request_id)s:%(message)s"))
        root_logger.addHandler(stream_handler)

        # Configure request context handling and test logger
        self.logger = logging.getLogger("test_logger")
        self.logger.addFilter(RequestContextFilter(mock_get_current_request_id))
    
    def test_json_formatter(self):
        """Test JsonFormatter."""
        formatter = JsonFormatter()
        
        # Create a log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test_file.py",
            lineno=123,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Format the record
        formatted = formatter.format(record)
        
        # Parse the JSON output
        json_output = json.loads(formatted)
        
        # Verify JSON structure
        self.assertEqual(json_output["level"], "INFO")
        self.assertEqual(json_output["name"], "test_logger")
        self.assertEqual(json_output["line"], 123)
        self.assertEqual(json_output["message"], "Test message")
        
        # Test with exception info
        try:
            raise ValueError("Test exception")
        except ValueError:
            record.exc_info = sys.exc_info()
            formatted = formatter.format(record)
            json_output = json.loads(formatted)
            
            # Verify exception info
            self.assertIn("exception", json_output)
            self.assertEqual(json_output["exception"]["type"], "ValueError")
            self.assertEqual(json_output["exception"]["message"], "Test exception")
    
    def test_request_context_filter(self):
        """Test RequestContextFilter."""
        # Create a mock request ID getter
        request_id_getter = lambda: "test-request-id"
        
        # Create the filter
        context_filter = RequestContextFilter(request_id_getter)
        
        # Create a log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test_file.py",
            lineno=123,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Apply the filter
        context_filter.filter(record)
        
        # Verify the request ID was added
        self.assertEqual(record.request_id, "test-request-id")
        
        # Test with None request ID
        none_request_id = RequestContextFilter(lambda: None)
        none_request_id.filter(record)
        self.assertIsNone(record.request_id)
    
    def test_configure_logging(self):
        """Test configure_logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            
            # Configure logging with file output
            logger = configure_logging(
                app_name="test_app",
                console_level=logging.WARNING,
                file_level=logging.DEBUG,
                log_file_path=log_file
            )
            
            # Verify logger
            self.assertEqual(logger.name, "test_app")
            
            # Verify log file was created
            self.assertTrue(os.path.exists(log_file))
            
            # Log some messages
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            
            # Verify log file contains the expected messages
            with open(log_file, 'r') as f:
                log_contents = f.read()
                
                # File level is DEBUG, so all messages should be logged to file
                self.assertIn("Debug message", log_contents)
                self.assertIn("Info message", log_contents)
                self.assertIn("Warning message", log_contents)
                self.assertIn("Error message", log_contents)
    
    def test_get_logger(self):
        """Test get_logger."""
        logger = get_logger("test_module")
        self.assertEqual(logger.name, "test_module")
        
        # Test that calling it again returns the same logger
        same_logger = get_logger("test_module")
        self.assertIs(logger, same_logger)
    
    @patch("google_ads_mcp_server.utils.logging.logging.getLogger")
    def test_add_request_context(self, mock_get_logger):
        """Test add_request_context."""
        mock_root_logger = MagicMock()
        mock_get_logger.return_value = mock_root_logger
        
        # Create a mock request ID getter
        request_id_getter = lambda: "test-request-id"
        
        # Add the request context
        add_request_context(request_id_getter)
        
        # Verify the filter was added to the root logger
        mock_root_logger.addFilter.assert_called_once()
        
        # Verify the filter is a RequestContextFilter
        filter_arg = mock_root_logger.addFilter.call_args[0][0]
        self.assertIsInstance(filter_arg, RequestContextFilter)
    
    @patch("google_ads_mcp_server.utils.logging.logging.getLogger")
    def test_log_api_call(self, mock_get_logger):
        """Test log_api_call."""
        mock_logger = MagicMock()
        
        # Test successful API call
        log_api_call(
            mock_logger,
            service="TestService",
            method="test_method",
            customer_id="123-456-7890",
            params={"param1": "value1"},
            duration_ms=100,
            success=True
        )
        
        # Verify logger.info was called
        mock_logger.info.assert_called_once()
        
        # Test failed API call
        mock_logger.reset_mock()
        log_api_call(
            mock_logger,
            service="TestService",
            method="test_method",
            customer_id="123-456-7890",
            params={"param1": "value1"},
            success=False
        )
        
        # Verify logger.error was called
        mock_logger.error.assert_called_once()
    
    @patch("google_ads_mcp_server.utils.logging.logging.getLogger")
    def test_log_mcp_request(self, mock_get_logger):
        """Test log_mcp_request."""
        mock_logger = MagicMock()
        
        # Test successful MCP request
        log_mcp_request(
            mock_logger,
            request_type="tool",
            request_id="req-123",
            params={"param1": "value1"},
            duration_ms=100,
            success=True
        )
        
        # Verify logger.info was called
        mock_logger.info.assert_called_once()
        
        # Test failed MCP request
        mock_logger.reset_mock()
        log_mcp_request(
            mock_logger,
            request_type="tool",
            request_id="req-123",
            params={"param1": "value1"},
            success=False
        )
        
        # Verify logger.error was called
        mock_logger.error.assert_called_once()

    def test_request_context_filter_integration(self):
        """Test RequestContextFilter adds context to logs."""
        test_id = "req-context-789"
        
        # Simulate setting the request context
        _mock_request_context['id'] = test_id
        
        self.logger.info("Message within context")
        
        # Simulate clearing the request context
        _mock_request_context.pop('id', None)
        
        self.logger.info("Message outside context")
        
        # Check the captured log output
        self.log_stream.seek(0)
        logs = self.log_stream.read().splitlines()
        
        # First log should have the request ID
        self.assertIn(f":{test_id}:Message within context", logs[0])
        
        # Second log should have None (or empty string depending on formatter)
        self.assertIn(f":None:Message outside context", logs[1])

    @patch("google_ads_mcp_server.utils.logging.logging.getLogger")
    def test_configure_logging_adds_filter(self, mock_get_logger):
        """Test that configure_logging adds the RequestContextFilter."""
        mock_root_logger = MagicMock()
        mock_get_logger.return_value = mock_root_logger
        
        # Configure logging
        configure_logging(app_name="test_config_app")
        
        # Verify a filter was added
        self.assertTrue(mock_root_logger.addFilter.called)
        
        # Verify the added filter is a RequestContextFilter
        added_filter = None
        for call in mock_root_logger.addFilter.call_args_list:
            filter_arg = call[0][0]
            if isinstance(filter_arg, RequestContextFilter):
                added_filter = filter_arg
                break
        self.assertIsInstance(added_filter, RequestContextFilter)

    @patch("google_ads_mcp_server.utils.logging.logging.getLogger")
    def test_log_api_call(self, mock_get_logger):
        """Test log_api_call."""
        mock_logger_instance = MagicMock()
        
        # Test successful API call
        log_api_call(
            mock_logger_instance,
            service="TestService",
            method="test_method",
            customer_id="123-456-7890",
            params={"param1": "value1"},
            duration_ms=100,
            success=True
        )
        
        # Verify logger.info was called with extra data
        mock_logger_instance.info.assert_called_once()
        call_args, call_kwargs = mock_logger_instance.info.call_args
        self.assertIn('extra', call_kwargs)
        self.assertIn('api_call', call_kwargs['extra'])
        self.assertEqual(call_kwargs['extra']['api_call']['service'], "TestService")
        
        # Test failed API call
        mock_logger_instance.reset_mock()
        log_api_call(
            mock_logger_instance,
            service="TestService",
            method="test_method",
            customer_id="123-456-7890",
            params={"param1": "value1"},
            success=False
        )
        
        # Verify logger.error was called with extra data
        mock_logger_instance.error.assert_called_once()
        call_args, call_kwargs = mock_logger_instance.error.call_args
        self.assertIn('extra', call_kwargs)
        self.assertIn('api_call', call_kwargs['extra'])

    @patch("google_ads_mcp_server.utils.logging.logging.getLogger")
    def test_log_mcp_request(self, mock_get_logger):
        """Test log_mcp_request."""
        mock_logger_instance = MagicMock()
        request_id = "mcp-req-111"
        params = {"tool_name": "get_campaigns"}
        
        # Test successful MCP request
        log_mcp_request(
            mock_logger_instance,
            request_type="tool",
            request_id=request_id,
            params=params,
            duration_ms=50.5,
            success=True,
            result_info={"count": 5}
        )
        
        # Verify logger.info was called with extra data
        mock_logger_instance.info.assert_called_once()
        call_args, call_kwargs = mock_logger_instance.info.call_args
        self.assertIn('extra', call_kwargs)
        self.assertIn('mcp_request', call_kwargs['extra'])
        self.assertEqual(call_kwargs['extra']['mcp_request']['request_id'], request_id)
        self.assertEqual(call_kwargs['extra']['mcp_request']['result_info'], {"count": 5})
        
        # Test failed MCP request
        mock_logger_instance.reset_mock()
        log_mcp_request(
            mock_logger_instance,
            request_type="resource",
            request_id=request_id,
            params=params,
            success=False,
            result_info={"error": "timeout"}
        )
        
        # Verify logger.error was called with extra data
        mock_logger_instance.error.assert_called_once()
        call_args, call_kwargs = mock_logger_instance.error.call_args
        self.assertIn('extra', call_kwargs)
        self.assertIn('mcp_request', call_kwargs['extra'])
        self.assertEqual(call_kwargs['extra']['mcp_request']['result_info'], {"error": "timeout"})

if __name__ == "__main__":
    unittest.main() 