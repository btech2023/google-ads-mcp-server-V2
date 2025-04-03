import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

from google_ads_mcp_server.visualization.breakdowns import (
    create_stacked_bar_chart,
    create_breakdown_table,
    create_treemap_chart,
    create_time_breakdown_chart,
    format_breakdown_visualization,
    _format_currency_micros,
    _format_percentage
)


class TestBreakdownVisualizations(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample device breakdown data
        self.device_data = [
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
            },
            {
                "device": "TABLET",
                "cost_micros": 5000000,
                "impressions": 1000,
                "clicks": 50,
                "conversions": 2
            }
        ]
        
        # Sample time breakdown data
        self.time_data = [
            {
                "day": "2025-04-01",
                "cost_micros": 5000000,
                "impressions": 1000,
                "clicks": 50,
                "conversions": 2
            },
            {
                "day": "2025-04-02",
                "cost_micros": 6000000,
                "impressions": 1200,
                "clicks": 60,
                "conversions": 3
            },
            {
                "day": "2025-04-03",
                "cost_micros": 5500000,
                "impressions": 1100,
                "clicks": 55,
                "conversions": 3
            }
        ]
        
        # Metrics to test with
        self.metrics = ["cost_micros", "clicks", "conversions"]
        
        # Sample breakdown data structure
        self.breakdown_data = {
            "entity_type": "campaign",
            "entity_id": "123456789",
            "entity_name": "Test Campaign",
            "dimensions": ["device", "day"],
            "date_range": "LAST_30_DAYS",
            "data": [
                {
                    "dimension": "device",
                    "segments": self.device_data
                },
                {
                    "dimension": "day",
                    "segments": self.time_data
                }
            ]
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

    def test_create_stacked_bar_chart(self):
        """Test the stacked bar chart function."""
        # Test with device data
        chart = create_stacked_bar_chart(
            data=self.device_data,
            dimension_key="device",
            metrics=self.metrics,
            title="Device Breakdown"
        )
        
        # Check chart structure
        self.assertEqual(chart["type"], "bar")
        self.assertEqual(chart["title"], "Device Breakdown")
        self.assertIn("data", chart)
        self.assertIn("labels", chart["data"])
        self.assertIn("datasets", chart["data"])
        
        # Check labels (device names)
        self.assertEqual(len(chart["data"]["labels"]), 3)
        self.assertEqual(chart["data"]["labels"][0], "MOBILE")
        self.assertEqual(chart["data"]["labels"][1], "DESKTOP")
        self.assertEqual(chart["data"]["labels"][2], "TABLET")
        
        # Check datasets (metrics)
        self.assertEqual(len(chart["data"]["datasets"]), 3)  # 3 metrics
        self.assertEqual(chart["data"]["datasets"][0]["label"], "Cost")
        self.assertEqual(chart["data"]["datasets"][1]["label"], "Clicks")
        self.assertEqual(chart["data"]["datasets"][2]["label"], "Conversions")
        
        # Check formatting of values
        self.assertEqual(chart["data"]["datasets"][0]["data"][0], 30.0)  # $30 (from 30000000 micros)
        self.assertEqual(chart["data"]["datasets"][0]["data"][1], 20.0)  # $20 
        self.assertEqual(chart["data"]["datasets"][0]["data"][2], 5.0)   # $5
        
        # Check stacking is enabled
        self.assertEqual(chart["data"]["datasets"][0]["stack"], "Stack 0")
        self.assertEqual(chart["data"]["datasets"][1]["stack"], "Stack 0")
        self.assertEqual(chart["data"]["datasets"][2]["stack"], "Stack 0")
        
        # Check options configuration
        self.assertTrue(chart["options"]["scales"]["x"]["stacked"])
        self.assertTrue(chart["options"]["scales"]["y"]["stacked"])
        
        # Test with empty data
        empty_chart = create_stacked_bar_chart(
            data=[],
            dimension_key="device",
            metrics=self.metrics,
            title="Empty Chart"
        )
        self.assertEqual(empty_chart["title"], "Empty Chart")
        self.assertEqual(len(empty_chart["data"]["labels"]), 0)
        self.assertEqual(len(empty_chart["data"]["datasets"]), 0)

    def test_create_breakdown_table(self):
        """Test the breakdown table function."""
        # Test with device data
        table = create_breakdown_table(
            data=self.device_data,
            dimension_key="device",
            metrics=self.metrics,
            title="Device Breakdown Table"
        )
        
        # Check table structure
        self.assertEqual(table["title"], "Device Breakdown Table")
        self.assertIn("headers", table)
        self.assertIn("rows", table)
        
        # Check headers
        self.assertEqual(len(table["headers"]), 4)  # Device, Cost, Clicks, Conversions
        self.assertEqual(table["headers"][0], "Device")
        self.assertEqual(table["headers"][1], "Cost")
        self.assertEqual(table["headers"][2], "Clicks")
        self.assertEqual(table["headers"][3], "Conversions")
        
        # Check rows
        self.assertEqual(len(table["rows"]), 3)  # 3 devices
        
        # Check values include percentages
        # MOBILE has 30/55 = ~54.5% of total cost
        self.assertTrue("$30.00" in table["rows"][0][1])
        self.assertTrue("54.5%" in table["rows"][0][1])
        
        # MOBILE has 300/550 = ~54.5% of total clicks
        self.assertTrue("300" in table["rows"][0][2])
        self.assertTrue("54.5%" in table["rows"][0][2])
        
        # Check rows are sorted by cost (highest first)
        self.assertEqual(table["rows"][0][0], "MOBILE")
        self.assertEqual(table["rows"][1][0], "DESKTOP")
        self.assertEqual(table["rows"][2][0], "TABLET")
        
        # Test with empty data
        empty_table = create_breakdown_table(
            data=[],
            dimension_key="device",
            metrics=self.metrics,
            title="Empty Table"
        )
        self.assertEqual(empty_table["title"], "Empty Table")
        self.assertEqual(len(empty_table["rows"]), 0)

    def test_create_treemap_chart(self):
        """Test the treemap chart function."""
        # Test with device data
        chart = create_treemap_chart(
            data=self.device_data,
            dimension_key="device",
            size_metric="cost_micros",
            color_metric="conversions",
            title="Cost Distribution by Device"
        )
        
        # Check chart structure
        self.assertEqual(chart["type"], "treemap")
        self.assertEqual(chart["title"], "Cost Distribution by Device")
        self.assertIn("data", chart)
        self.assertIn("datasets", chart["data"])
        
        # Check datasets
        self.assertEqual(len(chart["data"]["datasets"]), 1)
        self.assertIn("tree", chart["data"]["datasets"][0])
        
        # Check tree data has 3 entries (one per device)
        tree_data = chart["data"]["datasets"][0]["tree"]
        self.assertEqual(len(tree_data), 3)
        
        # Check tree data values are formatted correctly
        # Find MOBILE data
        mobile_data = next((item for item in tree_data if item["name"] == "MOBILE"), None)
        self.assertIsNotNone(mobile_data)
        self.assertEqual(mobile_data["value"], 30.0)  # Cost in dollars
        self.assertEqual(mobile_data["colorValue"], 15)  # Conversions
        
        # Test with empty data
        empty_chart = create_treemap_chart(
            data=[],
            dimension_key="device",
            title="Empty Treemap"
        )
        self.assertEqual(empty_chart["title"], "Empty Treemap")
        self.assertEqual(len(empty_chart["data"]["datasets"][0]["tree"]), 0)

    def test_create_time_breakdown_chart(self):
        """Test the time breakdown chart function."""
        # Test with time data
        chart = create_time_breakdown_chart(
            data=self.time_data,
            time_key="day",
            metrics=self.metrics,
            title="Daily Performance"
        )
        
        # Check chart structure
        self.assertEqual(chart["type"], "line")
        self.assertEqual(chart["title"], "Daily Performance")
        self.assertIn("data", chart)
        self.assertIn("labels", chart["data"])
        self.assertIn("datasets", chart["data"])
        
        # Check labels (dates)
        self.assertEqual(len(chart["data"]["labels"]), 3)
        self.assertEqual(chart["data"]["labels"][0], "2025-04-01")
        self.assertEqual(chart["data"]["labels"][1], "2025-04-02")
        self.assertEqual(chart["data"]["labels"][2], "2025-04-03")
        
        # Check datasets (metrics)
        self.assertEqual(len(chart["data"]["datasets"]), 3)  # 3 metrics
        self.assertEqual(chart["data"]["datasets"][0]["label"], "Cost")
        self.assertEqual(chart["data"]["datasets"][1]["label"], "Clicks")
        self.assertEqual(chart["data"]["datasets"][2]["label"], "Conversions")
        
        # Check formatting of values
        self.assertEqual(chart["data"]["datasets"][0]["data"][0], 5.0)   # $5
        self.assertEqual(chart["data"]["datasets"][0]["data"][1], 6.0)   # $6
        self.assertEqual(chart["data"]["datasets"][0]["data"][2], 5.5)   # $5.50
        self.assertEqual(chart["data"]["datasets"][1]["data"][0], 50)    # 50 clicks
        self.assertEqual(chart["data"]["datasets"][1]["data"][1], 60)    # 60 clicks
        self.assertEqual(chart["data"]["datasets"][1]["data"][2], 55)    # 55 clicks
        
        # Test with empty data
        empty_chart = create_time_breakdown_chart(
            data=[],
            time_key="day",
            metrics=self.metrics,
            title="Empty Chart"
        )
        self.assertEqual(empty_chart["title"], "Empty Chart")
        self.assertEqual(len(empty_chart["data"]["labels"]), 0)
        self.assertEqual(len(empty_chart["data"]["datasets"]), 0)

    def test_format_breakdown_visualization(self):
        """Test the comprehensive breakdown visualization function."""
        # Use our mock breakdown data
        visualization = format_breakdown_visualization(
            breakdown_data=self.breakdown_data,
            title="Test Breakdown"
        )
        
        # Check visualization structure
        self.assertIn("charts", visualization)
        self.assertIn("tables", visualization)
        
        # Should have charts and tables for two dimensions
        self.assertGreaterEqual(len(visualization["charts"]), 2)
        self.assertGreaterEqual(len(visualization["tables"]), 2)
        
        # First dimension should have a stacked bar chart for device
        device_chart = None
        device_table = None
        
        for chart in visualization["charts"]:
            if "Device" in chart["title"]:
                device_chart = chart
                break
        
        for table in visualization["tables"]:
            if "Device" in table["title"]:
                device_table = table
                break
        
        self.assertIsNotNone(device_chart)
        self.assertEqual(device_chart["type"], "bar")
        self.assertIsNotNone(device_table)
        
        # Second dimension should have a time series chart for day
        time_chart = None
        time_table = None
        
        for chart in visualization["charts"]:
            if "Day" in chart["title"]:
                time_chart = chart
                break
        
        for table in visualization["tables"]:
            if "Day" in table["title"]:
                time_table = table
                break
        
        self.assertIsNotNone(time_chart)
        self.assertEqual(time_chart["type"], "line")
        self.assertIsNotNone(time_table)
        
        # Check treemap is included for device dimension
        treemap = None
        for chart in visualization["charts"]:
            if "Distribution" in chart["title"] and "Device" in chart["title"]:
                treemap = chart
                break
        
        self.assertIsNotNone(treemap)
        self.assertEqual(treemap["type"], "treemap")
        
        # Test with empty data
        empty_breakdown = {
            "entity_type": "campaign",
            "entity_id": "123456789",
            "entity_name": "Test Campaign",
            "dimensions": ["device", "day"],
            "date_range": "LAST_30_DAYS",
            "data": [
                {
                    "dimension": "device",
                    "segments": []
                },
                {
                    "dimension": "day",
                    "segments": []
                }
            ]
        }
        
        empty_visualization = format_breakdown_visualization(
            breakdown_data=empty_breakdown,
            title="Empty Visualization"
        )
        self.assertEqual(len(empty_visualization["charts"]), 0)
        self.assertEqual(len(empty_visualization["tables"]), 0)
        
        # Test with single dimension
        single_dimension = {
            "entity_type": "campaign",
            "entity_id": "123456789",
            "entity_name": "Test Campaign",
            "dimensions": ["device"],
            "date_range": "LAST_30_DAYS",
            "data": [
                {
                    "dimension": "device",
                    "segments": self.device_data
                }
            ]
        }
        
        single_visualization = format_breakdown_visualization(
            breakdown_data=single_dimension,
            title="Single Dimension"
        )
        self.assertGreaterEqual(len(single_visualization["charts"]), 1)
        self.assertGreaterEqual(len(single_visualization["tables"]), 1)
        
        # All charts should have device in the title
        for chart in single_visualization["charts"]:
            self.assertIn("Device", chart["title"])


if __name__ == '__main__':
    unittest.main() 