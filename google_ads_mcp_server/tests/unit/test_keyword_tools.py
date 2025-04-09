import unittest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime, timedelta

# Import services that the tools rely on
from google_ads_mcp_server.google_ads.keywords import KeywordService

# Import the keyword tools from our module
try:
    # First try to import directly from keyword module (preferred future approach)
    from google_ads_mcp_server.mcp.tools.keyword import (
        get_keywords,
        get_keywords_json,
        add_keywords,
        update_keyword,
        remove_keywords,
        get_search_terms_report,
        get_search_terms_report_json,
        analyze_search_terms,
        analyze_search_terms_json
    )
except ImportError:
    # As fallback, import from the main tools module (if re-exporting is used)
    from google_ads_mcp_server.mcp.tools import (
        get_keywords,
        get_keywords_json,
        add_keywords,
        update_keyword,
        remove_keywords,
        get_search_terms_report,
        get_search_terms_report_json,
        analyze_search_terms,
        analyze_search_terms_json
    )

# Mock visualization functions
@patch('google_ads_mcp_server.visualization.keywords.format_keyword_comparison_table')
@patch('google_ads_mcp_server.visualization.keywords.format_keyword_status_distribution')
@patch('google_ads_mcp_server.visualization.keywords.format_keyword_performance_metrics')
class TestMCPKeywordTools(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.mock_keyword_service = MagicMock(spec=KeywordService)
        
        # Sample keyword data for tests
        self.sample_keywords = [
            {
                "id": "1234567890",
                "text": "test keyword 1",
                "match_type": "EXACT",
                "status": "ENABLED",
                "ad_group_id": "987654321",
                "ad_group_name": "Test Ad Group",
                "campaign_id": "1122334455",
                "campaign_name": "Test Campaign",
                "impressions": 1000,
                "clicks": 100,
                "ctr": 10.0,
                "cost": 50.75,
                "cpc": 0.51,
                "conversions": 5,
                "conversion_value": 100.0
            },
            {
                "id": "2345678901",
                "text": "test keyword 2",
                "match_type": "BROAD",
                "status": "PAUSED",
                "ad_group_id": "987654321",
                "ad_group_name": "Test Ad Group",
                "campaign_id": "1122334455",
                "campaign_name": "Test Campaign",
                "impressions": 2000,
                "clicks": 150,
                "ctr": 7.5,
                "cost": 75.25,
                "cpc": 0.50,
                "conversions": 3,
                "conversion_value": 60.0
            }
        ]
        
        # Sample search terms data for tests
        self.sample_search_terms = [
            {
                "query": "test search term 1",
                "keyword_text": "test keyword 1",
                "match_type": "EXACT",
                "ad_group_id": "987654321",
                "ad_group_name": "Test Ad Group",
                "campaign_id": "1122334455",
                "campaign_name": "Test Campaign",
                "impressions": 500,
                "clicks": 50,
                "ctr": 10.0,
                "cost": 25.50,
                "cpc": 0.51,
                "conversions": 2,
                "cost_per_conversion": 12.75
            },
            {
                "query": "test search term 2",
                "keyword_text": "test keyword 2",
                "match_type": "BROAD",
                "ad_group_id": "987654321",
                "ad_group_name": "Test Ad Group",
                "campaign_id": "1122334455",
                "campaign_name": "Test Campaign",
                "impressions": 800,
                "clicks": 40,
                "ctr": 5.0,
                "cost": 20.00,
                "cpc": 0.50,
                "conversions": 0,
                "cost_per_conversion": 0
            }
        ]

    def test_get_keywords(self, mock_format_performance, mock_format_status, mock_format_table):
        """Test the get_keywords MCP tool."""
        # Arrange
        customer_id = "123-456-7890"
        ad_group_id = "987654321"
        status = "ENABLED"
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        self.mock_keyword_service.get_keywords.return_value = [self.sample_keywords[0]]  # Just the ENABLED one
        
        # Act
        with patch('google_ads_mcp_server.mcp.tools.keyword.keyword_service', self.mock_keyword_service):
            result = get_keywords(
                customer_id=customer_id,
                ad_group_id=ad_group_id,
                status=status,
                start_date=start_date,
                end_date=end_date
            )
        
        # Assert
        self.mock_keyword_service.get_keywords.assert_called_once_with(
            customer_id="1234567890",  # Dashes removed
            ad_group_id=ad_group_id,
            status_filter=status,
            start_date=start_date,
            end_date=end_date
        )
        self.assertIn("Google Ads Keywords", result)
        self.assertIn("Account ID: 123-456-7890", result)
        self.assertIn("test keyword 1", result)
        self.assertIn("EXACT", result)
        self.assertIn("Test Ad Group", result)
        self.assertIn("Test Campaign", result)
        self.assertIn("ENABLED", result)
        self.assertIn("1,000", result)  # Formatted impressions
        self.assertIn("$50.75", result)  # Formatted cost

    def test_get_keywords_no_results(self, mock_format_performance, mock_format_status, mock_format_table):
        """Test get_keywords when the service returns no keywords."""
        # Arrange
        customer_id = "123-456-7890"
        self.mock_keyword_service.get_keywords.return_value = []
        
        # Act
        with patch('google_ads_mcp_server.mcp.tools.keyword.keyword_service', self.mock_keyword_service):
            result = get_keywords(customer_id=customer_id)
        
        # Assert
        self.mock_keyword_service.get_keywords.assert_called_once()
        self.assertEqual(result, "No keywords found with the specified filters.")

    def test_get_keywords_json(self, mock_format_performance, mock_format_status, mock_format_table):
        """Test the get_keywords_json MCP tool."""
        # Arrange
        customer_id = "123-456-7890"
        
        self.mock_keyword_service.get_keywords.return_value = self.sample_keywords
        
        # Set up the mock return values for visualization formatters
        mock_format_table.return_value = {"chart_type": "table", "title": "Keyword Performance"}
        mock_format_status.return_value = {"chart_type": "pie", "title": "Keyword Status Distribution"}
        mock_format_performance.return_value = {"chart_type": "bar", "title": "Top Keywords"}
        
        # Act
        with patch('google_ads_mcp_server.mcp.tools.keyword.keyword_service', self.mock_keyword_service):
            result = get_keywords_json(customer_id=customer_id)
        
        # Assert
        self.mock_keyword_service.get_keywords.assert_called_once()
        mock_format_table.assert_called_with(self.sample_keywords, title="Keyword Performance")
        mock_format_status.assert_called_with(self.sample_keywords)
        # Should be called twice - once for clicks and once for cost
        self.assertEqual(mock_format_performance.call_count, 2)
        
        # Check the JSON response structure
        self.assertEqual(result["type"], "success")
        self.assertEqual(result["data"], self.sample_keywords)
        self.assertEqual(len(result["visualization"]["charts"]), 4)  # Table, pie chart, and 2 bar charts
        self.assertEqual(result["total_keywords"], 2)

    def test_add_keywords(self, mock_format_performance, mock_format_status, mock_format_table):
        """Test the add_keywords MCP tool."""
        # Arrange
        customer_id = "123-456-7890"
        ad_group_id = "987654321"
        keyword_text = "new test keyword"
        match_type = "PHRASE"
        status = "ENABLED"
        cpc_bid_micros = 500000  # $0.50
        
        self.mock_keyword_service.add_keywords.return_value = {"keyword_id": "3456789012"}
        
        # Act
        with patch('google_ads_mcp_server.mcp.tools.keyword.keyword_service', self.mock_keyword_service):
            result = add_keywords(
                customer_id=customer_id,
                ad_group_id=ad_group_id,
                keyword_text=keyword_text,
                match_type=match_type,
                status=status,
                cpc_bid_micros=cpc_bid_micros
            )
        
        # Assert
        expected_keyword = {
            "text": keyword_text,
            "match_type": match_type,
            "status": status,
            "cpc_bid_micros": cpc_bid_micros
        }
        
        self.mock_keyword_service.add_keywords.assert_called_once_with(
            customer_id="1234567890",  # Dashes removed
            ad_group_id=ad_group_id,
            keywords=[expected_keyword]
        )
        
        self.assertIn("✅ Keyword added successfully", result)
        self.assertIn("Keyword: new test keyword", result)
        self.assertIn("Match Type: PHRASE", result)
        self.assertIn("Ad Group ID: 987654321", result)
        self.assertIn("Status: ENABLED", result)
        self.assertIn("CPC Bid: $0.50", result)
        self.assertIn("Keyword ID: 3456789012", result)

    def test_add_keywords_invalid_match_type(self, mock_format_performance, mock_format_status, mock_format_table):
        """Test add_keywords with invalid match type."""
        # Arrange
        customer_id = "123-456-7890"
        ad_group_id = "987654321"
        keyword_text = "new test keyword"
        match_type = "INVALID"  # Invalid match type
        
        # Act
        with patch('google_ads_mcp_server.mcp.tools.keyword.keyword_service', self.mock_keyword_service):
            result = add_keywords(
                customer_id=customer_id,
                ad_group_id=ad_group_id,
                keyword_text=keyword_text,
                match_type=match_type
            )
        
        # Assert
        self.mock_keyword_service.add_keywords.assert_not_called()
        self.assertIn("Error: Invalid match type", result)

    def test_update_keyword(self, mock_format_performance, mock_format_status, mock_format_table):
        """Test the update_keyword MCP tool."""
        # Arrange
        customer_id = "123-456-7890"
        keyword_id = "1234567890"
        status = "PAUSED"
        cpc_bid_micros = 600000  # $0.60
        
        self.mock_keyword_service.update_keywords.return_value = {"success": True}
        
        # Act
        with patch('google_ads_mcp_server.mcp.tools.keyword.keyword_service', self.mock_keyword_service):
            result = update_keyword(
                customer_id=customer_id,
                keyword_id=keyword_id,
                status=status,
                cpc_bid_micros=cpc_bid_micros
            )
        
        # Assert
        expected_update = {
            "id": keyword_id,
            "status": status,
            "cpc_bid_micros": cpc_bid_micros
        }
        
        self.mock_keyword_service.update_keywords.assert_called_once_with(
            customer_id="1234567890",  # Dashes removed
            keyword_updates=[expected_update]
        )
        
        self.assertIn("✅ Keyword updated successfully", result)
        self.assertIn("Keyword ID: 1234567890", result)
        self.assertIn("New Status: PAUSED", result)
        self.assertIn("New CPC Bid: $0.60", result)

    def test_remove_keywords(self, mock_format_performance, mock_format_status, mock_format_table):
        """Test the remove_keywords MCP tool."""
        # Arrange
        customer_id = "123-456-7890"
        keyword_ids = "1234567890,2345678901"
        
        self.mock_keyword_service.remove_keywords.return_value = {"success": True}
        
        # Act
        with patch('google_ads_mcp_server.mcp.tools.keyword.keyword_service', self.mock_keyword_service):
            result = remove_keywords(
                customer_id=customer_id,
                keyword_ids=keyword_ids
            )
        
        # Assert
        self.mock_keyword_service.remove_keywords.assert_called_once_with(
            customer_id="1234567890",  # Dashes removed
            keyword_ids=["1234567890", "2345678901"]
        )
        
        self.assertIn("✅ Keywords removed successfully", result)
        self.assertIn("Removed 2 keywords", result)

    def test_get_search_terms_report(self, mock_format_performance, mock_format_status, mock_format_table):
        """Test the get_search_terms_report MCP tool."""
        # Arrange
        customer_id = "123-456-7890"
        campaign_id = "1122334455"
        
        self.mock_keyword_service.get_search_terms.return_value = self.sample_search_terms
        
        # Act
        with patch('google_ads_mcp_server.mcp.tools.keyword.keyword_service', self.mock_keyword_service):
            result = get_search_terms_report(
                customer_id=customer_id,
                campaign_id=campaign_id
            )
        
        # Assert
        self.mock_keyword_service.get_search_terms.assert_called_once_with(
            customer_id="1234567890",  # Dashes removed
            campaign_id=campaign_id,
            ad_group_id=None,
            start_date=None,
            end_date=None
        )
        
        self.assertIn("Google Ads Search Terms Report", result)
        self.assertIn("Account ID: 123-456-7890", result)
        self.assertIn("Campaign Filter: 1122334455", result)
        self.assertIn("test search term 1", result)
        self.assertIn("test keyword 1", result)
        self.assertIn("EXACT", result)
        self.assertIn("500", result)
        self.assertIn("$25.50", result)

    def test_analyze_search_terms(self, mock_format_performance, mock_format_status, mock_format_table):
        """Test the analyze_search_terms MCP tool."""
        # Arrange
        customer_id = "123-456-7890"
        
        # Create a sample with no conversions for one search term (wasted spend)
        no_conv_term = self.sample_search_terms[1]  # Already has 0 conversions
        
        # Create a sample with high CTR
        high_ctr_term = self.sample_search_terms[0].copy()
        high_ctr_term["ctr"] = 15.0
        high_ctr_term["impressions"] = 100
        
        self.mock_keyword_service.get_search_terms.return_value = [
            self.sample_search_terms[0],  # Good converting term
            no_conv_term,                # Wasted spend term
            high_ctr_term                # High CTR term
        ]
        
        # Act
        with patch('google_ads_mcp_server.mcp.tools.keyword.keyword_service', self.mock_keyword_service):
            result = analyze_search_terms(customer_id=customer_id)
        
        # Assert
        self.mock_keyword_service.get_search_terms.assert_called_once()
        
        # Check for various sections in the analysis
        self.assertIn("Google Ads Search Terms Analysis", result)
        self.assertIn("Account ID: 123-456-7890", result)
        self.assertIn("Total Search Terms Analyzed: 3", result)
        
        # Check for top converting terms section
        self.assertIn("Top Performing Search Terms by Conversions:", result)
        self.assertIn("'test search term 1'", result)
        self.assertIn("2.0 conversions", result)
        
        # Check for wasted spend section
        self.assertIn("Potential Wasted Spend (High Cost, No Conversions):", result)
        self.assertIn("'test search term 2'", result)
        self.assertIn("$20.00 cost", result)
        self.assertIn("Consider adding these terms as negative keywords", result)
        
        # Check for high CTR section
        self.assertIn("High-Performing Search Terms by CTR:", result)
        self.assertIn("15.00% CTR", result)
        self.assertIn("Consider adding these high-CTR terms as keywords", result)

    def test_get_search_terms_report_json(self, mock_format_performance, mock_format_status, mock_format_table):
        """Test the get_search_terms_report_json MCP tool."""
        # Arrange
        customer_id = "123-456-7890"
        
        self.mock_keyword_service.get_search_terms.return_value = self.sample_search_terms
        
        # Mock the format_for_visualization function
        mock_visualization = {"chart_type": "bar", "title": "Search Terms"}
        
        # Act
        with patch('google_ads_mcp_server.mcp.tools.keyword.keyword_service', self.mock_keyword_service), \
             patch('google_ads_mcp_server.mcp.tools.keyword.format_for_visualization', return_value=mock_visualization):
            result = get_search_terms_report_json(customer_id=customer_id)
        
        # Assert
        self.mock_keyword_service.get_search_terms.assert_called_once()
        
        # Check the JSON response structure
        self.assertEqual(result["type"], "success")
        self.assertEqual(result["data"], self.sample_search_terms)
        self.assertEqual(result["visualization"], mock_visualization)
        self.assertEqual(result["total_search_terms"], 2)

if __name__ == '__main__':
    unittest.main() 