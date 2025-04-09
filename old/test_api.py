import os, asyncio, logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_ads_client import GoogleAdsService, GoogleAdsClientError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test-api")

async def test_google_ads_connection():
    """Test the Google Ads API connection."""
    try:
        print("Starting Google Ads API connection test...")
        
        # Initialize Google Ads service
        service = GoogleAdsService()
        print(f"Successfully initialized GoogleAdsService")
        print(f"Using login_customer_id: {service.login_customer_id}")
        print(f"Using client_customer_id: {service.client_customer_id}")
        
        # Use yesterday and today for the date range
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"Testing with date range: {yesterday} to {today}")
        
        # Get campaign data
        print("Retrieving campaign data...")
        campaigns = await service.get_campaigns(yesterday, today)
        print(f"Retrieved {len(campaigns)} campaigns")
        
        # Display campaign data if available
        if campaigns:
            print("First campaign details:")
            sample = campaigns[0]
            for key, value in sample.items():
                print(f"  {key}: {value}")
        else:
            print("No campaigns found in the date range.")
            
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Load environment variables
    print("Loading environment variables...")
    load_dotenv()
    
    # Run the test
    print("Running connection test...")
    result = asyncio.run(test_google_ads_connection())
    
    # Print final result
    if result:
        print("Connection test successful!")
    else:
        print("Connection test failed.") 