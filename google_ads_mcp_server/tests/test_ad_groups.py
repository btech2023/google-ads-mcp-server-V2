import os
import asyncio
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_ads.client import GoogleAdsService
from google_ads.ad_groups import AdGroupService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test-ad-groups")

async def test_ad_group_service():
    """Test the Ad Group service functionality."""
    try:
        print("Starting Ad Group service test...")
        
        # Initialize Google Ads service
        google_ads_service = GoogleAdsService()
        print(f"✓ Successfully initialized GoogleAdsService")
        
        # Initialize Ad Group service
        ad_group_service = AdGroupService(google_ads_service)
        print(f"✓ Successfully initialized AdGroupService")
        
        customer_id = google_ads_service.client_customer_id
        print(f"Using customer ID: {customer_id}")
        
        # Test get_ad_groups
        print("\nTesting get_ad_groups...")
        ad_groups = await ad_group_service.get_ad_groups(customer_id)
        print(f"✓ Retrieved {len(ad_groups)} ad groups")
        
        # Display ad group data if available
        if ad_groups:
            print("\nFirst ad group details:")
            sample = ad_groups[0]
            for key, value in sample.items():
                print(f"  {key}: {value}")
            
            # Test get_ad_group_performance with the first ad group
            ad_group_id = sample['id']
            print(f"\nTesting get_ad_group_performance for ad group {ad_group_id}...")
            performance = await ad_group_service.get_ad_group_performance(
                customer_id=customer_id,
                ad_group_id=ad_group_id
            )
            print(f"✓ Retrieved performance data:")
            
            # Display performance summary
            print("\nPerformance summary:")
            for key in ['impressions', 'clicks', 'cost', 'conversions', 'ctr', 'cpc', 'roas']:
                print(f"  {key}: {performance.get(key)}")
                
            print(f"\nRetrieved {len(performance['daily_stats'])} days of daily statistics")
        else:
            print("No ad groups found for testing.")
            
            # Try creating a test ad group if no ad groups exist
            print("\nTesting create_ad_group...")
            print("Fetching campaigns to find a parent for the new ad group...")
            
            # Get campaigns to find one to use as parent
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            today = datetime.now().strftime("%Y-%m-%d")
            campaigns = await google_ads_service.get_campaigns(yesterday, today)
            
            if not campaigns:
                # Try with a wider date range
                last_month = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                campaigns = await google_ads_service.get_campaigns(last_month, today)
            
            if campaigns:
                # Find an enabled campaign
                enabled_campaigns = [c for c in campaigns if c['status'] == 'ENABLED']
                if enabled_campaigns:
                    campaign = enabled_campaigns[0]
                    campaign_id = campaign['id']
                    
                    print(f"Creating test ad group in campaign {campaign_id}...")
                    test_name = f"Test Ad Group {datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    result = await ad_group_service.create_ad_group(
                        customer_id=customer_id,
                        campaign_id=campaign_id,
                        name=test_name,
                        status="PAUSED"  # Use PAUSED for testing
                    )
                    
                    print(f"✓ Created test ad group: {result}")
                    
                    # Update the newly created ad group
                    ad_group_id = result['ad_group_id']
                    print(f"\nTesting update_ad_group for ad group {ad_group_id}...")
                    
                    update_result = await ad_group_service.update_ad_group(
                        customer_id=customer_id,
                        ad_group_id=ad_group_id,
                        name=f"{test_name} - Updated"
                    )
                    
                    print(f"✓ Updated test ad group: {update_result}")
                else:
                    print("No enabled campaigns found for creating a test ad group.")
            else:
                print("No campaigns found for creating a test ad group.")
        
        print("\n✅ Ad Group service test completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Error during Ad Group service test: {str(e)}")
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
    print("\nRunning Ad Group service test...\n")
    result = asyncio.run(test_ad_group_service())
    
    # Print final result
    if result:
        print("\n✅ Ad Group service test successful!")
    else:
        print("\n❌ Ad Group service test failed.") 