"""
Test script for verifying insights tools registration.

This script mocks the necessary services and verifies that the insights tools are registered correctly.
"""

import logging
import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockMCP:
    """Mock MCP class for testing tool registration."""
    
    def __init__(self):
        """Initialize the mock MCP instance."""
        self.registered_tools = {}
        
    def tool(self):
        """Mock tool decorator that registers the function."""
        def decorator(func):
            self.registered_tools[func.__name__] = func
            return func
        return decorator

async def test_insights_tools_registration():
    """Test that insights tools register correctly."""
    # Create mock MCP instance
    mcp = MockMCP()
    
    # Create mock GoogleAdsService
    google_ads_service = MagicMock()
    
    # Create mock InsightsService with required methods
    insights_service = MagicMock()
    insights_service.detect_performance_anomalies = AsyncMock()
    insights_service.generate_optimization_suggestions = AsyncMock()
    insights_service.discover_opportunities = AsyncMock()
    
    # Import the register_insights_tools function
    # Use absolute import to avoid circular import issues
    import google_ads_mcp_server.mcp.tools.insights as insights_module
    
    # Register the insights tools
    insights_module.register_insights_tools(mcp, google_ads_service, insights_service)
    
    # Expected insights tools
    expected_tools = [
        "get_performance_anomalies",
        "get_performance_anomalies_json",
        "get_optimization_suggestions",
        "get_optimization_suggestions_json",
        "get_opportunities",
        "get_opportunities_json",
        "get_account_insights_json"
    ]
    
    # Verify that all expected tools were registered
    for tool_name in expected_tools:
        if tool_name in mcp.registered_tools:
            logger.info(f"✅ Tool {tool_name} registered correctly")
        else:
            logger.error(f"❌ Tool {tool_name} not registered!")
    
    # Summary
    registered_count = sum(1 for tool in expected_tools if tool in mcp.registered_tools)
    logger.info(f"Registered {registered_count} out of {len(expected_tools)} expected tools")
    
    return registered_count == len(expected_tools)

if __name__ == "__main__":
    # Add parent directory to Python path for imports
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
        
    # Run the test
    success = asyncio.run(test_insights_tools_registration())
    
    if success:
        logger.info("✅ All insights tools registered correctly")
        exit(0)
    else:
        logger.error("❌ Some insights tools were not registered correctly")
        exit(1) 