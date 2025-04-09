#!/usr/bin/env python
"""
Run unit tests for all utility modules.
"""

import unittest
import sys
import os

# Add the parent directory to the path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the test modules
from google_ads_mcp_server.tests.unit.test_formatting import TestFormattingUtils
from google_ads_mcp_server.tests.unit.test_validation import TestValidationUtils
from google_ads_mcp_server.tests.unit.test_error_handler import TestErrorHandlerUtils
from google_ads_mcp_server.tests.unit.test_logging import TestLoggingUtils

def main():
    # Create a test suite with all test cases
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestFormattingUtils))
    test_suite.addTest(unittest.makeSuite(TestValidationUtils))
    test_suite.addTest(unittest.makeSuite(TestErrorHandlerUtils))
    test_suite.addTest(unittest.makeSuite(TestLoggingUtils))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main()) 