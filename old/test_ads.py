import os
import asyncio
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_ads_client import GoogleAdsService, GoogleAdsClientError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test-ads")

async def test_google_ads_connection():
    """Test the Google Ads API connection."""
    try:
        print("Starting Google Ads API connection test...")
        
        # Initialize Google Ads service
        service = GoogleAdsService()
        print(f"✓ Successfully initialized GoogleAdsService")
        print(f"  Using login_customer_id: {service.login_customer_id}")
        print(f"  Using client_customer_id: {service.client_customer_id}")
        
        # Use yesterday and today for the date range
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"\nTesting with date range: {yesterday} to {today}")
        
        # Get campaign data
        print("Retrieving campaign data...")
        campaigns = await service.get_campaigns(yesterday, today)
        print(f"✓ Retrieved {len(campaigns)} campaigns")
        
        # Display campaign data if available
        if campaigns:
            print("\nFirst campaign details:")
            sample = campaigns[0]
            for key, value in sample.items():
                print(f"  {key}: {value}")
        else:
            print("No campaigns found in the date range.")
            
            # Try with a wider date range
            last_month = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            print(f"\nTrying with a wider date range: {last_month} to {today}")
            campaigns = await service.get_campaigns(last_month, today)
            print(f"✓ Retrieved {len(campaigns)} campaigns with wider date range")
            
            if campaigns:
                print("\nFirst campaign details:")
                sample = campaigns[0]
                for key, value in sample.items():
                    print(f"  {key}: {value}")
        
        return True
    except GoogleAdsClientError as e:
        print(f"❌ Google Ads API error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Load environment variables
    print("Loading environment variables...")
    load_dotenv()
    
    # Print environment variables (masked)
    for var in ["GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CLIENT_ID", 
                "GOOGLE_ADS_CLIENT_SECRET", "GOOGLE_ADS_REFRESH_TOKEN", 
                "GOOGLE_ADS_LOGIN_CUSTOMER_ID", "GOOGLE_ADS_CLIENT_CUSTOMER_ID"]:
        value = os.environ.get(var, "")
        if value:
            masked = value[:5] + "..." + value[-5:] if len(value) > 10 else "(too short to mask)"
            print(f"- {var}: {masked}")
        else:
            print(f"- {var}: NOT SET")
    
    # Run the test
    print("\nRunning connection test...\n")
    result = asyncio.run(test_google_ads_connection())
    
    # Print final result
    if result:
        print("\n✅ Connection test successful!")
    else:
        print("\n❌ Connection test failed.") 