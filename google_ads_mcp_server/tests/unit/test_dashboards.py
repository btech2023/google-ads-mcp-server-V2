import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta

# Import the visualization functions
from google_ads_mcp_server.visualization.dashboards import (
    create_kpi_cards,
    create_trend_chart,
    create_top_performers_table,
    create_donut_chart,
    create_account_dashboard_visualization,
    create_campaign_dashboard_visualization,
    _format_currency,
    _format_percentage,
    _calculate_change
)


class TestDashboardVisualizations(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample metrics data for testing
        self.metrics_data = {
            "cost_micros": 50000000,  # $50
            "impressions": 10000,
            "clicks": 500,
            "conversions": 25,
            "ctr": 0.05,  # Will be calculated if not present
            "average_cpc": 100000,  # $0.10, will be calculated if not present
        }
        
        # Sample comparison metrics
        self.comparison_metrics = {
            "cost_micros": 45000000,  # $45
            "impressions": 9000,
            "clicks": 400,
            "conversions": 20,
        }
        
        # Sample time series data
        self.time_series_data = [
            {
                "date": "2025-04-01",
                "cost_micros": 5000000,
                "impressions": 1000,
                "clicks": 50,
                "conversions": 2
            },
            {
                "date": "2025-04-02",
                "cost_micros": 6000000,
                "impressions": 1200,
                "clicks": 60,
                "conversions": 3
            },
            {
                "date": "2025-04-03",
                "cost_micros": 5500000,
                "impressions": 1100,
                "clicks": 55,
                "conversions": 3
            }
        ]
        
        # Sample campaign data
        self.campaign_data = [
            {
                "id": 123,
                "name": "Campaign 1",
                "status": "ENABLED",
                "budget_amount_micros": 10000000,
                "cost_micros": 8000000,
                "impressions": 2000,
                "clicks": 100,
                "conversions": 5
            },
            {
                "id": 456,
                "name": "Campaign 2",
                "status": "ENABLED",
                "budget_amount_micros": 20000000,
                "cost_micros": 15000000,
                "impressions": 3000,
                "clicks": 150,
                "conversions": 8
            }
        ]
        
        # Sample ad group data
        self.ad_group_data = [
            {
                "id": 789,
                "name": "Ad Group 1",
                "campaign_name": "Campaign 1",
                "status": "ENABLED",
                "cost_micros": 5000000,
                "impressions": 1000,
                "clicks": 50,
                "conversions": 3
            },
            {
                "id": 012,
                "name": "Ad Group 2",
                "campaign_name": "Campaign 1",
                "status": "ENABLED",
                "cost_micros": 3000000,
                "impressions": 800,
                "clicks": 40,
                "conversions": 2
            }
        ]
        
        # Sample campaign dashboard data
        self.campaign_dashboard_data = {
            "id": 123,
            "name": "Test Campaign",
            "status": "ENABLED",
            "budget_amount_micros": 10000000,
            "budget_utilization": 0.8,
            "type": "SEARCH",
            "start_date": "2025-01-01",
            "end_date": None,
            "metrics": self.metrics_data,
            "time_series": self.time_series_data,
            "ad_groups": self.ad_group_data,
            "device_performance": [
                {
                    "device": "MOBILE",
                    "cost_micros": 30000000,
                    "impressions": 6000,
                    "clicks": 300,
                    "conversions": 15
                },
                {
                    "device": "DESKTOP",
                    "cost_micros": 20000000,
                    "impressions": 4000,
                    "clicks": 200,
                    "conversions": 10
                }
            ],
            "keywords": [
                {
                    "id": 111,
                    "text": "test keyword 1",
                    "match_type": "EXACT",
                    "ad_group_name": "Ad Group 1",
                    "cost_micros": 2000000,
                    "impressions": 400,
                    "clicks": 20,
                    "conversions": 1
                },
                {
                    "id": 222,
                    "text": "test keyword 2",
                    "match_type": "PHRASE",
                    "ad_group_name": "Ad Group 2",
                    "cost_micros": 1500000,
                    "impressions": 300,
                    "clicks": 15,
                    "conversions": 1
                }
            ]
        }
        
        # Sample account dashboard data
        self.account_dashboard_data = {
            "metrics": self.metrics_data,
            "time_series": self.time_series_data,
            "campaigns": self.campaign_data,
            "ad_groups": self.ad_group_data,
            "comparison_metrics": self.comparison_metrics
        }

    def test_format_currency(self):
        """Test the currency formatting helper function."""
        self.assertEqual(_format_currency(1000000), 1.0)
        self.assertEqual(_format_currency(10000000), 10.0)
        self.assertEqual(_format_currency(1500000), 1.5)
        self.assertEqual(_format_currency(0), 0.0)

    def test_format_percentage(self):
        """Test the percentage formatting helper function."""
        self.assertEqual(_format_percentage(0.1), 10.0)
        self.assertEqual(_format_percentage(0.055), 5.5)
        self.assertEqual(_format_percentage(1.0), 100.0)
        self.assertEqual(_format_percentage(0), 0.0)

    def test_calculate_change(self):
        """Test the change calculation helper function."""
        # Positive change
        change = _calculate_change(110, 100)
        self.assertEqual(change["absolute"], 10)
        self.assertEqual(change["percentage"], 10.0)
        self.assertEqual(change["direction"], "up")
        
        # Negative change
        change = _calculate_change(90, 100)
        self.assertEqual(change["absolute"], -10)
        self.assertEqual(change["percentage"], -10.0)
        self.assertEqual(change["direction"], "down")
        
        # No change
        change = _calculate_change(100, 100)
        self.assertEqual(change["absolute"], 0)
        self.assertEqual(change["percentage"], 0.0)
        self.assertEqual(change["direction"], "unchanged")
        
        # From zero
        change = _calculate_change(100, 0)
        self.assertEqual(change["absolute"], 100)
        self.assertEqual(change["percentage"], 100.0)
        self.assertEqual(change["direction"], "up")
        
        # To zero
        change = _calculate_change(0, 100)
        self.assertEqual(change["absolute"], -100)
        self.assertEqual(change["percentage"], -100.0)
        self.assertEqual(change["direction"], "down")
        
        # Zero to zero
        change = _calculate_change(0, 0)
        self.assertEqual(change["absolute"], 0)
        self.assertEqual(change["percentage"], 0.0)
        self.assertEqual(change["direction"], "unchanged")

    def test_create_kpi_cards(self):
        """Test the KPI cards creation function."""
        # Test with metrics only (no comparison)
        kpi_cards = create_kpi_cards(self.metrics_data)
        
        # Check we have the right number of cards
        self.assertGreaterEqual(len(kpi_cards), 4)  # At least cost, impressions, clicks, conversions
        
        # Check specific cards
        cost_card = next((card for card in kpi_cards if card["name"] == "Cost"), None)
        self.assertIsNotNone(cost_card)
        self.assertEqual(cost_card["value"], 50.0)
        self.assertEqual(cost_card["display_value"], "$50.00")
        
        # Test with comparison metrics
        kpi_cards = create_kpi_cards(self.metrics_data, self.comparison_metrics)
        
        # Check comparison data is included
        cost_card = next((card for card in kpi_cards if card["name"] == "Cost"), None)
        self.assertIsNotNone(cost_card)
        self.assertIn("comparison", cost_card)
        self.assertEqual(cost_card["comparison"]["value"], 45.0)
        self.assertEqual(cost_card["comparison"]["change"]["percentage"], 11.11)
        self.assertEqual(cost_card["comparison"]["change"]["direction"], "up")
        
        # Test derived metrics (CTR, CPC, etc.)
        impressions_card = next((card for card in kpi_cards if card["name"] == "Impressions"), None)
        self.assertIsNotNone(impressions_card)
        self.assertEqual(impressions_card["value"], 10000)
        
        ctr_card = next((card for card in kpi_cards if card["name"] == "CTR"), None)
        self.assertIsNotNone(ctr_card)
        self.assertEqual(ctr_card["value"], 0.05)
        self.assertEqual(ctr_card["display_value"], "5.00%")

    def test_create_trend_chart(self):
        """Test the trend chart creation function."""
        # Test with a single metric
        chart = create_trend_chart(
            self.time_series_data,
            ["cost_micros"],
            "Cost Trend"
        )
        
        # Check chart structure
        self.assertEqual(chart["type"], "line")
        self.assertEqual(chart["title"], "Cost Trend")
        self.assertIn("data", chart)
        self.assertIn("labels", chart["data"])
        self.assertIn("datasets", chart["data"])
        
        # Check data content
        self.assertEqual(len(chart["data"]["labels"]), 3)  # 3 dates
        self.assertEqual(len(chart["data"]["datasets"]), 1)  # 1 metric
        self.assertEqual(chart["data"]["datasets"][0]["label"], "Cost")
        self.assertEqual(len(chart["data"]["datasets"][0]["data"]), 3)  # 3 data points
        
        # Check values are correctly formatted (from micros to dollars)
        self.assertEqual(chart["data"]["datasets"][0]["data"][0], 5.0)
        self.assertEqual(chart["data"]["datasets"][0]["data"][1], 6.0)
        self.assertEqual(chart["data"]["datasets"][0]["data"][2], 5.5)
        
        # Test with multiple metrics
        chart = create_trend_chart(
            self.time_series_data,
            ["impressions", "clicks"],
            "Engagement Trend"
        )
        
        # Check multiple datasets
        self.assertEqual(len(chart["data"]["datasets"]), 2)
        self.assertEqual(chart["data"]["datasets"][0]["label"], "Impressions")
        self.assertEqual(chart["data"]["datasets"][1]["label"], "Clicks")

    def test_create_top_performers_table(self):
        """Test the top performers table creation function."""
        # Test with campaigns
        table = create_top_performers_table(
            self.campaign_data,
            "campaigns",
            "cost_micros",
            "Top Campaigns by Spend"
        )
        
        # Check table structure
        self.assertEqual(table["title"], "Top Campaigns by Spend")
        self.assertIn("headers", table)
        self.assertIn("rows", table)
        
        # Check headers are correct for campaigns
        self.assertEqual(len(table["headers"]), 4)
        self.assertEqual(table["headers"][0], "Campaign")
        self.assertEqual(table["headers"][1], "Budget")
        self.assertEqual(table["headers"][2], "Status")
        self.assertEqual(table["headers"][3], "Cost Micros")
        
        # Check rows
        self.assertEqual(len(table["rows"]), 2)  # 2 campaigns
        
        # Check sorting (highest cost first)
        self.assertEqual(table["rows"][0][0], "Campaign 2")  # Name
        self.assertEqual(table["rows"][0][1], "$20.00")  # Budget
        self.assertEqual(table["rows"][0][2], "ENABLED")  # Status
        self.assertEqual(table["rows"][0][3], "$15.00")  # Cost
        
        # Test with ad groups
        table = create_top_performers_table(
            self.ad_group_data,
            "ad_groups",
            "conversions",
            "Top Ad Groups by Conversions"
        )
        
        # Check headers are correct for ad groups
        self.assertEqual(len(table["headers"]), 4)
        self.assertEqual(table["headers"][0], "Ad Group")
        self.assertEqual(table["headers"][1], "Campaign")
        
        # Check rows
        self.assertEqual(len(table["rows"]), 2)  # 2 ad groups
        self.assertEqual(table["rows"][0][0], "Ad Group 1")  # Name
        self.assertEqual(table["rows"][0][1], "Campaign 1")  # Campaign
        self.assertEqual(table["rows"][0][3], "3")  # Conversions

    def test_create_donut_chart(self):
        """Test the donut chart creation function."""
        chart = create_donut_chart(
            self.campaign_data,
            "name",
            "cost_micros",
            "Cost Distribution by Campaign"
        )
        
        # Check chart structure
        self.assertEqual(chart["type"], "doughnut")
        self.assertEqual(chart["title"], "Cost Distribution by Campaign")
        self.assertIn("data", chart)
        self.assertIn("labels", chart["data"])
        self.assertIn("datasets", chart["data"])
        
        # Check labels and data
        self.assertEqual(len(chart["data"]["labels"]), 2)  # 2 campaigns
        self.assertEqual(chart["data"]["labels"][0], "Campaign 1")
        self.assertEqual(chart["data"]["labels"][1], "Campaign 2")
        
        self.assertEqual(len(chart["data"]["datasets"]), 1)
        self.assertEqual(len(chart["data"]["datasets"][0]["data"]), 2)
        self.assertEqual(chart["data"]["datasets"][0]["data"][0], 8.0)  # $8
        self.assertEqual(chart["data"]["datasets"][0]["data"][1], 15.0)  # $15
        
        # Check colors
        self.assertGreaterEqual(len(chart["data"]["datasets"][0]["backgroundColor"]), 2)

    def test_create_account_dashboard_visualization(self):
        """Test the account dashboard visualization function."""
        dashboard = create_account_dashboard_visualization(self.account_dashboard_data)
        
        # Check dashboard structure
        self.assertIn("charts", dashboard)
        self.assertIn("tables", dashboard)
        
        # Check KPI cards
        kpi_table = next((table for table in dashboard["tables"] if table.get("type") == "kpi_cards"), None)
        self.assertIsNotNone(kpi_table)
        self.assertIn("cards", kpi_table)
        self.assertGreaterEqual(len(kpi_table["cards"]), 4)
        
        # Check charts
        self.assertGreaterEqual(len(dashboard["charts"]), 3)  # At least 3 charts
        
        # Check for cost trend chart
        cost_trend = next((chart for chart in dashboard["charts"] if chart["title"] == "Cost Trend"), None)
        self.assertIsNotNone(cost_trend)
        
        # Check for campaign distribution chart
        distribution_chart = next((chart for chart in dashboard["charts"] if "Distribution" in chart["title"]), None)
        self.assertIsNotNone(distribution_chart)
        
        # Check tables
        self.assertGreaterEqual(len(dashboard["tables"]), 2)  # KPI cards + at least 1 more table
        
        # Check for top campaigns table
        campaigns_table = next((table for table in dashboard["tables"] if "Top Campaigns" in table["title"]), None)
        self.assertIsNotNone(campaigns_table)

    def test_create_campaign_dashboard_visualization(self):
        """Test the campaign dashboard visualization function."""
        dashboard = create_campaign_dashboard_visualization(self.campaign_dashboard_data)
        
        # Check dashboard structure
        self.assertIn("charts", dashboard)
        self.assertIn("tables", dashboard)
        
        # Check campaign info
        campaign_info = next((table for table in dashboard["tables"] if "Campaign:" in table["title"]), None)
        self.assertIsNotNone(campaign_info)
        self.assertEqual(len(campaign_info["rows"]), 7)  # ID, Status, Budget, Utilization, Type, Start, End
        
        # Check KPI cards
        kpi_table = next((table for table in dashboard["tables"] if table.get("type") == "kpi_cards"), None)
        self.assertIsNotNone(kpi_table)
        
        # Check charts
        self.assertGreaterEqual(len(dashboard["charts"]), 3)  # At least 3 charts
        
        # Check for performance trend chart
        perf_trend = next((chart for chart in dashboard["charts"] if "Performance" in chart["title"]), None)
        self.assertIsNotNone(perf_trend)
        
        # Check device breakdown
        device_chart = next((chart for chart in dashboard["charts"] if "Device" in chart["title"]), None)
        self.assertIsNotNone(device_chart)
        
        # Check tables
        self.assertGreaterEqual(len(dashboard["tables"]), 3)  # Campaign info, KPI cards, at least 1 more
        
        # Check for ad groups table
        ad_groups_table = next((table for table in dashboard["tables"] if "Ad Groups" in table["title"]), None)
        self.assertIsNotNone(ad_groups_table)
        
        # Check for device table
        device_table = next((table for table in dashboard["tables"] if "Device" in table["title"]), None)
        self.assertIsNotNone(device_table)
        self.assertEqual(len(device_table["rows"]), 2)  # Mobile and Desktop

    def test_create_account_dashboard_with_comparison(self):
        """Test account dashboard with comparison data."""
        dashboard = create_account_dashboard_visualization(
            self.account_dashboard_data,
            self.account_dashboard_data.get("comparison_metrics")
        )
        
        # Check KPI cards have comparison data
        kpi_table = next((table for table in dashboard["tables"] if table.get("type") == "kpi_cards"), None)
        self.assertIsNotNone(kpi_table)
        
        cost_card = next((card for card in kpi_table["cards"] if card["name"] == "Cost"), None)
        self.assertIsNotNone(cost_card)
        self.assertIn("comparison", cost_card)
        self.assertIn("change", cost_card["comparison"])
        self.assertIn("percentage", cost_card["comparison"]["change"])


if __name__ == '__main__':
    unittest.main() 