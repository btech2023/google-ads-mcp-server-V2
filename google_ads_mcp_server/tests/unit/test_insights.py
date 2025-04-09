"""
Unit tests for the Insights Service and visualization components.
"""

import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
import json
import asyncio

from google_ads_mcp_server.google_ads.insights import InsightsService
from visualization.insights import (
    format_anomalies_visualization,
    format_optimization_suggestions_visualization,
    format_opportunities_visualization,
    format_insights_visualization
)

class TestInsightsService(unittest.TestCase):
    """
    Test cases for the InsightsService class.
    """
    
    def setUp(self):
        """Set up test dependencies."""
        self.google_ads_service = MagicMock()
        
        # Mock dependent services
        self.keyword_service = MagicMock()
        self.search_term_service = MagicMock()
        self.budget_service = MagicMock()
        self.ad_group_service = MagicMock()
        
        # Set up InsightsService with mocked dependencies
        self.insights_service = InsightsService(self.google_ads_service)
        self.insights_service.keyword_service = self.keyword_service
        self.insights_service.search_term_service = self.search_term_service
        self.insights_service.budget_service = self.budget_service
        self.insights_service.ad_group_service = self.ad_group_service
    
    @patch.object(InsightsService, '_get_performance_data')
    @patch.object(InsightsService, '_get_comparison_data')
    @patch.object(InsightsService, '_analyze_for_anomalies')
    async def test_detect_performance_anomalies(self, mock_analyze, mock_get_comparison, mock_get_performance):
        """Test detect_performance_anomalies method."""
        # Set up mocks
        mock_get_performance.return_value = [
            {"id": "1", "name": "Campaign 1", "impressions": 1000, "clicks": 50, "cost": 100.0},
            {"id": "2", "name": "Campaign 2", "impressions": 2000, "clicks": 100, "cost": 200.0}
        ]
        mock_get_comparison.return_value = [
            {"id": "1", "name": "Campaign 1", "impressions": 800, "clicks": 40, "cost": 80.0},
            {"id": "2", "name": "Campaign 2", "impressions": 2200, "clicks": 110, "cost": 220.0}
        ]
        mock_analyze.return_value = [
            {
                "entity_type": "CAMPAIGN",
                "entity_id": "1",
                "entity_name": "Campaign 1",
                "metric": "impressions",
                "current_value": 1000,
                "comparison_value": 800,
                "percent_change": 25.0,
                "direction": "INCREASE",
                "severity": "MEDIUM"
            }
        ]
        
        # Call the method
        result = await self.insights_service.detect_performance_anomalies(
            customer_id="123456789",
            entity_type="CAMPAIGN",
            metrics=["impressions", "clicks", "cost"]
        )
        
        # Assertions
        self.assertIsInstance(result, dict)
        self.assertIn("anomalies", result)
        self.assertIn("metadata", result)
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["entity_id"], "1")
        
        # Verify calls
        mock_get_performance.assert_called_once()
        mock_get_comparison.assert_called_once()
        mock_analyze.assert_called_once()
    
    @patch.object(InsightsService, '_analyze_campaigns_for_suggestions')
    @patch.object(InsightsService, '_analyze_ad_groups_for_suggestions')
    @patch.object(InsightsService, '_analyze_keywords_for_suggestions')
    async def test_generate_optimization_suggestions(self, mock_keywords, mock_ad_groups, mock_campaigns):
        """Test generate_optimization_suggestions method."""
        # Set up mocks
        mock_campaigns.return_value = {
            "budget_allocation": [{"entity_id": "1", "entity_name": "Campaign 1", "suggestion": "Increase budget", "impact": "HIGH"}],
            "bid_management": [],
            "negative_keywords": [],
            "ad_copy": [],
            "account_structure": []
        }
        mock_ad_groups.return_value = {
            "budget_allocation": [],
            "bid_management": [],
            "negative_keywords": [],
            "ad_copy": [{"entity_id": "101", "entity_name": "Ad Group 1", "suggestion": "Improve ad copy", "impact": "MEDIUM"}],
            "account_structure": []
        }
        mock_keywords.return_value = {
            "budget_allocation": [],
            "bid_management": [{"entity_id": "1001", "entity_text": "Keyword 1", "suggestion": "Increase bid", "impact": "HIGH"}],
            "negative_keywords": [{"entity_text": "Irrelevant Term", "suggestion": "Add negative keyword", "impact": "MEDIUM"}],
            "ad_copy": [],
            "account_structure": []
        }
        
        # Call the method
        result = await self.insights_service.generate_optimization_suggestions(
            customer_id="123456789",
            entity_types=["CAMPAIGN", "AD_GROUP", "KEYWORD"]
        )
        
        # Assertions
        self.assertIsInstance(result, dict)
        self.assertIn("suggestions", result)
        self.assertIn("metadata", result)
        self.assertEqual(len(result["suggestions"]["budget_allocation"]), 1)
        self.assertEqual(len(result["suggestions"]["ad_copy"]), 1)
        self.assertEqual(len(result["suggestions"]["bid_management"]), 1)
        self.assertEqual(len(result["suggestions"]["negative_keywords"]), 1)
        self.assertEqual(result["metadata"]["total_suggestions"], 4)
        
        # Verify calls
        mock_campaigns.assert_called_once()
        mock_ad_groups.assert_called_once()
        mock_keywords.assert_called_once()
    
    @patch.object(InsightsService, '_discover_keyword_opportunities')
    @patch.object(InsightsService, '_discover_ad_variation_opportunities')
    @patch.object(InsightsService, '_discover_structure_opportunities')
    async def test_discover_opportunities(self, mock_structure, mock_ad_variations, mock_keywords):
        """Test discover_opportunities method."""
        # Set up mocks
        mock_keywords.return_value = [
            {
                "type": "ADD_KEYWORD_FROM_SEARCH_TERM",
                "search_term": "test keyword",
                "ad_group_name": "Ad Group 1",
                "impressions": 500,
                "clicks": 25,
                "conversions": 2,
                "opportunity": "Add 'test keyword' as a keyword",
                "impact": "HIGH"
            }
        ]
        mock_ad_variations.return_value = [
            {
                "type": "CREATE_AD_VARIATION",
                "entity_name": "Ad Group 2",
                "campaign_name": "Campaign 2",
                "opportunity": "Create additional ad variations",
                "impact": "MEDIUM"
            }
        ]
        mock_structure.return_value = [
            {
                "type": "SPLIT_LARGE_AD_GROUP",
                "entity_name": "Large Ad Group",
                "campaign_name": "Campaign 3",
                "opportunity": "Split large ad group into themes",
                "impact": "MEDIUM"
            }
        ]
        
        # Call the method
        result = await self.insights_service.discover_opportunities(
            customer_id="123456789"
        )
        
        # Assertions
        self.assertIsInstance(result, dict)
        self.assertIn("opportunities", result)
        self.assertIn("metadata", result)
        self.assertEqual(len(result["opportunities"]["keyword_expansion"]), 1)
        self.assertEqual(len(result["opportunities"]["ad_variation"]), 1)
        self.assertEqual(len(result["opportunities"]["structure"]), 1)
        self.assertEqual(result["metadata"]["total_opportunities"], 3)
        
        # Verify calls
        mock_keywords.assert_called_once()
        mock_ad_variations.assert_called_once()
        mock_structure.assert_called_once()

class TestInsightsVisualizations(unittest.TestCase):
    """
    Test cases for the insights visualization functions.
    """
    
    def test_format_anomalies_visualization(self):
        """Test format_anomalies_visualization function."""
        # Sample data
        anomalies_data = {
            "anomalies": [
                {
                    "entity_type": "CAMPAIGN",
                    "entity_id": "1",
                    "entity_name": "Campaign 1",
                    "metric": "impressions",
                    "current_value": 1000,
                    "comparison_value": 800,
                    "percent_change": 25.0,
                    "direction": "INCREASE",
                    "severity": "MEDIUM"
                },
                {
                    "entity_type": "CAMPAIGN",
                    "entity_id": "2",
                    "entity_name": "Campaign 2",
                    "metric": "clicks",
                    "current_value": 100,
                    "comparison_value": 150,
                    "percent_change": -33.33,
                    "direction": "DECREASE",
                    "severity": "HIGH"
                }
            ],
            "metadata": {
                "customer_id": "123456789",
                "entity_type": "CAMPAIGN",
                "start_date": "2025-05-01",
                "end_date": "2025-05-07",
                "comparison_period": "PREVIOUS_PERIOD",
                "threshold": 2.0,
                "total_entities_analyzed": 10,
                "anomalies_detected": 2,
                "metrics_analyzed": ["impressions", "clicks", "cost", "ctr", "conversions"]
            }
        }
        
        # Call the function
        result = format_anomalies_visualization(anomalies_data)
        
        # Assertions
        self.assertEqual(result["type"], "artifact")
        self.assertEqual(result["format"], "json")
        self.assertIsInstance(result["content"], list)
        
        # Check for expected visualization components
        self.assertEqual(len(result["content"]), 3)  # Summary card, bar chart, table
        
        # Check summary card
        summary_card = result["content"][0]
        self.assertEqual(summary_card["type"], "card")
        self.assertEqual(summary_card["title"], "Anomaly Detection Summary")
        
        # Check bar chart
        bar_chart = result["content"][1]
        self.assertEqual(bar_chart["type"], "bar")
        self.assertEqual(bar_chart["title"], "Anomalies by Metric")
        
        # Check table
        table = result["content"][2]
        self.assertEqual(table["type"], "table")
        self.assertEqual(table["title"], "Top Anomalies")
        self.assertEqual(len(table["rows"]), 2)
    
    def test_format_optimization_suggestions_visualization(self):
        """Test format_optimization_suggestions_visualization function."""
        # Sample data
        suggestions_data = {
            "suggestions": {
                "budget_allocation": [
                    {
                        "type": "INCREASE_BUDGET",
                        "entity_type": "CAMPAIGN",
                        "entity_id": "1",
                        "entity_name": "Campaign 1",
                        "suggestion": "Increase budget for campaign 'Campaign 1'",
                        "impact": "HIGH",
                        "action": "Consider increasing the budget by 10-20% to allow for growth"
                    }
                ],
                "bid_management": [
                    {
                        "type": "INCREASE_BID_HIGH_CONV",
                        "entity_type": "KEYWORD",
                        "entity_id": "1001",
                        "entity_text": "high converting keyword",
                        "suggestion": "Keyword 'high converting keyword' has strong conversion rate",
                        "impact": "MEDIUM",
                        "action": "Increase bid by 10-15% to capture more traffic"
                    }
                ],
                "negative_keywords": [
                    {
                        "type": "ADD_NEGATIVE_KEYWORD",
                        "entity_type": "SEARCH_TERM",
                        "entity_text": "irrelevant term",
                        "suggestion": "Add 'irrelevant term' as a negative keyword",
                        "impact": "MEDIUM",
                        "action": "Add as a negative exact match keyword"
                    }
                ],
                "ad_copy": [],
                "account_structure": []
            },
            "metadata": {
                "customer_id": "123456789",
                "entity_types": ["CAMPAIGN", "AD_GROUP", "KEYWORD"],
                "start_date": "2025-04-19",
                "end_date": "2025-05-19",
                "total_suggestions": 3
            }
        }
        
        # Call the function
        result = format_optimization_suggestions_visualization(suggestions_data)
        
        # Assertions
        self.assertEqual(result["type"], "artifact")
        self.assertEqual(result["format"], "json")
        self.assertIsInstance(result["content"], list)
        
        # Check for expected visualization components (at least summary card and pie chart)
        self.assertGreaterEqual(len(result["content"]), 2)
        
        # Check summary card
        summary_card = result["content"][0]
        self.assertEqual(summary_card["type"], "card")
        self.assertEqual(summary_card["title"], "Optimization Suggestions Summary")
        
        # Check pie chart
        pie_chart = result["content"][1]
        self.assertEqual(pie_chart["type"], "pie")
        self.assertEqual(pie_chart["title"], "Suggestions by Category")
    
    def test_format_opportunities_visualization(self):
        """Test format_opportunities_visualization function."""
        # Sample data
        opportunities_data = {
            "opportunities": {
                "keyword_expansion": [
                    {
                        "type": "ADD_KEYWORD_FROM_SEARCH_TERM",
                        "search_term": "test keyword",
                        "suggested_match_type": "EXACT",
                        "ad_group_name": "Ad Group 1",
                        "impressions": 500,
                        "clicks": 25,
                        "conversions": 2,
                        "opportunity": "Add 'test keyword' as a keyword",
                        "impact": "HIGH",
                        "action": "Add as an exact match keyword"
                    }
                ],
                "ad_variation": [
                    {
                        "type": "CREATE_AD_VARIATION",
                        "entity_type": "AD_GROUP",
                        "entity_name": "Ad Group 2",
                        "campaign_name": "Campaign 2",
                        "opportunity": "Create additional ad variations",
                        "impact": "MEDIUM",
                        "action": "Add at least one more responsive search ad"
                    }
                ],
                "structure": [],
                "audience": []
            },
            "metadata": {
                "customer_id": "123456789",
                "start_date": "2025-04-19",
                "end_date": "2025-05-19",
                "total_opportunities": 2
            }
        }
        
        # Call the function
        result = format_opportunities_visualization(opportunities_data)
        
        # Assertions
        self.assertEqual(result["type"], "artifact")
        self.assertEqual(result["format"], "json")
        self.assertIsInstance(result["content"], list)
        
        # Check for expected visualization components
        self.assertGreaterEqual(len(result["content"]), 2)
        
        # Check summary card
        summary_card = result["content"][0]
        self.assertEqual(summary_card["type"], "card")
        self.assertEqual(summary_card["title"], "Growth Opportunities Summary")
        
        # Check pie chart
        pie_chart = result["content"][1]
        self.assertEqual(pie_chart["type"], "pie")
        self.assertEqual(pie_chart["title"], "Opportunities by Category")
    
    def test_format_insights_visualization(self):
        """Test format_insights_visualization function."""
        # Sample data
        anomalies_data = {
            "anomalies": [
                {
                    "entity_type": "CAMPAIGN",
                    "entity_id": "1",
                    "entity_name": "Campaign 1",
                    "metric": "impressions",
                    "current_value": 1000,
                    "comparison_value": 800,
                    "percent_change": 25.0,
                    "direction": "INCREASE",
                    "severity": "MEDIUM"
                }
            ],
            "metadata": {
                "anomalies_detected": 1
            }
        }
        
        suggestions_data = {
            "suggestions": {
                "budget_allocation": [
                    {
                        "type": "INCREASE_BUDGET",
                        "entity_type": "CAMPAIGN",
                        "entity_id": "1",
                        "entity_name": "Campaign 1",
                        "suggestion": "Increase budget for campaign 'Campaign 1'",
                        "impact": "HIGH",
                        "action": "Consider increasing the budget by 10-20% to allow for growth"
                    }
                ],
                "bid_management": [],
                "negative_keywords": [],
                "ad_copy": [],
                "account_structure": []
            },
            "metadata": {
                "total_suggestions": 1
            }
        }
        
        opportunities_data = {
            "opportunities": {
                "keyword_expansion": [
                    {
                        "type": "ADD_KEYWORD_FROM_SEARCH_TERM",
                        "search_term": "test keyword",
                        "opportunity": "Add 'test keyword' as a keyword",
                        "impact": "HIGH"
                    }
                ],
                "ad_variation": [],
                "structure": [],
                "audience": []
            },
            "metadata": {
                "total_opportunities": 1
            }
        }
        
        # Call the function
        result = format_insights_visualization(anomalies_data, suggestions_data, opportunities_data)
        
        # Assertions
        self.assertEqual(result["type"], "artifact")
        self.assertEqual(result["format"], "json")
        self.assertIsInstance(result["content"], list)
        
        # Check for expected visualization components
        self.assertGreaterEqual(len(result["content"]), 2)  # At least summary card and tabs
        
        # Check summary card
        summary_card = result["content"][0]
        self.assertEqual(summary_card["type"], "card")
        self.assertEqual(summary_card["title"], "Account Insights Summary")
        
        # Check tabs
        tabs_component = result["content"][1]
        self.assertEqual(tabs_component["type"], "tabs")
        self.assertEqual(len(tabs_component["tabs"]), 3)  # One tab for each insight type 