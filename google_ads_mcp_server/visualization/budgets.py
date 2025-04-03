"""
Budget Visualization Module

This module provides functions for creating budget-related visualizations.
"""

import logging
from typing import List, Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

def create_budget_utilization_chart(budgets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a utilization chart for campaign budgets.
    
    Args:
        budgets: List of budget data dictionaries
        
    Returns:
        Chart configuration for budget utilization visualization
    """
    logger.info("Creating budget utilization chart")
    
    # Sort budgets by amount
    sorted_budgets = sorted(budgets, key=lambda x: x.get("amount", 0), reverse=True)
    
    # Extract data for visualization
    labels = []
    amounts = []
    spends = []
    utilization_percentages = []
    
    for budget in sorted_budgets:
        name = budget.get("name", "Unknown")
        if len(name) > 20:
            name = name[:17] + "..."
            
        labels.append(name)
        amounts.append(budget.get("amount", 0))
        spends.append(budget.get("current_spend", 0))
        utilization_percentages.append(budget.get("utilization_percent", 0))
    
    # Create chart configuration
    chart_config = {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "label": "Budget Amount",
                    "data": amounts,
                    "backgroundColor": "rgba(54, 162, 235, 0.5)",
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "borderWidth": 1
                },
                {
                    "label": "Current Spend",
                    "data": spends,
                    "backgroundColor": "rgba(255, 99, 132, 0.5)",
                    "borderColor": "rgba(255, 99, 132, 1)",
                    "borderWidth": 1
                }
            ]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "title": {
                    "display": True,
                    "text": "Campaign Budget Utilization"
                },
                "tooltip": {
                    "callbacks": {
                        "footer": "function(items) { return 'Utilization: ' + utilization[items[0].dataIndex].toFixed(1) + '%'; }"
                    }
                }
            },
            "scales": {
                "y": {
                    "beginAtZero": True,
                    "title": {
                        "display": True,
                        "text": "Amount ($)"
                    }
                },
                "x": {
                    "title": {
                        "display": True,
                        "text": "Budget"
                    }
                }
            }
        },
        "scriptVars": {
            "utilization": utilization_percentages
        }
    }
    
    return chart_config

def create_budget_distribution_chart(budget: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a distribution chart showing how a budget is utilized across campaigns.
    
    Args:
        budget: Budget data dictionary including associated campaigns
        
    Returns:
        Chart configuration for budget distribution visualization
    """
    logger.info("Creating budget distribution chart")
    
    campaigns = budget.get("associated_campaigns", [])
    
    if not campaigns:
        return {
            "type": "error",
            "message": "No campaigns associated with this budget"
        }
    
    # Sort campaigns by cost
    sorted_campaigns = sorted(campaigns, key=lambda x: x.get("cost", 0), reverse=True)
    
    # Extract data for visualization
    labels = []
    costs = []
    statuses = []
    
    for campaign in sorted_campaigns:
        name = campaign.get("name", "Unknown")
        if len(name) > 20:
            name = name[:17] + "..."
            
        labels.append(name)
        costs.append(campaign.get("cost", 0))
        statuses.append(campaign.get("status", "UNKNOWN"))
    
    # Create color mappings for different statuses
    colors = []
    for status in statuses:
        if status == "ENABLED":
            colors.append("rgba(75, 192, 192, 0.7)")  # Green
        elif status == "PAUSED":
            colors.append("rgba(255, 206, 86, 0.7)")  # Yellow
        else:
            colors.append("rgba(201, 203, 207, 0.7)")  # Grey
    
    # Create chart configuration
    chart_config = {
        "type": "pie",
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "data": costs,
                    "backgroundColor": colors,
                    "hoverOffset": 4
                }
            ]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "title": {
                    "display": True,
                    "text": f"Budget Distribution - {budget.get('name', 'Unknown Budget')}"
                },
                "tooltip": {
                    "callbacks": {
                        "label": "function(item) { return item.label + ': $' + item.raw.toFixed(2) + ' (' + statuses[item.dataIndex] + ')'; }"
                    }
                }
            }
        },
        "scriptVars": {
            "statuses": statuses
        }
    }
    
    return chart_config

def create_budget_performance_chart(budgets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a performance chart for budget utilization vs. campaign count.
    
    Args:
        budgets: List of budget data dictionaries
        
    Returns:
        Chart configuration for budget performance visualization
    """
    logger.info("Creating budget performance chart")
    
    # Extract data for visualization
    data_points = []
    hover_labels = []
    
    for budget in budgets:
        name = budget.get("name", "Unknown")
        amount = budget.get("amount", 0)
        spend = budget.get("current_spend", 0)
        utilization = budget.get("utilization_percent", 0)
        campaign_count = len(budget.get("associated_campaigns", []))
        
        # Create data point for the scatter plot
        data_points.append({
            "x": campaign_count,
            "y": utilization,
            "r": (amount / 100) if amount > 0 else 5  # Size bubble based on budget amount
        })
        
        hover_labels.append({
            "name": name,
            "amount": amount,
            "spend": spend,
            "campaigns": campaign_count
        })
    
    # Create chart configuration
    chart_config = {
        "type": "bubble",
        "data": {
            "datasets": [
                {
                    "label": "Budget Performance",
                    "data": data_points,
                    "backgroundColor": "rgba(255, 99, 132, 0.5)",
                    "borderColor": "rgba(255, 99, 132, 1)",
                    "borderWidth": 1
                }
            ]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "title": {
                    "display": True,
                    "text": "Budget Performance Analysis"
                },
                "tooltip": {
                    "callbacks": {
                        "label": "function(item) { " +
                                 "var label = labels[item.dataIndex]; " +
                                 "return [" +
                                 "  'Budget: ' + label.name, " +
                                 "  'Amount: $' + label.amount.toFixed(2), " +
                                 "  'Spend: $' + label.spend.toFixed(2), " +
                                 "  'Campaign Count: ' + label.campaigns, " +
                                 "  'Utilization: ' + item.raw.y.toFixed(1) + '%'" +
                                 "]; }"
                    }
                }
            },
            "scales": {
                "y": {
                    "title": {
                        "display": True,
                        "text": "Utilization (%)"
                    }
                },
                "x": {
                    "title": {
                        "display": True,
                        "text": "Number of Campaigns"
                    }
                }
            }
        },
        "scriptVars": {
            "labels": hover_labels
        }
    }
    
    return chart_config

def create_budget_recommendation_chart(budget: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a chart visualizing current budget vs. recommended budget.
    
    Args:
        budget: Budget data dictionary including recommendation data
        
    Returns:
        Chart configuration for budget recommendation visualization
    """
    logger.info("Creating budget recommendation chart")
    
    # Check if the budget has a recommendation
    if not budget.get("has_recommended_budget", False):
        return {
            "type": "error",
            "message": "No recommendation available for this budget"
        }
    
    current_amount = budget.get("amount", 0)
    recommended_amount = budget.get("recommended_budget_amount", 0)
    
    # Create chart configuration
    chart_config = {
        "type": "bar",
        "data": {
            "labels": ["Current Budget", "Recommended Budget"],
            "datasets": [
                {
                    "label": "Budget Amount",
                    "data": [current_amount, recommended_amount],
                    "backgroundColor": ["rgba(54, 162, 235, 0.5)", "rgba(75, 192, 192, 0.5)"],
                    "borderColor": ["rgba(54, 162, 235, 1)", "rgba(75, 192, 192, 1)"],
                    "borderWidth": 1
                }
            ]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "title": {
                    "display": True,
                    "text": f"Budget Recommendation - {budget.get('name', 'Unknown Budget')}"
                },
                "tooltip": {
                    "callbacks": {
                        "label": "function(item) { return '$' + item.raw.toFixed(2); }"
                    }
                }
            },
            "scales": {
                "y": {
                    "beginAtZero": True,
                    "title": {
                        "display": True,
                        "text": "Amount ($)"
                    }
                }
            }
        }
    }
    
    return chart_config

def format_budget_for_visualization(budgets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Format budget data for visualization.
    
    Args:
        budgets: List of budget data dictionaries
        
    Returns:
        Collection of visualizations for budget data
    """
    logger.info(f"Formatting {len(budgets)} budgets for visualization")
    
    # Return early if no budgets
    if not budgets:
        return {
            "type": "error",
            "message": "No budget data available for visualization"
        }
    
    # Create various visualizations
    visualizations = {
        "utilization_chart": create_budget_utilization_chart(budgets),
        "performance_chart": create_budget_performance_chart(budgets)
    }
    
    # Add single budget visualizations for the first budget
    if len(budgets) > 0:
        budget = budgets[0]
        visualizations["distribution_chart"] = create_budget_distribution_chart(budget)
        
        if budget.get("has_recommended_budget", False):
            visualizations["recommendation_chart"] = create_budget_recommendation_chart(budget)
    
    # Create a summary table
    summary_table = {
        "headers": ["Budget Name", "Amount", "Spend", "Utilization", "Campaigns"],
        "rows": []
    }
    
    for budget in budgets:
        summary_table["rows"].append([
            budget.get("name", "Unknown"),
            f"${budget.get('amount', 0):,.2f}",
            f"${budget.get('current_spend', 0):,.2f}",
            f"{budget.get('utilization_percent', 0):.1f}%",
            len(budget.get("associated_campaigns", []))
        ])
    
    visualizations["summary_table"] = summary_table
    
    return visualizations 