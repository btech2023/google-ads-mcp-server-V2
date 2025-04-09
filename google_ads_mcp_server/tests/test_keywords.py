import os
import asyncio
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google_ads_mcp_server.google_ads.client import GoogleAdsService
from google_ads_mcp_server.google_ads.keywords import KeywordService
import unittest
from unittest.mock import patch, AsyncMock

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test-keywords")

async def test_keyword_service():
    """Test the Keyword service functionality."""
    try:
        print("Starting Keyword service test...")
        
        # Initialize Google Ads service
        google_ads_service = GoogleAdsService()
        print(f"✓ Successfully initialized GoogleAdsService")
        
        # Initialize Keyword service
        keyword_service = KeywordService(google_ads_service)
        print(f"✓ Successfully initialized KeywordService")
        
        customer_id = google_ads_service.client_customer_id
        print(f"Using customer ID: {customer_id}")
        
        # Test get_keywords
        print("\nTesting get_keywords...")
        
        # Calculate default date range
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        keywords = await keyword_service.get_keywords(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"✓ Retrieved {len(keywords)} keywords")
        
        # Display keyword data if available
        if keywords:
            print("\nFirst keyword details:")
            sample = keywords[0]
            for key, value in sample.items():
                print(f"  {key}: {value}")
            
            # If there are active ad groups, we can test the add/update/remove functionality
            
            # First, get the ad groups to find one for testing
            print("\nGetting ad groups to find one for keyword testing...")
            from google_ads_mcp_server.google_ads.ad_groups import AdGroupService
            ad_group_service = AdGroupService(google_ads_service)
            ad_groups = await ad_group_service.get_ad_groups(customer_id)
            
            if ad_groups:
                # Find an enabled ad group
                enabled_ad_groups = [ag for ag in ad_groups if ag['status'] == 'ENABLED']
                if enabled_ad_groups:
                    ad_group = enabled_ad_groups[0]
                    ad_group_id = ad_group['id']
                    
                    # Test adding a keyword
                    print(f"\nTesting add_keywords to ad group {ad_group_id}...")
                    test_keyword = f"test keyword {datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    # Create keyword specification
                    keyword_spec = [{
                        "text": test_keyword,
                        "match_type": "BROAD",
                        "status": "PAUSED"  # Use PAUSED for testing
                    }]
                    
                    result = await keyword_service.add_keywords(
                        customer_id=customer_id,
                        ad_group_id=ad_group_id,
                        keywords=keyword_spec
                    )
                    
                    print(f"✓ Add keywords result: {result}")
                    
                    if result.get('success') and result.get('created_keywords'):
                        # Get the new keyword ID for later tests
                        new_keyword_id = result['created_keywords'][0]['criterion_id']
                        
                        # Test updating the keyword
                        print(f"\nTesting update_keywords for keyword {new_keyword_id}...")
                        
                        update_result = await keyword_service.update_keywords(
                            customer_id=customer_id,
                            keyword_updates=[{
                                "id": new_keyword_id,
                                "status": "ENABLED"
                            }]
                        )
                        
                        print(f"✓ Update keyword result: {update_result}")
                        
                        # Test removing the keyword (set to REMOVED)
                        print(f"\nTesting remove_keywords for keyword {new_keyword_id}...")
                        
                        remove_result = await keyword_service.remove_keywords(
                            customer_id=customer_id,
                            keyword_ids=[new_keyword_id]
                        )
                        
                        print(f"✓ Remove keyword result: {remove_result}")
                    else:
                        print("⚠ Could not create a test keyword for update/remove testing")
                else:
                    print("⚠ No enabled ad groups found for keyword testing")
            else:
                print("⚠ No ad groups found for keyword testing")
        else:
            print("No keywords found for this customer in the current date range.")
        
        # Test search term functionality
        print("\nTesting search term functionality...")
        from google_ads_mcp_server.google_ads.search_terms import SearchTermService
        search_term_service = SearchTermService(google_ads_service)
        
        search_terms = await search_term_service.get_search_terms(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"✓ Retrieved {len(search_terms)} search terms")
        
        # Display search term data if available
        if search_terms:
            print("\nFirst search term details:")
            sample = search_terms[0]
            for key, value in sample.items():
                print(f"  {key}: {value}")
                
            # Test search term analysis
            print("\nTesting search term analysis...")
            
            analysis = await search_term_service.analyze_search_terms(
                customer_id=customer_id,
                start_date=start_date,
                end_date=end_date
            )
            
            print(f"✓ Completed search term analysis")
            print(f"  Total search terms: {analysis['total_search_terms']}")
            print(f"  Total clicks: {analysis['total_clicks']}")
            print(f"  Total cost: ${analysis['total_cost']:.2f}")
            print(f"  Top performing terms: {len(analysis['top_performing_terms'])}")
            print(f"  Low performing terms: {len(analysis['low_performing_terms'])}")
        else:
            print("No search terms found for this customer in the current date range.")
        
        print("\n✅ Keyword service test completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Error during Keyword service test: {str(e)}")
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
    print("\nRunning Keyword service test...\n")
    result = asyncio.run(test_keyword_service())
    
    # Print final result
    if result:
        print("\n✅ Keyword service test successful!")
    else:
        print("\n❌ Keyword service test failed.") 