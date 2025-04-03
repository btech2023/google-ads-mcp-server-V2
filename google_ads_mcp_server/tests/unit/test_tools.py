import unittest
from unittest.mock import MagicMock, patch
import json

# Import services that the tools rely on
from google_ads_mcp_server.google_ads.budgets import BudgetService
from google_ads_mcp_server.google_ads.keywords import KeywordService
from google_ads_mcp_server.google_ads.search_terms import SearchTermService

# Import the MCP tool functions
from google_ads_mcp_server.mcp.tools import (
    get_budgets,
    get_budgets_json,
    analyze_budgets,
    update_budget,
    register_budget_tools,
    # Add imports for other tool functions as needed
    # get_keywords, get_keywords_json, add_keywords, update_keyword_status,
    # get_search_terms, get_search_terms_json, analyze_search_terms
)

# Mock visualization functions used by JSON tools
# We will test visualizations separately, so mock them here.
# Adjust the path based on actual location
@patch('google_ads_mcp_server.visualization.budgets.format_budget_for_visualization')
class TestMCPBudgetTools(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.mock_budget_service = MagicMock(spec=BudgetService)
        # Mock other services as needed when adding tests for other tools
        # self.mock_keyword_service = MagicMock(spec=KeywordService)
        # self.mock_search_term_service = MagicMock(spec=SearchTermService)

        # Inject the mocked service into the tool functions
        # This assumes the tool functions accept the service as an argument
        # or we patch the service instance within each test.
        # A cleaner approach might be a dependency injection framework
        # or refactoring tools to be methods of a class that holds services.
        # For now, we'll patch where needed or assume functions can access mocks.

        # Example budget data returned by the service
        self.sample_budget_data = [
            {
                "id": 456,
                "name": "Test Budget 1",
                "amount_micros": 50000000,
                "status": "ENABLED",
                "period": "DAILY",
                "utilization": 0.5,
                "metrics": {"cost_micros": 25000000}
            },
            {
                "id": 457,
                "name": "Test Budget 2",
                "amount_micros": 100000000,
                "status": "ENABLED",
                "period": "DAILY",
                "utilization": 0.95,
                "metrics": {"cost_micros": 95000000}
            }
        ]
        self.sample_analysis_data = [
            {
                "budget_id": 456,
                "budget_name": "Test Budget 1",
                "utilization": 0.5,
                "insights": ["Moderate Utilization (50.0%)"],
                "recommendations": ["Monitor performance."]
            },
             {
                "budget_id": 457,
                "budget_name": "Test Budget 2",
                "utilization": 0.95,
                "insights": ["High Utilization (95.0%)"],
                "recommendations": ["Consider increasing budget"] # Shortened for brevity
            }
        ]

    def test_get_budgets(self, mock_format_viz): # Mock passed by class decorator
        """Test the get_budgets MCP tool."""
        # Arrange
        self.mock_budget_service.get_budgets.return_value = self.sample_budget_data
        budget_ids = [456, 457]
        status = "ENABLED"

        # Act
        # Assuming get_budgets uses dependency injection or a global/contextual service instance
        # For simplicity, let's patch the service instance access within the tool's scope if needed,
        # or assume the tool function is written to accept the service instance.
        # Let's refine this based on the actual implementation of get_budgets.
        # Option 1: Patching (if get_budgets imports/uses BudgetService directly)
        with patch('google_ads_mcp_server.mcp.tools.budget_service', self.mock_budget_service):
            result = get_budgets(budget_ids_str="456,457", status="ENABLED")

        # Assert
        self.mock_budget_service.get_budgets.assert_called_once_with(budget_ids=[456, 457], status="ENABLED")
        self.assertIn("Budget Report", result)
        self.assertIn("ID: 456", result)
        self.assertIn("Name: Test Budget 1", result)
        self.assertIn("Amount: 50.00", result)
        self.assertIn("Utilization: 50.0%", result)
        self.assertIn("ID: 457", result)
        self.assertIn("Name: Test Budget 2", result)
        self.assertIn("Amount: 100.00", result)
        self.assertIn("Utilization: 95.0%", result)

    def test_get_budgets_no_results(self, mock_format_viz):
        """Test get_budgets when the service returns no budgets."""
        # Arrange
        self.mock_budget_service.get_budgets.return_value = []
        with patch('google_ads_mcp_server.mcp.tools.budget_service', self.mock_budget_service):
            # Act
            result = get_budgets()
            # Assert
            self.mock_budget_service.get_budgets.assert_called_once_with(budget_ids=None, status=None)
            self.assertEqual(result, "No budgets found matching the criteria.")

    def test_get_budgets_json(self, mock_format_viz):
        """Test the get_budgets_json MCP tool."""
        # Arrange
        self.mock_budget_service.get_budgets.return_value = self.sample_budget_data
        mock_format_viz.return_value = {"charts": [{"type": "bar"}], "tables": [{"data": "dummy"}]}
        budget_ids = [456]
        status = "ENABLED"

        # Act
        with patch('google_ads_mcp_server.mcp.tools.budget_service', self.mock_budget_service):
            result_str = get_budgets_json(budget_ids_str="456", status="ENABLED")

        # Assert
        self.mock_budget_service.get_budgets.assert_called_once_with(budget_ids=[456], status="ENABLED")
        mock_format_viz.assert_called_once_with(self.sample_budget_data[:1]) # Called with the filtered data
        result_data = json.loads(result_str)
        self.assertIn("budgets", result_data)
        self.assertEqual(len(result_data["budgets"]), 1)
        self.assertEqual(result_data["budgets"][0]["id"], 456)
        self.assertIn("visualization", result_data)
        self.assertEqual(result_data["visualization"], mock_format_viz.return_value)

    def test_analyze_budgets(self, mock_format_viz):
        """Test the analyze_budgets MCP tool."""
        # Arrange
        # Assume get_budgets is called first, then analyze_budget_performance
        self.mock_budget_service.get_budgets.return_value = self.sample_budget_data
        self.mock_budget_service.analyze_budget_performance.return_value = self.sample_analysis_data

        # Act
        with patch('google_ads_mcp_server.mcp.tools.budget_service', self.mock_budget_service):
            result = analyze_budgets(budget_ids_str="456,457")

        # Assert
        self.mock_budget_service.get_budgets.assert_called_once_with(budget_ids=[456, 457], status=None)
        self.mock_budget_service.analyze_budget_performance.assert_called_once_with(self.sample_budget_data)
        self.assertIn("Budget Analysis Report", result)
        self.assertIn("Budget: Test Budget 1 (ID: 456)", result)
        self.assertIn("Utilization: 50.0%", result)
        self.assertIn("- Moderate Utilization (50.0%)", result)
        self.assertIn("- Monitor performance.", result)
        self.assertIn("Budget: Test Budget 2 (ID: 457)", result)
        self.assertIn("Utilization: 95.0%", result)
        self.assertIn("- High Utilization (95.0%)", result)
        self.assertIn("- Consider increasing budget", result)

    def test_update_budget(self, mock_format_viz):
        """Test the update_budget MCP tool (using placeholder service method)."""
        # Arrange
        budget_id = 456
        update_json = '{"amount_micros": 60000000, "status": "PAUSED"}'
        expected_updates = {"amount_micros": 60000000, "status": "PAUSED"}
        placeholder_response = f"Budget {budget_id} update simulated (API call not implemented). Updates: {expected_updates}"
        self.mock_budget_service.update_budget.return_value = placeholder_response

        # Act
        with patch('google_ads_mcp_server.mcp.tools.budget_service', self.mock_budget_service):
            result = update_budget(budget_id=budget_id, update_json=update_json)

        # Assert
        self.mock_budget_service.update_budget.assert_called_once_with(budget_id, expected_updates)
        self.assertEqual(result, placeholder_response)

    def test_update_budget_invalid_json(self, mock_format_viz):
        """Test update_budget with invalid JSON input."""
        # Arrange
        budget_id = 456
        update_json = '{"amount_micros": 60000000, status: "PAUSED"}' # Invalid JSON (missing quotes around status)

        # Act
        with patch('google_ads_mcp_server.mcp.tools.budget_service', self.mock_budget_service):
            result = update_budget(budget_id=budget_id, update_json=update_json)

        # Assert
        self.assertIn("Error: Invalid JSON provided for updates.", result)
        self.mock_budget_service.update_budget.assert_not_called()

    # --- Placeholder Tests for Other Tools --- 

    # @patch('google_ads_mcp_server.visualization.keywords.format_keyword_for_visualization')
    # def test_get_keywords(self, mock_format_kw_viz):
    #     # TODO: Implement test
    #     pass

    # @patch('google_ads_mcp_server.visualization.keywords.format_keyword_for_visualization')
    # def test_get_keywords_json(self, mock_format_kw_viz):
    #     # TODO: Implement test
    #     pass

    # def test_add_keywords(self):
    #     # TODO: Implement test
    #     pass

    # def test_update_keyword_status(self):
    #     # TODO: Implement test
    #     pass

    # @patch('google_ads_mcp_server.visualization.search_terms.format_search_term_for_visualization')
    # def test_get_search_terms(self, mock_format_st_viz):
    #     # TODO: Implement test
    #     pass

    # @patch('google_ads_mcp_server.visualization.search_terms.format_search_term_for_visualization')
    # def test_get_search_terms_json(self, mock_format_st_viz):
    #     # TODO: Implement test
    #     pass

    # def test_analyze_search_terms(self):
    #     # TODO: Implement test
    #     pass

if __name__ == '__main__':
    unittest.main() 