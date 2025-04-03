"""
Unit tests for visualization formatters.
"""

import unittest
import logging
from typing import Dict, Any

from visualization.keywords import (
    format_keyword_comparison_table,
    format_keyword_status_distribution,
    format_keyword_performance_metrics
)
from visualization.search_terms import (
    format_search_term_table,
    format_search_term_word_cloud,
    format_search_term_analysis
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test-visualization")

class TestKeywordVisualizations(unittest.TestCase):
    """Test cases for keyword visualizations."""
    
    def setUp(self):
        """Set up test data for keyword visualizations."""
        # Sample keyword data
        self.keyword_data = [
            {
                "id": "1234567890",
                "text": "test keyword 1",
                "match_type": "EXACT",
                "status": "ENABLED",
                "ad_group_id": "12345",
                "ad_group_name": "Test Ad Group",
                "campaign_id": "67890",
                "campaign_name": "Test Campaign",
                "impressions": 1000,
                "clicks": 50,
                "cost": 75.50,
                "ctr": 5.0,
                "conversions": 2.5,
                "conversion_value": 125.75,
                "cost_per_conversion": 30.20,
                "roas": 1.67
            },
            {
                "id": "2345678901",
                "text": "test keyword 2",
                "match_type": "PHRASE",
                "status": "PAUSED",
                "ad_group_id": "12345",
                "ad_group_name": "Test Ad Group",
                "campaign_id": "67890",
                "campaign_name": "Test Campaign",
                "impressions": 500,
                "clicks": 25,
                "cost": 35.25,
                "ctr": 5.0,
                "conversions": 1.0,
                "conversion_value": 50.0,
                "cost_per_conversion": 35.25,
                "roas": 1.42
            },
            {
                "id": "3456789012",
                "text": "test keyword 3",
                "match_type": "BROAD",
                "status": "REMOVED",
                "ad_group_id": "12345",
                "ad_group_name": "Test Ad Group",
                "campaign_id": "67890",
                "campaign_name": "Test Campaign",
                "impressions": 2000,
                "clicks": 100,
                "cost": 150.0,
                "ctr": 5.0,
                "conversions": 5.0,
                "conversion_value": 300.0,
                "cost_per_conversion": 30.0,
                "roas": 2.0
            }
        ]
        
        # Empty data for testing edge cases
        self.empty_keyword_data = []
    
    def test_keyword_comparison_table(self):
        """Test keyword comparison table formatter."""
        # Test with valid data
        result = format_keyword_comparison_table(self.keyword_data)
        
        # Check structure
        self.assertEqual(result["chart_type"], "table")
        self.assertEqual(result["title"], "Keyword Performance")
        self.assertTrue("columns" in result)
        self.assertTrue("data" in result)
        
        # Check columns
        column_keys = [col["key"] for col in result["columns"]]
        expected_keys = ["id", "text", "match_type", "status", "ad_group_name", "campaign_name", 
                         "impressions", "clicks", "cost", "ctr", "conversions", "conversion_value", 
                         "cost_per_conversion", "roas"]
        for key in expected_keys:
            self.assertIn(key, column_keys)
        
        # Check data sorting (by cost, descending)
        self.assertEqual(result["data"][0]["id"], "3456789012")  # Highest cost
        self.assertEqual(result["data"][2]["id"], "2345678901")  # Lowest cost
        
        # Test with empty data
        empty_result = format_keyword_comparison_table(self.empty_keyword_data)
        self.assertEqual(empty_result["chart_type"], "table")
        self.assertEqual(len(empty_result["columns"]), 0)
        self.assertEqual(len(empty_result["data"]), 0)
    
    def test_keyword_status_distribution(self):
        """Test keyword status distribution formatter."""
        # Test with valid data
        result = format_keyword_status_distribution(self.keyword_data)
        
        # Check structure
        self.assertEqual(result["chart_type"], "pie")
        self.assertEqual(result["title"], "Keyword Status Distribution")
        self.assertTrue("labels" in result)
        self.assertTrue("values" in result)
        
        # Check data
        self.assertEqual(len(result["labels"]), 3)  # 3 unique statuses
        self.assertEqual(len(result["values"]), 3)
        self.assertEqual(sum(result["values"]), 3)  # 3 total keywords
        
        # Test with empty data
        empty_result = format_keyword_status_distribution(self.empty_keyword_data)
        self.assertEqual(empty_result["chart_type"], "pie")
        self.assertEqual(len(empty_result["labels"]), 0)
        self.assertEqual(len(empty_result["values"]), 0)
    
    def test_keyword_performance_metrics(self):
        """Test keyword performance metrics formatter."""
        # Test with valid data and clicks metric
        result_clicks = format_keyword_performance_metrics(self.keyword_data, metric="clicks")
        
        # Check structure
        self.assertEqual(result_clicks["chart_type"], "bar")
        self.assertEqual(result_clicks["orientation"], "horizontal")
        self.assertEqual(result_clicks["title"], "Top Keywords by Clicks")
        self.assertEqual(result_clicks["axis_x"]["name"], "Clicks")
        self.assertEqual(result_clicks["axis_y"]["name"], "Keyword")
        
        # Check data sorting (by clicks, descending)
        self.assertEqual(result_clicks["labels"][0], "test keyword 3")  # Highest clicks
        self.assertEqual(result_clicks["values"][0], 100)
        
        # Test with cost metric
        result_cost = format_keyword_performance_metrics(self.keyword_data, metric="cost")
        
        # Check structure
        self.assertEqual(result_cost["title"], "Top Keywords by Cost")
        self.assertEqual(result_cost["format"], "currency")
        
        # Check data sorting (by cost, descending)
        self.assertEqual(result_cost["labels"][0], "test keyword 3")  # Highest cost
        self.assertEqual(result_cost["values"][0], 150.0)
        
        # Test with empty data
        empty_result = format_keyword_performance_metrics(self.empty_keyword_data)
        self.assertEqual(empty_result["chart_type"], "bar")
        self.assertEqual(len(empty_result["labels"]), 0)
        self.assertEqual(len(empty_result["values"]), 0)

class TestSearchTermVisualizations(unittest.TestCase):
    """Test cases for search term visualizations."""
    
    def setUp(self):
        """Set up test data for search term visualizations."""
        # Sample search term data
        self.search_term_data = [
            {
                "search_term": "test search term 1",
                "ad_group_id": "12345",
                "ad_group_name": "Test Ad Group",
                "campaign_id": "67890",
                "campaign_name": "Test Campaign",
                "impressions": 1000,
                "clicks": 50,
                "cost": 75.50,
                "ctr": 5.0,
                "conversions": 2.5,
                "conversion_value": 125.75,
                "cpc": 1.51,
                "cost_per_conversion": 30.20,
                "roas": 1.67
            },
            {
                "search_term": "test search term 2",
                "ad_group_id": "12345",
                "ad_group_name": "Test Ad Group",
                "campaign_id": "67890",
                "campaign_name": "Test Campaign",
                "impressions": 500,
                "clicks": 25,
                "cost": 35.25,
                "ctr": 5.0,
                "conversions": 1.0,
                "conversion_value": 50.0,
                "cpc": 1.41,
                "cost_per_conversion": 35.25,
                "roas": 1.42
            },
            {
                "search_term": "test search term 3",
                "ad_group_id": "12345",
                "ad_group_name": "Test Ad Group",
                "campaign_id": "67890",
                "campaign_name": "Test Campaign",
                "impressions": 2000,
                "clicks": 100,
                "cost": 150.0,
                "ctr": 5.0,
                "conversions": 5.0,
                "conversion_value": 300.0,
                "cpc": 1.50,
                "cost_per_conversion": 30.0,
                "roas": 2.0
            },
            {
                "search_term": "test search term 1",  # Duplicate to test aggregation
                "ad_group_id": "54321",
                "ad_group_name": "Another Ad Group",
                "campaign_id": "67890",
                "campaign_name": "Test Campaign",
                "impressions": 800,
                "clicks": 40,
                "cost": 60.0,
                "ctr": 5.0,
                "conversions": 2.0,
                "conversion_value": 100.0,
                "cpc": 1.50,
                "cost_per_conversion": 30.0,
                "roas": 1.67
            }
        ]
        
        # Sample search term analysis data
        self.search_term_analysis = {
            "total_search_terms": 3,
            "total_impressions": 4300,
            "total_clicks": 215,
            "total_cost": 320.75,
            "total_conversions": 10.5,
            "average_ctr": 5.0,
            "average_cpc": 1.49,
            "average_conversion_rate": 4.88,
            "top_performing_terms": self.search_term_data[:2],
            "low_performing_terms": [],
            "potential_negative_keywords": []
        }
        
        # Empty data for testing edge cases
        self.empty_search_term_data = []
        self.empty_search_term_analysis = {
            "total_search_terms": 0,
            "total_impressions": 0,
            "total_clicks": 0,
            "total_cost": 0,
            "total_conversions": 0,
            "average_ctr": 0,
            "average_cpc": 0,
            "average_conversion_rate": 0,
            "top_performing_terms": [],
            "low_performing_terms": [],
            "potential_negative_keywords": []
        }
    
    def test_search_term_table(self):
        """Test search term table formatter."""
        # Test with valid data
        result = format_search_term_table(self.search_term_data)
        
        # Check structure
        self.assertEqual(result["chart_type"], "table")
        self.assertEqual(result["title"], "Search Term Performance")
        self.assertTrue("columns" in result)
        self.assertTrue("data" in result)
        
        # Check columns
        column_keys = [col["key"] for col in result["columns"]]
        expected_keys = ["search_term", "ad_group_name", "campaign_name", "impressions", "clicks", 
                         "cost", "ctr", "conversions", "conversion_value", "cpc", 
                         "cost_per_conversion", "roas"]
        for key in expected_keys:
            self.assertIn(key, column_keys)
        
        # Check data sorting (by cost, descending)
        self.assertEqual(result["data"][0]["search_term"], "test search term 3")  # Highest cost
        
        # Test with empty data
        empty_result = format_search_term_table(self.empty_search_term_data)
        self.assertEqual(empty_result["chart_type"], "table")
        self.assertEqual(len(empty_result["columns"]), 0)
        self.assertEqual(len(empty_result["data"]), 0)
    
    def test_search_term_word_cloud(self):
        """Test search term word cloud formatter."""
        # Test with valid data and cost metric
        result = format_search_term_word_cloud(self.search_term_data, weight_metric="cost")
        
        # Check structure
        self.assertEqual(result["chart_type"], "word_cloud")
        self.assertEqual(result["title"], "Search Term Cloud by Cost")
        self.assertTrue("data" in result)
        
        # Check data
        self.assertEqual(len(result["data"]), 3)  # 3 unique search terms
        
        # Check aggregation of duplicate terms
        term1_data = next((item for item in result["data"] if item["text"] == "test search term 1"), None)
        self.assertIsNotNone(term1_data)
        self.assertEqual(term1_data["value"], 135.5)  # 75.50 + 60.0
        
        # Check sorting
        self.assertEqual(result["data"][0]["text"], "test search term 3")  # Highest cost
        
        # Test with clicks metric
        result_clicks = format_search_term_word_cloud(self.search_term_data, weight_metric="clicks")
        self.assertEqual(result_clicks["title"], "Search Term Cloud by Clicks")
        
        # Check aggregation with clicks
        term1_clicks = next((item for item in result_clicks["data"] if item["text"] == "test search term 1"), None)
        self.assertIsNotNone(term1_clicks)
        self.assertEqual(term1_clicks["value"], 90)  # 50 + 40
        
        # Test with empty data
        empty_result = format_search_term_word_cloud(self.empty_search_term_data)
        self.assertEqual(empty_result["chart_type"], "word_cloud")
        self.assertEqual(len(empty_result["data"]), 0)
    
    def test_search_term_analysis(self):
        """Test search term analysis formatter."""
        # Test with valid data
        result = format_search_term_analysis(self.search_term_analysis)
        
        # Check structure
        self.assertEqual(result["chart_type"], "composite")
        self.assertEqual(result["title"], "Search Term Analysis")
        self.assertTrue("components" in result)
        
        # Check components
        self.assertEqual(len(result["components"]), 4)  # 4 components: summary, top terms, low terms, negative terms
        
        # Check summary component
        summary = result["components"][0]
        self.assertEqual(summary["chart_type"], "metrics")
        self.assertEqual(len(summary["metrics"]), 8)  # 8 summary metrics
        
        # Check top terms component
        top_terms = result["components"][1]
        self.assertEqual(top_terms["chart_type"], "table")
        self.assertEqual(top_terms["title"], "Top Performing Search Terms")
        self.assertEqual(len(top_terms["data"]), 2)  # 2 top performing terms
        
        # Test with empty data
        empty_result = format_search_term_analysis(self.empty_search_term_analysis)
        self.assertEqual(empty_result["chart_type"], "composite")
        self.assertEqual(len(empty_result["components"]), 0)

if __name__ == "__main__":
    unittest.main() 