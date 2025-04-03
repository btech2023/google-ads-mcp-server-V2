import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

from google_ads_mcp_server.visualization.comparisons import (
    format_bar_chart,
    format_pie_chart,
    create_comparison_bar_chart,
    create_comparison_data_table,
    create_comparison_radar_chart,
    format_comparison_visualization,
    _format_currency_micros,
    _format_percentage,
    _calculate_change
)


class TestComparisonVisualizations(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample entity data for testing
        self.campaign_data = [
            {
                "id": 123,
                "name": "Campaign 1",
                "status": "ENABLED",
                "budget_amount_micros": 10000000,
                "cost_micros": 8000000,
                "impressions": 2000,
                "clicks": 100,
                "conversions": 5,
                "ctr": 0.05
            },
            {
                "id": 456,
                "name": "Campaign 2",
                "status": "ENABLED",
                "budget_amount_micros": 20000000,
                "cost_micros": 15000000,
                "impressions": 3000,
                "clicks": 150,
                "conversions": 8,
                "ctr": 0.05
            }
        ]
        
        # Metrics to test with
        self.metrics = ["cost_micros", "clicks", "conversions"]
        
        # Sample comparison data structure
        self.comparison_data = {
            "campaigns": self.campaign_data,
            "metrics": self.metrics,
            "date_range": "LAST_30_DAYS"
        }

    def test_format_currency_micros(self):
        """Test the currency formatting helper function."""
        self.assertEqual(_format_currency_micros(1000000), 1.0)
        self.assertEqual(_format_currency_micros(10000000), 10.0)
        self.assertEqual(_format_currency_micros(1500000), 1.5)
        self.assertEqual(_format_currency_micros(0), 0.0)
        self.assertEqual(_format_currency_micros(None), 0.0)

    def test_format_percentage(self):
        """Test the percentage formatting helper function."""
        self.assertEqual(_format_percentage(0.1), 10.0)
        self.assertEqual(_format_percentage(0.055), 5.5)
        self.assertEqual(_format_percentage(1.0), 100.0)
        self.assertEqual(_format_percentage(0), 0.0)
        self.assertEqual(_format_percentage(None), 0.0)

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

    def test_format_bar_chart(self):
        """Test the original bar chart formatting function."""
        # Test with specific metrics
        chart = format_bar_chart(
            data=self.campaign_data,
            metrics=["impressions", "clicks"],
            category_key="name",
            title="Test Bar Chart"
        )
        
        # Check chart structure
        self.assertEqual(chart["chart_type"], "bar")
        self.assertEqual(chart["title"], "Test Bar Chart")
        self.assertEqual(len(chart["data"]), 2)  # 2 campaigns
        self.assertEqual(len(chart["series"]), 2)  # 2 metrics
        
        # Check series names
        self.assertEqual(chart["series"][0]["name"], "Impressions")
        self.assertEqual(chart["series"][1]["name"], "Clicks")
        
        # Test with empty data
        empty_chart = format_bar_chart(
            data=[],
            metrics=["impressions", "clicks"],
            title="Empty Chart"
        )
        self.assertEqual(empty_chart["title"], "Empty Chart")
        self.assertEqual(len(empty_chart["data"]), 0)
        self.assertEqual(len(empty_chart["series"]), 0)

    def test_format_pie_chart(self):
        """Test the original pie chart formatting function."""
        # Test with specific metric
        chart = format_pie_chart(
            data=self.campaign_data,
            metric="cost_micros",
            category_key="name",
            title="Test Pie Chart"
        )
        
        # Check chart structure
        self.assertEqual(chart["chart_type"], "pie")
        self.assertEqual(chart["title"], "Test Pie Chart")
        self.assertEqual(len(chart["data"]), 2)  # 2 campaigns
        
        # Check data values
        self.assertEqual(chart["data"][0]["name"], "Campaign 2")  # Sorted by value
        self.assertEqual(chart["data"][0]["value"], 15000000)
        self.assertEqual(chart["data"][1]["name"], "Campaign 1")
        self.assertEqual(chart["data"][1]["value"], 8000000)
        
        # Test with empty data
        empty_chart = format_pie_chart(
            data=[],
            metric="cost_micros",
            title="Empty Pie Chart"
        )
        self.assertEqual(empty_chart["title"], "Empty Pie Chart")
        self.assertEqual(len(empty_chart["data"]), 0)

    def test_create_comparison_bar_chart(self):
        """Test the new comparison bar chart function."""
        # Test with sample campaign data
        chart = create_comparison_bar_chart(
            entities=self.campaign_data,
            metrics=self.metrics,
            entity_name_key="name",
            title="Campaign Comparison"
        )
        
        # Check chart structure
        self.assertEqual(chart["type"], "bar")
        self.assertEqual(chart["title"], "Campaign Comparison")
        self.assertIn("data", chart)
        self.assertIn("labels", chart["data"])
        self.assertIn("datasets", chart["data"])
        
        # Check labels (campaign names)
        self.assertEqual(len(chart["data"]["labels"]), 2)
        self.assertEqual(chart["data"]["labels"][0], "Campaign 1")
        self.assertEqual(chart["data"]["labels"][1], "Campaign 2")
        
        # Check datasets (metrics)
        self.assertEqual(len(chart["data"]["datasets"]), 3)  # 3 metrics
        self.assertEqual(chart["data"]["datasets"][0]["label"], "Cost")
        self.assertEqual(chart["data"]["datasets"][1]["label"], "Clicks")
        self.assertEqual(chart["data"]["datasets"][2]["label"], "Conversions")
        
        # Check formatting of values
        self.assertEqual(chart["data"]["datasets"][0]["data"][0], 8.0)  # $8 (from 8000000 micros)
        self.assertEqual(chart["data"]["datasets"][0]["data"][1], 15.0)  # $15 (from 15000000 micros)
        self.assertEqual(chart["data"]["datasets"][1]["data"][0], 100)  # 100 clicks
        self.assertEqual(chart["data"]["datasets"][1]["data"][1], 150)  # 150 clicks
        
        # Test with empty data
        empty_chart = create_comparison_bar_chart(
            entities=[],
            metrics=self.metrics,
            title="Empty Comparison"
        )
        self.assertEqual(empty_chart["title"], "Empty Comparison")
        self.assertEqual(len(empty_chart["data"]["labels"]), 0)
        self.assertEqual(len(empty_chart["data"]["datasets"]), 0)

    def test_create_comparison_data_table(self):
        """Test the comparison data table function."""
        # Test with sample campaign data and include change calculations
        table = create_comparison_data_table(
            entities=self.campaign_data,
            metrics=self.metrics,
            entity_name_key="name",
            title="Campaign Comparison Table",
            include_change=True,
            baseline_entity_index=0
        )
        
        # Check table structure
        self.assertEqual(table["title"], "Campaign Comparison Table")
        self.assertIn("headers", table)
        self.assertIn("rows", table)
        
        # Check headers
        self.assertEqual(len(table["headers"]), 4)  # Metric, Campaign 1, Campaign 2, Change
        self.assertEqual(table["headers"][0], "Metric")
        self.assertEqual(table["headers"][1], "Campaign 1")
        self.assertEqual(table["headers"][2], "Campaign 2")
        self.assertTrue("Change" in table["headers"][3])
        
        # Check rows
        self.assertEqual(len(table["rows"]), 3)  # 3 metrics
        
        # Check first row (Cost)
        self.assertEqual(table["rows"][0][0], "Cost")
        self.assertEqual(table["rows"][0][1], "$8.00")
        self.assertEqual(table["rows"][0][2], "$15.00")
        # Change value should be positive (since 15 > 8)
        self.assertTrue("+87.50%" in table["rows"][0][3])
        
        # Test without change calculation
        table_no_change = create_comparison_data_table(
            entities=self.campaign_data,
            metrics=self.metrics,
            entity_name_key="name",
            title="No Change Comparison",
            include_change=False
        )
        
        # Check headers (should not include change column)
        self.assertEqual(len(table_no_change["headers"]), 3)  # Metric, Campaign 1, Campaign 2
        
        # Test with empty data
        empty_table = create_comparison_data_table(
            entities=[],
            metrics=self.metrics,
            title="Empty Table"
        )
        self.assertEqual(empty_table["title"], "Empty Table")
        self.assertEqual(len(empty_table["rows"]), 0)

    def test_create_comparison_radar_chart(self):
        """Test the comparison radar chart function."""
        # Test with sample campaign data
        chart = create_comparison_radar_chart(
            entities=self.campaign_data,
            metrics=self.metrics,
            entity_name_key="name",
            title="Radar Comparison"
        )
        
        # Check chart structure
        self.assertEqual(chart["type"], "radar")
        self.assertEqual(chart["title"], "Radar Comparison")
        self.assertIn("data", chart)
        self.assertIn("labels", chart["data"])
        self.assertIn("datasets", chart["data"])
        
        # Check labels (metric names)
        self.assertEqual(len(chart["data"]["labels"]), 3)
        self.assertEqual(chart["data"]["labels"][0], "Cost")
        self.assertEqual(chart["data"]["labels"][1], "Clicks")
        self.assertEqual(chart["data"]["labels"][2], "Conversions")
        
        # Check datasets (campaigns)
        self.assertEqual(len(chart["data"]["datasets"]), 2)  # 2 campaigns
        self.assertEqual(chart["data"]["datasets"][0]["label"], "Campaign 1")
        self.assertEqual(chart["data"]["datasets"][1]["label"], "Campaign 2")
        
        # Check data normalization
        # Campaign 2 has highest values for all metrics, so it should have 100 for each
        self.assertEqual(chart["data"]["datasets"][1]["data"][0], 100.0)  # Cost
        self.assertEqual(chart["data"]["datasets"][1]["data"][1], 100.0)  # Clicks
        self.assertEqual(chart["data"]["datasets"][1]["data"][2], 100.0)  # Conversions
        
        # Campaign 1 values should be normalized relative to Campaign 2
        self.assertAlmostEqual(chart["data"]["datasets"][0]["data"][0], 8.0/15.0 * 100, places=1)  # Cost
        self.assertAlmostEqual(chart["data"]["datasets"][0]["data"][1], 100.0/150.0 * 100, places=1)  # Clicks
        self.assertAlmostEqual(chart["data"]["datasets"][0]["data"][2], 5.0/8.0 * 100, places=1)  # Conversions
        
        # Test with empty data
        empty_chart = create_comparison_radar_chart(
            entities=[],
            metrics=self.metrics,
            title="Empty Radar"
        )
        self.assertEqual(empty_chart["title"], "Empty Radar")
        self.assertEqual(len(empty_chart["data"]["labels"]), 0)
        self.assertEqual(len(empty_chart["data"]["datasets"]), 0)

    def test_format_comparison_visualization(self):
        """Test the comprehensive comparison visualization function."""
        # Use our mock comparison data
        visualization = format_comparison_visualization(
            comparison_data=self.comparison_data,
            metrics=self.metrics,
            title="Test Comparison"
        )
        
        # Check visualization structure
        self.assertIn("charts", visualization)
        self.assertIn("tables", visualization)
        
        # Should include at least one chart (bar chart) and one table
        self.assertGreaterEqual(len(visualization["charts"]), 1)
        self.assertGreaterEqual(len(visualization["tables"]), 1)
        
        # First chart should be a bar chart
        self.assertEqual(visualization["charts"][0]["type"], "bar")
        
        # If we have 3+ metrics, a radar chart should be included
        if len(self.metrics) >= 3:
            radar_chart = None
            for chart in visualization["charts"]:
                if chart["type"] == "radar":
                    radar_chart = chart
                    break
            self.assertIsNotNone(radar_chart)
        
        # Table should be present with comparison data
        self.assertEqual(visualization["tables"][0]["title"], "Test Comparison - Detailed Comparison")
        
        # Test with empty data
        empty_visualization = format_comparison_visualization(
            comparison_data={"campaigns": [], "metrics": self.metrics},
            title="Empty Visualization"
        )
        self.assertEqual(len(empty_visualization["charts"]), 0)
        self.assertEqual(len(empty_visualization["tables"]), 1)  # Should have one table with error message


if __name__ == '__main__':
    unittest.main() 