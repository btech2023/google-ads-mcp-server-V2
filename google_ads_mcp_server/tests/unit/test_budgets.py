import unittest
from unittest.mock import MagicMock, patch
import datetime

from google_ads_mcp_server.google_ads.budgets import BudgetService
# Assuming GoogleAdsService is in google_ads.service
# Adjust the import path if necessary
# from google_ads_mcp_server.google_ads.service import GoogleAdsService


class TestBudgetService(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures, if any."""
        self.mock_google_ads_service = MagicMock()
        self.budget_service = BudgetService(self.mock_google_ads_service)

    def test_get_budgets_success(self):
        """Test successful retrieval of budgets."""
        # Arrange
        mock_budget_data = [
            {
                "resource_name": "customers/123/campaignBudgets/456",
                "id": 456,
                "name": "Test Budget 1",
                "amount_micros": 50000000, # 50 units
                "status": "ENABLED",
                "delivery_method": "STANDARD",
                "effective_date_time": "2025-04-20 10:00:00",
                "total_amount_micros": None,
                "period": "DAILY",
                "associated_campaigns": ["customers/123/campaigns/789"],
                "metrics": {
                    "cost_micros": 25000000, # 25 units
                    "impressions": 1000,
                    "clicks": 100
                }
            },
            {
                "resource_name": "customers/123/campaignBudgets/457",
                "id": 457,
                "name": "Test Budget 2",
                "amount_micros": 100000000, # 100 units
                "status": "ENABLED",
                "delivery_method": "STANDARD",
                "effective_date_time": "2025-04-21 11:00:00",
                "total_amount_micros": None,
                "period": "DAILY",
                "associated_campaigns": ["customers/123/campaigns/790"],
                "metrics": {
                    "cost_micros": 95000000, # 95 units
                    "impressions": 5000,
                    "clicks": 450
                }
            }
        ]
        self.mock_google_ads_service.get_campaign_budgets.return_value = mock_budget_data
        budget_ids = [456, 457]
        status = "ENABLED"

        # Act
        result = self.budget_service.get_budgets(budget_ids=budget_ids, status=status)

        # Assert
        self.mock_google_ads_service.get_campaign_budgets.assert_called_once_with(
            budget_ids=budget_ids, status=status
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], 456)
        self.assertEqual(result[1]["id"], 457)
        self.assertEqual(result[0]["utilization"], 0.5) # 25 / 50
        self.assertEqual(result[1]["utilization"], 0.95) # 95 / 100

    def test_get_budgets_no_data(self):
        """Test budget retrieval when no data is returned."""
        # Arrange
        self.mock_google_ads_service.get_campaign_budgets.return_value = []

        # Act
        result = self.budget_service.get_budgets()

        # Assert
        self.mock_google_ads_service.get_campaign_budgets.assert_called_once_with(
            budget_ids=None, status=None
        )
        self.assertEqual(result, [])

    def test_get_budgets_api_error(self):
        """Test budget retrieval when the API service raises an error."""
        # Arrange
        self.mock_google_ads_service.get_campaign_budgets.side_effect = Exception("API Error")

        # Act & Assert
        with self.assertRaises(Exception) as context:
            self.budget_service.get_budgets()
        self.assertTrue("API Error" in str(context.exception))
        self.mock_google_ads_service.get_campaign_budgets.assert_called_once()

    def test_update_budget_placeholder(self):
        """Test the placeholder update_budget method."""
        # Arrange
        budget_id = 456
        updates = {"amount_micros": 60000000}

        # Act
        result = self.budget_service.update_budget(budget_id, updates)

        # Assert
        # Verify the placeholder message is returned and no API call is made
        self.assertEqual(result, f"Budget {budget_id} update simulated (API call not implemented). Updates: {updates}")
        self.mock_google_ads_service.update_campaign_budget.assert_not_called() # Assuming a method name

    def test_analyze_budget_performance_high_utilization(self):
        """Test budget analysis identifying high utilization."""
        # Arrange
        mock_budget_data = [
            {
                "id": 457,
                "name": "Test Budget High Util",
                "amount_micros": 100000000, # 100
                "period": "DAILY",
                "metrics": {"cost_micros": 95000000}, # 95
                "utilization": 0.95
            }
        ]

        # Act
        analysis = self.budget_service.analyze_budget_performance(mock_budget_data)

        # Assert
        self.assertEqual(len(analysis), 1)
        self.assertEqual(analysis[0]["budget_id"], 457)
        self.assertIn("High Utilization (95.0%)", analysis[0]["insights"])
        self.assertIn("Consider increasing budget", analysis[0]["recommendations"])

    def test_analyze_budget_performance_low_utilization(self):
        """Test budget analysis identifying low utilization."""
        # Arrange
        mock_budget_data = [
            {
                "id": 456,
                "name": "Test Budget Low Util",
                "amount_micros": 50000000, # 50
                "period": "DAILY",
                "metrics": {"cost_micros": 5000000}, # 5
                "utilization": 0.10
            }
        ]

        # Act
        analysis = self.budget_service.analyze_budget_performance(mock_budget_data)

        # Assert
        self.assertEqual(len(analysis), 1)
        self.assertEqual(analysis[0]["budget_id"], 456)
        self.assertIn("Low Utilization (10.0%)", analysis[0]["insights"])
        self.assertIn("Consider budget reallocation or campaign optimization", analysis[0]["recommendations"])

    def test_analyze_budget_performance_moderate_utilization(self):
        """Test budget analysis for moderate utilization (no specific recommendations)."""
        # Arrange
        mock_budget_data = [
            {
                "id": 458,
                "name": "Test Budget Moderate Util",
                "amount_micros": 75000000, # 75
                "period": "DAILY",
                "metrics": {"cost_micros": 50000000}, # 50
                "utilization": 50/75 # approx 0.667
            }
        ]

        # Act
        analysis = self.budget_service.analyze_budget_performance(mock_budget_data)

        # Assert
        self.assertEqual(len(analysis), 1)
        self.assertEqual(analysis[0]["budget_id"], 458)
        self.assertIn("Moderate Utilization (66.7%)", analysis[0]["insights"])
        self.assertEqual(analysis[0]["recommendations"], ["Monitor performance."])

    def test_analyze_budget_performance_multiple_budgets(self):
        """Test budget analysis with multiple budgets having different utilization."""
        # Arrange
        mock_budget_data = [
             {
                "id": 456,
                "name": "Test Budget Low Util",
                "amount_micros": 50000000, # 50
                "period": "DAILY",
                "metrics": {"cost_micros": 5000000}, # 5
                "utilization": 0.10
            },
            {
                "id": 457,
                "name": "Test Budget High Util",
                "amount_micros": 100000000, # 100
                "period": "DAILY",
                "metrics": {"cost_micros": 95000000}, # 95
                "utilization": 0.95
            }
        ]

        # Act
        analysis = self.budget_service.analyze_budget_performance(mock_budget_data)

        # Assert
        self.assertEqual(len(analysis), 2)
        # Check low utilization budget
        self.assertEqual(analysis[0]["budget_id"], 456)
        self.assertIn("Low Utilization (10.0%)", analysis[0]["insights"])
        self.assertIn("Consider budget reallocation", analysis[0]["recommendations"])
        # Check high utilization budget
        self.assertEqual(analysis[1]["budget_id"], 457)
        self.assertIn("High Utilization (95.0%)", analysis[1]["insights"])
        self.assertIn("Consider increasing budget", analysis[1]["recommendations"])

    def test_analyze_budget_performance_no_utilization(self):
        """Test budget analysis when utilization cannot be calculated (e.g., missing amount)."""
        # Arrange
        mock_budget_data = [
            {
                "id": 459,
                "name": "Test Budget No Amount",
                "amount_micros": 0, # Edge case
                "period": "DAILY",
                "metrics": {"cost_micros": 5000000}, # 5
                "utilization": None # Assume get_budgets handles this
            }
        ]

        # Act
        analysis = self.budget_service.analyze_budget_performance(mock_budget_data)

        # Assert
        self.assertEqual(len(analysis), 1)
        self.assertEqual(analysis[0]["budget_id"], 459)
        self.assertIn("Utilization N/A", analysis[0]["insights"])
        self.assertEqual(analysis[0]["recommendations"], ["Review budget configuration."])


if __name__ == '__main__':
    unittest.main() 