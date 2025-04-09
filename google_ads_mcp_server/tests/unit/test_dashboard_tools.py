import unittest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime, timedelta

# Import services that the tools rely on
from google_ads_mcp_server.google_ads.dashboards import DashboardService

# Import the dashboard tools from the module
try:
    # First try to import directly from dashboard module (preferred future approach)
    from google_ads_mcp_server.mcp.tools.dashboard import (
        get_account_dashboard_json,
        get_campaign_dashboard_json,
        get_campaigns_comparison_json,
        get_performance_breakdown_json
    )
except ImportError:
    # As fallback, import from the main tools module (if re-exporting is used)
    from google_ads_mcp_server.mcp.tools import (
        get_account_dashboard_json,
        get_campaign_dashboard_json,
        get_campaigns_comparison_json,
        get_performance_breakdown_json
    )

# Mock visualization functions
@patch('google_ads_mcp_server.visualization.dashboards.create_account_dashboard_visualization')
@patch('google_ads_mcp_server.visualization.dashboards.create_campaign_dashboard_visualization')
class TestMCPDashboardTools(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.mock_dashboard_service = MagicMock(spec=DashboardService)
        
        # Sample account dashboard data for tests
        self.account_dashboard_data = {
            "account_name": "Test Account",
            "metrics": {
                "impressions": 50000,
                "clicks": 2500,
                "cost_micros": 5000000000,  # $5,000
                "conversions": 100,
                "conversion_value_micros": 20000000000  # $20,000
            },
            "time_series": [
                {
                    "date": "2025-03-01",
                    "impressions": 1500,
                    "clicks": 75,
                    "cost_micros": 150000000,  # $150
                    "conversions": 3
                },
                {
                    "date": "2025-03-02",
                    "impressions": 1600,
                    "clicks": 80,
                    "cost_micros": 160000000,  # $160
                    "conversions": 4
                }
            ],
            "campaigns": [
                {
                    "id": "1122334455",
                    "name": "Test Campaign 1",
                    "status": "ENABLED",
                    "budget_amount_micros": 1000000000,  # $1,000
                    "impressions": 30000,
                    "clicks": 1500,
                    "cost_micros": 3000000000,  # $3,000
                    "conversions": 60
                },
                {
                    "id": "2233445566",
                    "name": "Test Campaign 2",
                    "status": "ENABLED",
                    "budget_amount_micros": 500000000,  # $500
                    "impressions": 20000,
                    "clicks": 1000,
                    "cost_micros": 2000000000,  # $2,000
                    "conversions": 40
                }
            ],
            "ad_groups": [
                {
                    "id": "111222333",
                    "name": "Test Ad Group 1",
                    "campaign_id": "1122334455",
                    "campaign_name": "Test Campaign 1",
                    "status": "ENABLED",
                    "impressions": 15000,
                    "clicks": 750,
                    "cost_micros": 1500000000,  # $1,500
                    "conversions": 30
                },
                {
                    "id": "222333444",
                    "name": "Test Ad Group 2",
                    "campaign_id": "2233445566",
                    "campaign_name": "Test Campaign 2",
                    "status": "ENABLED",
                    "impressions": 10000,
                    "clicks": 500,
                    "cost_micros": 1000000000,  # $1,000
                    "conversions": 20
                }
            ]
        }
        
        # Sample campaign dashboard data for tests
        self.campaign_dashboard_data = {
            "id": "1122334455",
            "name": "Test Campaign 1",
            "status": "ENABLED",
            "budget_amount_micros": 1000000000,  # $1,000
            "metrics": {
                "impressions": 30000,
                "clicks": 1500,
                "cost_micros": 3000000000,  # $3,000
                "conversions": 60,
                "conversion_value_micros": 12000000000  # $12,000
            },
            "time_series": [
                {
                    "date": "2025-03-01",
                    "impressions": 1000,
                    "clicks": 50,
                    "cost_micros": 100000000,  # $100
                    "conversions": 2
                },
                {
                    "date": "2025-03-02",
                    "impressions": 1100,
                    "clicks": 55,
                    "cost_micros": 110000000,  # $110
                    "conversions": 3
                }
            ],
            "ad_groups": [
                {
                    "id": "111222333",
                    "name": "Test Ad Group 1",
                    "status": "ENABLED",
                    "impressions": 15000,
                    "clicks": 750,
                    "cost_micros": 1500000000,  # $1,500
                    "conversions": 30
                },
                {
                    "id": "222333444",
                    "name": "Test Ad Group 2",
                    "status": "ENABLED",
                    "impressions": 15000,
                    "clicks": 750,
                    "cost_micros": 1500000000,  # $1,500
                    "conversions": 30
                }
            ],
            "device_performance": [
                {
                    "device": "MOBILE",
                    "impressions": 15000,
                    "clicks": 750,
                    "cost_micros": 1500000000,  # $1,500
                    "conversions": 30
                },
                {
                    "device": "DESKTOP",
                    "impressions": 10000,
                    "clicks": 500,
                    "cost_micros": 1000000000,  # $1,000
                    "conversions": 20
                },
                {
                    "device": "TABLET",
                    "impressions": 5000,
                    "clicks": 250,
                    "cost_micros": 500000000,  # $500
                    "conversions": 10
                }
            ],
            "keywords": [
                {
                    "id": "12345",
                    "text": "test keyword 1",
                    "match_type": "EXACT",
                    "ad_group_id": "111222333",
                    "ad_group_name": "Test Ad Group 1",
                    "status": "ENABLED",
                    "impressions": 7500,
                    "clicks": 375,
                    "cost_micros": 750000000,  # $750
                    "conversions": 15
                },
                {
                    "id": "23456",
                    "text": "test keyword 2",
                    "match_type": "BROAD",
                    "ad_group_id": "222333444",
                    "ad_group_name": "Test Ad Group 2",
                    "status": "ENABLED",
                    "impressions": 7500,
                    "clicks": 375,
                    "cost_micros": 750000000,  # $750
                    "conversions": 15
                }
            ]
        }
        
        # Sample campaigns comparison data for tests
        self.campaigns_comparison_data = {
            "campaigns": [
                {
                    "id": "1122334455",
                    "name": "Test Campaign 1",
                    "status": "ENABLED",
                    "impressions": 30000,
                    "clicks": 1500,
                    "cost_micros": 3000000000,  # $3,000
                    "conversions": 60,
                    "ctr": 0.05,  # 5%
                    "average_cpc": 2000000,  # $2
                    "conversion_rate": 0.04,  # 4%
                    "cost_per_conversion": 50000000  # $50
                },
                {
                    "id": "2233445566",
                    "name": "Test Campaign 2",
                    "status": "ENABLED",
                    "impressions": 20000,
                    "clicks": 1000,
                    "cost_micros": 2000000000,  # $2,000
                    "conversions": 40,
                    "ctr": 0.05,  # 5%
                    "average_cpc": 2000000,  # $2
                    "conversion_rate": 0.04,  # 4%
                    "cost_per_conversion": 50000000  # $50
                }
            ],
            "metrics": [
                "impressions", 
                "clicks", 
                "cost_micros", 
                "conversions", 
                "ctr", 
                "average_cpc", 
                "conversion_rate", 
                "cost_per_conversion"
            ],
            "date_range": "LAST_30_DAYS"
        }
        
        # Sample performance breakdown data for tests
        self.performance_breakdown_data = {
            "entity_type": "campaign",
            "entity_id": "1122334455",
            "entity_name": "Test Campaign 1",
            "dimensions": ["device", "day"],
            "date_range": "LAST_30_DAYS",
            "data": [
                {
                    "dimension": "device",
                    "segments": [
                        {
                            "device": "MOBILE",
                            "impressions": 15000,
                            "clicks": 750,
                            "cost_micros": 1500000000,  # $1,500
                            "conversions": 30
                        },
                        {
                            "device": "DESKTOP",
                            "impressions": 10000,
                            "clicks": 500,
                            "cost_micros": 1000000000,  # $1,000
                            "conversions": 20
                        },
                        {
                            "device": "TABLET",
                            "impressions": 5000,
                            "clicks": 250,
                            "cost_micros": 500000000,  # $500
                            "conversions": 10
                        }
                    ]
                },
                {
                    "dimension": "day",
                    "segments": [
                        {
                            "day": "2025-03-01",
                            "impressions": 10000,
                            "clicks": 500,
                            "cost_micros": 1000000000,  # $1,000
                            "conversions": 20
                        },
                        {
                            "day": "2025-03-02",
                            "impressions": 10000,
                            "clicks": 500,
                            "cost_micros": 1000000000,  # $1,000
                            "conversions": 20
                        },
                        {
                            "day": "2025-03-03",
                            "impressions": 10000,
                            "clicks": 500,
                            "cost_micros": 1000000000,  # $1,000
                            "conversions": 20
                        }
                    ]
                }
            ]
        }

    def test_get_account_dashboard_json(self, mock_campaign_viz, mock_account_viz):
        """Test the get_account_dashboard_json MCP tool."""
        # Arrange
        customer_id = "123-456-7890"
        date_range = "LAST_30_DAYS"
        comparison_range = "PREVIOUS_30_DAYS"
        
        self.mock_dashboard_service.get_account_dashboard.return_value = self.account_dashboard_data
        mock_account_viz.return_value = {"charts": [{"type": "line"}], "tables": [{"data": "dummy"}]}
        
        # Act
        with patch('google_ads_mcp_server.mcp.tools.dashboard.dashboard_service', self.mock_dashboard_service):
            result = get_account_dashboard_json(
                customer_id=customer_id,
                date_range=date_range,
                comparison_range=comparison_range
            )
        
        # Assert
        self.mock_dashboard_service.get_account_dashboard.assert_called_once_with(
            customer_id="1234567890",  # Dashes removed
            date_range=date_range,
            comparison_range=comparison_range
        )
        mock_account_viz.assert_called_once_with(account_data=self.account_dashboard_data)
        
        # Check result structure
        self.assertEqual(result["type"], "success")
        self.assertEqual(result["data"]["customer_id"], "123-456-7890")
        self.assertEqual(result["data"]["date_range"], date_range)
        self.assertEqual(result["data"]["comparison_range"], comparison_range)
        self.assertEqual(result["data"]["account_name"], "Test Account")
        self.assertEqual(result["data"]["metrics"], self.account_dashboard_data["metrics"])
        self.assertEqual(result["data"]["time_series"], self.account_dashboard_data["time_series"])
        self.assertEqual(result["data"]["campaigns"], self.account_dashboard_data["campaigns"])
        self.assertEqual(result["data"]["ad_groups"], self.account_dashboard_data["ad_groups"])
        self.assertEqual(result["visualization"], mock_account_viz.return_value)

    def test_get_account_dashboard_json_error_handling(self, mock_campaign_viz, mock_account_viz):
        """Test get_account_dashboard_json error handling."""
        # Arrange
        customer_id = "123-456-7890"
        self.mock_dashboard_service.get_account_dashboard.return_value = {"error": "API Error"}
        
        # Act
        with patch('google_ads_mcp_server.mcp.tools.dashboard.dashboard_service', self.mock_dashboard_service):
            result = get_account_dashboard_json(customer_id=customer_id)
        
        # Assert
        self.assertEqual(result["type"], "error")
        self.assertIn("Error: API Error", result["message"])
        mock_account_viz.assert_not_called()

    def test_get_campaign_dashboard_json(self, mock_campaign_viz, mock_account_viz):
        """Test the get_campaign_dashboard_json MCP tool."""
        # Arrange
        customer_id = "123-456-7890"
        campaign_id = "1122334455"
        date_range = "LAST_30_DAYS"
        comparison_range = "PREVIOUS_30_DAYS"
        
        self.mock_dashboard_service.get_campaign_dashboard.return_value = self.campaign_dashboard_data
        mock_campaign_viz.return_value = {"charts": [{"type": "line"}], "tables": [{"data": "dummy"}]}
        
        # Act
        with patch('google_ads_mcp_server.mcp.tools.dashboard.dashboard_service', self.mock_dashboard_service):
            result = get_campaign_dashboard_json(
                customer_id=customer_id,
                campaign_id=campaign_id,
                date_range=date_range,
                comparison_range=comparison_range
            )
        
        # Assert
        self.mock_dashboard_service.get_campaign_dashboard.assert_called_once_with(
            customer_id="1234567890",  # Dashes removed
            campaign_id=campaign_id,
            date_range=date_range,
            comparison_range=comparison_range
        )
        mock_campaign_viz.assert_called_once_with(campaign_data=self.campaign_dashboard_data)
        
        # Check result structure
        self.assertEqual(result["type"], "success")
        self.assertEqual(result["data"]["customer_id"], "123-456-7890")
        self.assertEqual(result["data"]["campaign_id"], campaign_id)
        self.assertEqual(result["data"]["campaign_name"], "Test Campaign 1")
        self.assertEqual(result["data"]["date_range"], date_range)
        self.assertEqual(result["data"]["comparison_range"], comparison_range)
        self.assertEqual(result["data"]["metrics"], self.campaign_dashboard_data["metrics"])
        self.assertEqual(result["data"]["time_series"], self.campaign_dashboard_data["time_series"])
        self.assertEqual(result["data"]["ad_groups"], self.campaign_dashboard_data["ad_groups"])
        self.assertEqual(result["data"]["device_performance"], self.campaign_dashboard_data["device_performance"])
        self.assertEqual(result["data"]["keywords"], self.campaign_dashboard_data["keywords"])
        self.assertEqual(result["visualization"], mock_campaign_viz.return_value)

    def test_get_campaign_dashboard_json_error_handling(self, mock_campaign_viz, mock_account_viz):
        """Test get_campaign_dashboard_json error handling."""
        # Arrange
        customer_id = "123-456-7890"
        campaign_id = "1122334455"
        self.mock_dashboard_service.get_campaign_dashboard.return_value = {"error": "API Error"}
        
        # Act
        with patch('google_ads_mcp_server.mcp.tools.dashboard.dashboard_service', self.mock_dashboard_service):
            result = get_campaign_dashboard_json(
                customer_id=customer_id,
                campaign_id=campaign_id
            )
        
        # Assert
        self.assertEqual(result["type"], "error")
        self.assertIn("Error: API Error", result["message"])
        mock_campaign_viz.assert_not_called()

    def test_get_campaigns_comparison_json(self, mock_campaign_viz, mock_account_viz):
        """Test the get_campaigns_comparison_json MCP tool."""
        # Arrange
        customer_id = "123-456-7890"
        campaign_ids = "1122334455,2233445566"
        date_range = "LAST_30_DAYS"
        metrics = "impressions,clicks,cost_micros,conversions"
        
        self.mock_dashboard_service.get_campaigns_comparison.return_value = self.campaigns_comparison_data
        
        # Act
        with patch('google_ads_mcp_server.mcp.tools.dashboard.dashboard_service', self.mock_dashboard_service):
            result = get_campaigns_comparison_json(
                customer_id=customer_id,
                campaign_ids=campaign_ids,
                date_range=date_range,
                metrics=metrics
            )
        
        # Assert
        self.mock_dashboard_service.get_campaigns_comparison.assert_called_once_with(
            customer_id="1234567890",  # Dashes removed
            campaign_ids=["1122334455", "2233445566"],
            date_range=date_range,
            metrics=["impressions", "clicks", "cost_micros", "conversions"]
        )
        
        # Check result structure
        self.assertEqual(result["type"], "success")
        self.assertEqual(result["data"]["customer_id"], "123-456-7890")
        self.assertEqual(result["data"]["date_range"], date_range)
        self.assertEqual(result["data"]["campaigns"], self.campaigns_comparison_data["campaigns"])
        self.assertEqual(result["data"]["metrics"], self.campaigns_comparison_data["metrics"])
        
        # Check visualization structure
        self.assertIn("title", result["visualization"])
        self.assertIn("description", result["visualization"])
        self.assertIn("charts", result["visualization"])
        self.assertIn("table", result["visualization"])
        
        # Charts exist for the metrics
        self.assertEqual(len(result["visualization"]["charts"]), 4)  # Limited to top 4 metrics

    def test_get_campaigns_comparison_json_error_handling(self, mock_campaign_viz, mock_account_viz):
        """Test get_campaigns_comparison_json error handling."""
        # Arrange
        customer_id = "123-456-7890"
        campaign_ids = "1122334455,2233445566"
        self.mock_dashboard_service.get_campaigns_comparison.return_value = {"error": "API Error"}
        
        # Act
        with patch('google_ads_mcp_server.mcp.tools.dashboard.dashboard_service', self.mock_dashboard_service):
            result = get_campaigns_comparison_json(
                customer_id=customer_id,
                campaign_ids=campaign_ids
            )
        
        # Assert
        self.assertEqual(result["type"], "error")
        self.assertIn("Error: API Error", result["message"])

    def test_get_performance_breakdown_json(self, mock_campaign_viz, mock_account_viz):
        """Test the get_performance_breakdown_json MCP tool."""
        # Arrange
        customer_id = "123-456-7890"
        entity_type = "campaign"
        entity_id = "1122334455"
        dimensions = "device,day"
        date_range = "LAST_30_DAYS"
        
        self.mock_dashboard_service.get_performance_breakdown.return_value = self.performance_breakdown_data
        
        # Act
        with patch('google_ads_mcp_server.mcp.tools.dashboard.dashboard_service', self.mock_dashboard_service):
            result = get_performance_breakdown_json(
                customer_id=customer_id,
                entity_type=entity_type,
                entity_id=entity_id,
                dimensions=dimensions,
                date_range=date_range
            )
        
        # Assert
        self.mock_dashboard_service.get_performance_breakdown.assert_called_once_with(
            customer_id="1234567890",  # Dashes removed
            entity_type=entity_type,
            entity_id=entity_id,
            dimensions=["device", "day"],
            date_range=date_range
        )
        
        # Check result structure
        self.assertEqual(result["type"], "success")
        self.assertEqual(result["data"]["customer_id"], "123-456-7890")
        self.assertEqual(result["data"]["entity_type"], entity_type)
        self.assertEqual(result["data"]["entity_id"], entity_id)
        self.assertEqual(result["data"]["entity_name"], "Test Campaign 1")
        self.assertEqual(result["data"]["date_range"], date_range)
        self.assertEqual(result["data"]["dimensions"], ["device", "day"])
        self.assertEqual(result["data"]["breakdown_data"], self.performance_breakdown_data["data"])
        
        # Check visualization structure
        self.assertIn("title", result["visualization"])
        self.assertIn("description", result["visualization"])
        self.assertIn("charts", result["visualization"])
        
        # There should be charts for both dimensions (device and day)
        # For device: cost pie chart + clicks pie chart
        # For day: 4 line charts (impressions, clicks, cost, conversions)
        self.assertEqual(len(result["visualization"]["charts"]), 6)

    def test_get_performance_breakdown_json_invalid_entity_type(self, mock_campaign_viz, mock_account_viz):
        """Test get_performance_breakdown_json with invalid entity type."""
        # Arrange
        customer_id = "123-456-7890"
        entity_type = "invalid_type"  # Invalid entity type
        
        # Act
        with patch('google_ads_mcp_server.mcp.tools.dashboard.dashboard_service', self.mock_dashboard_service):
            result = get_performance_breakdown_json(
                customer_id=customer_id,
                entity_type=entity_type
            )
        
        # Assert
        self.assertEqual(result["type"], "error")
        self.assertIn("Invalid entity_type", result["message"])
        self.mock_dashboard_service.get_performance_breakdown.assert_not_called()

    def test_get_performance_breakdown_json_missing_entity_id(self, mock_campaign_viz, mock_account_viz):
        """Test get_performance_breakdown_json with missing entity ID."""
        # Arrange
        customer_id = "123-456-7890"
        entity_type = "campaign"
        entity_id = None  # Missing entity ID for campaign
        
        # Act
        with patch('google_ads_mcp_server.mcp.tools.dashboard.dashboard_service', self.mock_dashboard_service):
            result = get_performance_breakdown_json(
                customer_id=customer_id,
                entity_type=entity_type,
                entity_id=entity_id
            )
        
        # Assert
        self.assertEqual(result["type"], "error")
        self.assertIn("entity_id is required", result["message"])
        self.mock_dashboard_service.get_performance_breakdown.assert_not_called()

    def test_get_performance_breakdown_json_error_handling(self, mock_campaign_viz, mock_account_viz):
        """Test get_performance_breakdown_json error handling."""
        # Arrange
        customer_id = "123-456-7890"
        entity_type = "campaign"
        entity_id = "1122334455"
        self.mock_dashboard_service.get_performance_breakdown.return_value = {"error": "API Error"}
        
        # Act
        with patch('google_ads_mcp_server.mcp.tools.dashboard.dashboard_service', self.mock_dashboard_service):
            result = get_performance_breakdown_json(
                customer_id=customer_id,
                entity_type=entity_type,
                entity_id=entity_id
            )
        
        # Assert
        self.assertEqual(result["type"], "error")
        self.assertIn("Error: API Error", result["message"])

if __name__ == '__main__':
    unittest.main() 