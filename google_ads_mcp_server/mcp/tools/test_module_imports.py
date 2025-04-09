"""
Test script for verifying module imports.

This script simply tests that all modules can be imported without errors.
"""

import importlib
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_module_imports():
    """Test that all modules can be imported without errors."""
    # List of modules to test
    modules = [
        "google_ads_mcp_server.mcp.tools.health",
        "google_ads_mcp_server.mcp.tools.budget",
        "google_ads_mcp_server.mcp.tools.campaign",
        "google_ads_mcp_server.mcp.tools.ad_group",
        "google_ads_mcp_server.mcp.tools.keyword",
        "google_ads_mcp_server.mcp.tools.search_term",
        "google_ads_mcp_server.mcp.tools.dashboard",
        "google_ads_mcp_server.mcp.tools.insights"
    ]
    
    success = True
    
    # Try to import each module
    for module_name in modules:
        try:
            # Import the module
            module = importlib.import_module(module_name)
            logger.info(f"✅ Successfully imported {module_name}")
            
            # Verify the register_X_tools function exists
            tool_registrar_name = f"register_{module_name.split('.')[-1]}_tools"
            if hasattr(module, tool_registrar_name):
                logger.info(f"✅ Found {tool_registrar_name} function in {module_name}")
            else:
                logger.error(f"❌ Could not find {tool_registrar_name} function in {module_name}")
                success = False
                
        except ImportError as e:
            logger.error(f"❌ Failed to import {module_name}: {str(e)}")
            success = False
    
    return success

if __name__ == "__main__":
    import sys
    import os
    
    # Add parent directory to Python path for imports
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Run the test
    success = test_module_imports()
    
    if success:
        logger.info("✅ All modules imported successfully")
        exit(0)
    else:
        logger.error("❌ Some modules failed to import or were missing expected functions")
        exit(1) 