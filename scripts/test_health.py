#!/usr/bin/env python
"""
Test script for health check endpoints
"""

import os
import sys
import json
import asyncio
import httpx

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_http_health_endpoint():
    """Test the HTTP health endpoint."""
    print("\n=== Testing HTTP Health Endpoint ===")
    
    port = int(os.environ.get("PORT", "8000"))
    url = f"http://localhost:{port}/health"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            
        if response.status_code == 200:
            print("✅ Health check endpoint responded with status 200")
            health_data = response.json()
            print(f"Status: {health_data.get('status', 'Unknown')}")
            print(f"Environment: {health_data.get('environment', 'Unknown')}")
            print(f"Uptime: {health_data.get('uptime_formatted', 'Unknown')}")
            
            # Check components
            components = health_data.get('components', {})
            print("\nComponent Status:")
            for component, status in components.items():
                print(f"- {component}: {status}")
                
            return True
        else:
            print(f"❌ Health check failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error connecting to health endpoint: {str(e)}")
        return False

async def main():
    """Run all tests."""
    print("Google Ads MCP Server - Health Check Test")
    print("========================================")
    
    server_running = await test_http_health_endpoint()
    
    if server_running:
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Tests failed. Make sure the server is running.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 