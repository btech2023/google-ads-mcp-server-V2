#!/usr/bin/env python

import os
import sys
import logging
from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main():
    # Load environment variables
    if os.path.exists(".env"):
        load_dotenv(".env")
        logger.info("Loaded environment variables from ./.env")
    
    # Check required environment variables
    required_vars = [
        "GOOGLE_ADS_DEVELOPER_TOKEN", 
        "GOOGLE_ADS_CLIENT_ID",
        "GOOGLE_ADS_CLIENT_SECRET",
        "GOOGLE_ADS_REFRESH_TOKEN",
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID"
    ]
    
    for var in required_vars:
        if not os.environ.get(var):
            logger.error(f"Missing required environment variable: {var}")
            return 1
    
    # Get customer IDs
    login_customer_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    if '-' in login_customer_id:
        login_customer_id = login_customer_id.replace('-', '')
    
    client_customer_id = os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID")
    if client_customer_id and '-' in client_customer_id:
        client_customer_id = client_customer_id.replace('-', '')
    
    if not client_customer_id:
        client_customer_id = login_customer_id
    
    logger.info(f"Using login customer ID: {login_customer_id}")
    logger.info(f"Using client customer ID: {client_customer_id}")
    
    try:
        # Initialize the Google Ads client
        client = GoogleAdsClient.load_from_env()
        
        # Create a Google Ads service client
        google_ads_service = client.get_service("GoogleAdsService")
        
        # Create a simple query that doesn't use complex fields
        query = """
        SELECT
          campaign.id,
          campaign.name,
          campaign.status
        FROM campaign
        LIMIT 10
        """
        
        # Execute the search request
        search_request = client.get_type("SearchGoogleAdsRequest")
        search_request.customer_id = client_customer_id
        search_request.query = query
        
        logger.info("Executing Google Ads query...")
        response = google_ads_service.search(search_request)
        
        # Process the results
        campaign_count = 0
        for row in response:
            campaign = row.campaign
            campaign_count += 1
            logger.info(f"Campaign ID: {campaign.id}, Name: {campaign.name}, Status: {campaign.status.name}")
        
        logger.info(f"Found {campaign_count} campaigns")
        
        return 0
        
    except GoogleAdsException as ex:
        logger.error("Google Ads API Error:")
        for error in ex.failure.errors:
            logger.error(f"Error message: {error.message}")
        return 1
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 