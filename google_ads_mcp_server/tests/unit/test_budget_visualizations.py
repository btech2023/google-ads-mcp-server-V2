import unittest
from unittest.mock import patch, MagicMock

# Import the visualization functions
from google_ads_mcp_server.visualization.budgets import (
    create_budget_utilization_chart,
    create_budget_distribution_chart,
    create_budget_performance_chart,
    create_budget_recommendation_chart,
    format_budget_for_visualization
)


class TestBudgetVisualizations(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample budget data for testing
        self.sample_budget_data = [
            {
                "id": 456,
                "name": "Test Budget 1",
                "amount_micros": 50000000,  # 50 units
                "status": "ENABLED",
                "period": "DAILY",
                "delivery_method": "STANDARD",
                "utilization": 0.5,  # 50%
                "metrics": {
                    "cost_micros": 25000000,  # 25 units
                    "impressions": 1000,
                    "clicks": 100,
                    "conversions": 10
                },
                "associated_campaigns": [
                    {"id": 789, "name": "Campaign A", "status": "ENABLED"}
                ]
            },
            {
                "id": 457,
                "name": "Test Budget 2",
                "amount_micros": 100000000,  # 100 units
                "status": "ENABLED",
                "period": "DAILY",
                "delivery_method": "STANDARD",
                "utilization": 0.95,  # 95%
                "metrics": {
                    "cost_micros": 95000000,  # 95 units
                    "impressions": 5000,
                    "clicks": 450,
                    "conversions": 45
                },
                "associated_campaigns": [
                    {"id": 790, "name": "Campaign B", "status": "ENABLED"},
                    {"id": 791, "name": "Campaign C", "status": "ENABLED"}
                ]
            },
            {
                "id": 458,
                "name": "Test Budget 3",
                "amount_micros": 75000000,  # 75 units
                "status": "ENABLED",
                "period": "DAILY",
                "delivery_method": "STANDARD",
                "utilization": 0.25,  # 25%
                "metrics": {
                    "cost_micros": 18750000,  # 18.75 units
                    "impressions": 750,
                    "clicks": 75,
                    "conversions": 5
                },
                "associated_campaigns": [
                    {"id": 792, "name": "Campaign D", "status": "ENABLED"}
                ]
            }
        ]

    def test_create_budget_utilization_chart(self):
        """Test the budget utilization chart creation."""
        # Act
        result = create_budget_utilization_chart(self.sample_budget_data)
        
        # Assert
        self.assertEqual(result["type"], "bar")
        self.assertEqual(result["title"], "Budget Utilization")
        
        # Check data structure
        self.assertIn("data", result)
        self.assertIn("labels", result["data"])
        self.assertIn("datasets", result["data"])
        
        # Check correct number of budgets
        self.assertEqual(len(result["data"]["labels"]), 3)
        
        # Check labels contain budget names
        self.assertIn("Test Budget 1", result["data"]["labels"])
        self.assertIn("Test Budget 2", result["data"]["labels"])
        self.assertIn("Test Budget 3", result["data"]["labels"])
        
        # Check dataset values
        self.assertEqual(len(result["data"]["datasets"]), 1)
        dataset = result["data"]["datasets"][0]
        self.assertEqual(len(dataset["data"]), 3)
        
        # Verify the values correspond to utilization percentages
        # Data should be [50, 95, 25] representing utilization percentages
        self.assertEqual(dataset["data"][0], 50)  # 50% for Budget 1
        self.assertEqual(dataset["data"][1], 95)  # 95% for Budget 2
        self.assertEqual(dataset["data"][2], 25)  # 25% for Budget 3

    def test_create_budget_distribution_chart(self):
        """Test the budget distribution chart creation."""
        # Act
        result = create_budget_distribution_chart(self.sample_budget_data)
        
        # Assert
        self.assertEqual(result["type"], "pie")
        self.assertEqual(result["title"], "Budget Distribution by Campaign")
        
        # Check data structure
        self.assertIn("data", result)
        self.assertIn("labels", result["data"])
        self.assertIn("datasets", result["data"])
        
        # Check correct number of campaigns
        # We have 4 campaigns across 3 budgets
        self.assertEqual(len(result["data"]["labels"]), 4)
        
        # Check campaign names in labels
        self.assertIn("Campaign A", result["data"]["labels"])
        self.assertIn("Campaign B", result["data"]["labels"])
        self.assertIn("Campaign C", result["data"]["labels"])
        self.assertIn("Campaign D", result["data"]["labels"])
        
        # Check dataset values
        self.assertEqual(len(result["data"]["datasets"]), 1)
        dataset = result["data"]["datasets"][0]
        self.assertEqual(len(dataset["data"]), 4)
        
        # Sum of values should add up to total budget (225 units)
        total_budget = sum(dataset["data"])
        self.assertAlmostEqual(total_budget, 225, delta=0.1)  # Allow small rounding error

    def test_create_budget_performance_chart(self):
        """Test the budget performance chart creation."""
        # Act
        result = create_budget_performance_chart(self.sample_budget_data)
        
        # Assert
        self.assertEqual(result["type"], "bubble")
        self.assertEqual(result["title"], "Budget Performance")
        
        # Check data structure
        self.assertIn("data", result)
        self.assertIn("datasets", result["data"])
        
        # Check correct number of budgets
        self.assertEqual(len(result["data"]["datasets"]), 3)
        
        # Check each dataset has the right budget
        budget_names = [dataset["label"] for dataset in result["data"]["datasets"]]
        self.assertIn("Test Budget 1", budget_names)
        self.assertIn("Test Budget 2", budget_names)
        self.assertIn("Test Budget 3", budget_names)
        
        # Check data points contain correct structure (x, y, r)
        for dataset in result["data"]["datasets"]:
            self.assertEqual(len(dataset["data"]), 1)  # One data point per budget
            data_point = dataset["data"][0]
            self.assertIn("x", data_point)  # Should have x (CTR)
            self.assertIn("y", data_point)  # Should have y (Conversion Rate)
            self.assertIn("r", data_point)  # Should have r (Budget Amount)

    def test_create_budget_recommendation_chart(self):
        """Test the budget recommendation chart creation."""
        # Act
        result = create_budget_recommendation_chart(self.sample_budget_data)
        
        # Assert
        self.assertEqual(result["type"], "bar")
        self.assertEqual(result["title"], "Budget Recommendations")
        
        # Check data structure
        self.assertIn("data", result)
        self.assertIn("labels", result["data"])
        self.assertIn("datasets", result["data"])
        
        # Check correct number of budgets
        self.assertEqual(len(result["data"]["labels"]), 3)
        
        # Check labels contain budget names
        self.assertIn("Test Budget 1", result["data"]["labels"])
        self.assertIn("Test Budget 2", result["data"]["labels"])
        self.assertIn("Test Budget 3", result["data"]["labels"])
        
        # Check datasets
        self.assertEqual(len(result["data"]["datasets"]), 2)  # Current and Recommended
        
        # Check dataset values lengths
        current_dataset = result["data"]["datasets"][0]
        recommended_dataset = result["data"]["datasets"][1]
        self.assertEqual(len(current_dataset["data"]), 3)
        self.assertEqual(len(recommended_dataset["data"]), 3)
        
        # Check current values match budget amounts (50, 100, 75)
        self.assertEqual(current_dataset["data"][0], 50)
        self.assertEqual(current_dataset["data"][1], 100)
        self.assertEqual(current_dataset["data"][2], 75)
        
        # Check recommended values follow expected pattern:
        # - Near max for high utilization (Budget 2)
        # - Reduced for low utilization (Budget 3)
        # - Similar for moderate utilization (Budget 1)
        self.assertTrue(recommended_dataset["data"][1] >= current_dataset["data"][1])  # Budget 2 (high util)
        self.assertTrue(recommended_dataset["data"][2] < current_dataset["data"][2])   # Budget 3 (low util)

    @patch('google_ads_mcp_server.visualization.budgets.create_budget_utilization_chart')
    @patch('google_ads_mcp_server.visualization.budgets.create_budget_distribution_chart')
    @patch('google_ads_mcp_server.visualization.budgets.create_budget_performance_chart')
    @patch('google_ads_mcp_server.visualization.budgets.create_budget_recommendation_chart')
    def test_format_budget_for_visualization(self, mock_recommendation, mock_performance, 
                                            mock_distribution, mock_utilization):
        """Test the main budget visualization formatter."""
        # Arrange
        # Set up return values for mocked chart functions
        mock_utilization.return_value = {"type": "bar", "title": "Utilization"}
        mock_distribution.return_value = {"type": "pie", "title": "Distribution"}
        mock_performance.return_value = {"type": "bubble", "title": "Performance"}
        mock_recommendation.return_value = {"type": "bar", "title": "Recommendations"}
        
        # Act
        result = format_budget_for_visualization(self.sample_budget_data)
        
        # Assert
        # Check that all chart creation functions were called with the budget data
        mock_utilization.assert_called_once_with(self.sample_budget_data)
        mock_distribution.assert_called_once_with(self.sample_budget_data)
        mock_performance.assert_called_once_with(self.sample_budget_data)
        mock_recommendation.assert_called_once_with(self.sample_budget_data)
        
        # Check result structure
        self.assertIn("charts", result)
        self.assertIn("tables", result)
        
        # Check all charts are included
        self.assertEqual(len(result["charts"]), 4)
        chart_titles = [chart["title"] for chart in result["charts"]]
        self.assertIn("Utilization", chart_titles)
        self.assertIn("Distribution", chart_titles)
        self.assertIn("Performance", chart_titles)
        self.assertIn("Recommendations", chart_titles)
        
        # Check tables are included
        self.assertGreaterEqual(len(result["tables"]), 1)
        self.assertIn("Budget Summary", [table["title"] for table in result["tables"]])

    def test_format_budget_for_visualization_integration(self):
        """Integration test for the budget visualization formatter without mocks."""
        # Act - call the actual function without mocks
        result = format_budget_for_visualization(self.sample_budget_data)
        
        # Assert
        # Check structure
        self.assertIn("charts", result)
        self.assertIn("tables", result)
        
        # Check charts
        self.assertEqual(len(result["charts"]), 4)
        chart_types = [chart["type"] for chart in result["charts"]]
        self.assertIn("bar", chart_types)
        self.assertIn("pie", chart_types)
        self.assertIn("bubble", chart_types)
        
        # Check budget summary table
        self.assertGreaterEqual(len(result["tables"]), 1)
        budget_table = next(table for table in result["tables"] 
                           if table["title"] == "Budget Summary")
        
        # Check table headers and rows
        self.assertIn("headers", budget_table)
        self.assertIn("rows", budget_table)
        self.assertEqual(len(budget_table["rows"]), 3)  # 3 budgets
        
        # Check headers include important budget fields
        header_fields = budget_table["headers"]
        expected_fields = ["ID", "Name", "Amount", "Utilization", "Campaigns"]
        for field in expected_fields:
            self.assertTrue(any(field in header for header in header_fields),
                           f"Header '{field}' not found in table headers")


if __name__ == '__main__':
    unittest.main() 