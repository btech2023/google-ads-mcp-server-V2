"""
Search Term Analysis Module

This module provides functionality for analyzing Google Ads search terms.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Import utilities
from ..utils.logging import get_logger
from ..utils.validation import (
    validate_customer_id,
    validate_campaign_id,
    validate_ad_group_id,
    validate_date_format,
    validate_date_range,
    validate_numeric_range,
    validate_positive_integer
)
from ..utils.error_handler import (
    handle_exception,
    handle_google_ads_exception,
    create_error_response,
    ErrorDetails,
    CATEGORY_BUSINESS_LOGIC,
    CATEGORY_API_ERROR,
    CATEGORY_VALIDATION,
    SEVERITY_ERROR,
    SEVERITY_WARNING
)
from ..utils.formatting import clean_customer_id, format_customer_id

logger = get_logger(__name__)

class SearchTermService:
    """Service for analyzing Google Ads search terms."""
    
    def __init__(self, google_ads_service):
        """
        Initialize the Search Term service.
        
        Args:
            google_ads_service: The Google Ads service instance
        """
        self.google_ads_service = google_ads_service
        self.ga_service = google_ads_service.client.get_service("GoogleAdsService")
        logger.info("SearchTermService initialized")
    
    async def get_search_terms(self, customer_id: str, campaign_id: Optional[str] = None,
                              ad_group_id: Optional[str] = None,
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get search terms report for a customer, optionally filtered by campaign_id and ad_group_id.
        
        Args:
            customer_id: Google Ads customer ID
            campaign_id: Optional campaign ID to filter by
            ad_group_id: Optional ad group ID to filter by
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            List of search term data with metrics
        """
        context = {
            "customer_id": customer_id,
            "campaign_id": campaign_id,
            "ad_group_id": ad_group_id,
            "start_date": start_date,
            "end_date": end_date,
            "method": "get_search_terms"
        }

        try:
            # --- Validation ---
            validation_errors = []
            
            if not validate_customer_id(customer_id):
                validation_errors.append(f"Invalid customer ID format: {customer_id}")
            
            if campaign_id and not validate_campaign_id(campaign_id):
                validation_errors.append(f"Invalid campaign_id format: {campaign_id}")
            
            if ad_group_id and not validate_ad_group_id(ad_group_id):
                validation_errors.append(f"Invalid ad_group_id format: {ad_group_id}")

            # Calculate default date range if not provided
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                
            # Validate dates
            if not validate_date_format(start_date):
                validation_errors.append(f"Invalid start_date format: {start_date}")
            elif not validate_date_format(end_date):
                validation_errors.append(f"Invalid end_date format: {end_date}")
            elif not validate_date_range(start_date, end_date):
                validation_errors.append(f"Invalid date range: {start_date} to {end_date}")

            # If validation errors found, raise ValueError with all errors
            if validation_errors:
                raise ValueError("; ".join(validation_errors))
            
            # Proceed with validated data
            cleaned_customer_id = clean_customer_id(customer_id)
            context["customer_id"] = cleaned_customer_id
            context["start_date"] = start_date
            context["end_date"] = end_date

            logger.info(f"Getting search terms for customer ID {format_customer_id(cleaned_customer_id)} (Campaign: {campaign_id or 'All'}, AdGroup: {ad_group_id or 'All'})")

            # Get data from the Google Ads service
            search_terms = await self.google_ads_service.get_search_terms_report(
                start_date=start_date,
                end_date=end_date,
                campaign_id=campaign_id,
                ad_group_id=ad_group_id,
                customer_id=cleaned_customer_id
            )
            
            logger.info(f"Retrieved {len(search_terms)} search terms")
            return search_terms

        except ValueError as ve:
            error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
            logger.warning(f"Validation error getting search terms: {error_details.message}")
            raise ve
        except Exception as e:
            # Handle Google Ads API exceptions specifically
            if "GoogleAdsException" in str(type(e)):
                error_details = handle_google_ads_exception(e, context=context)
                logger.error(f"Google Ads API error getting search terms: {error_details.message}")
            else:
                error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
                logger.error(f"Error getting search terms: {error_details.message}")
            
            raise RuntimeError(f"Failed to get search terms: {error_details.message}") from e
    
    async def analyze_search_terms(self, customer_id: str, campaign_id: Optional[str] = None,
                                  ad_group_id: Optional[str] = None,
                                  start_date: Optional[str] = None,
                                  end_date: Optional[str] = None,
                                  min_impressions: Optional[int] = 100,
                                  min_clicks: Optional[int] = 10,
                                  ctr_threshold_multiplier: Optional[float] = 0.5,
                                  cost_threshold_multiplier: Optional[float] = 3.0) -> Dict[str, Any]:
        """
        Analyze search terms and provide insights.
        
        Args:
            customer_id: Google Ads customer ID
            campaign_id: Optional campaign ID to filter by
            ad_group_id: Optional ad group ID to filter by
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            min_impressions: Minimum impressions to consider for negative keyword suggestions (default: 100)
            min_clicks: Minimum clicks to consider for negative keyword suggestions (default: 10)
            ctr_threshold_multiplier: Multiplier for CTR threshold (default: 0.5 = 50% of average)
            cost_threshold_multiplier: Multiplier for CPC threshold (default: 3.0 = 300% of average)
            
        Returns:
            Dictionary with search term analysis and insights
        """
        context = {
            "customer_id": customer_id,
            "campaign_id": campaign_id,
            "ad_group_id": ad_group_id,
            "start_date": start_date,
            "end_date": end_date,
            "min_impressions": min_impressions,
            "min_clicks": min_clicks,
            "ctr_threshold_multiplier": ctr_threshold_multiplier,
            "cost_threshold_multiplier": cost_threshold_multiplier,
            "method": "analyze_search_terms"
        }

        try:
            # --- Additional Validation ---
            validation_errors = []
            
            # Customer ID validation
            if not validate_customer_id(customer_id):
                validation_errors.append(f"Invalid customer ID format: {customer_id}")
            
            # IDs validation if provided
            if campaign_id and not validate_campaign_id(campaign_id):
                validation_errors.append(f"Invalid campaign_id format: {campaign_id}")
            
            if ad_group_id and not validate_ad_group_id(ad_group_id):
                validation_errors.append(f"Invalid ad_group_id format: {ad_group_id}")
            
            # Threshold validation
            if min_impressions is not None and not validate_positive_integer(min_impressions):
                validation_errors.append(f"min_impressions must be a positive integer: {min_impressions}")
            
            if min_clicks is not None and not validate_positive_integer(min_clicks):
                validation_errors.append(f"min_clicks must be a positive integer: {min_clicks}")
                
            if ctr_threshold_multiplier is not None and not validate_numeric_range(ctr_threshold_multiplier, min_value=0.0):
                validation_errors.append(f"ctr_threshold_multiplier must be a non-negative number: {ctr_threshold_multiplier}")
                
            if cost_threshold_multiplier is not None and not validate_numeric_range(cost_threshold_multiplier, min_value=0.0):
                validation_errors.append(f"cost_threshold_multiplier must be a non-negative number: {cost_threshold_multiplier}")
            
            # If validation errors found, raise ValueError with all errors
            if validation_errors:
                raise ValueError("; ".join(validation_errors))

            # Set default values if None
            min_impressions = 100 if min_impressions is None else min_impressions
            min_clicks = 10 if min_clicks is None else min_clicks
            ctr_threshold_multiplier = 0.5 if ctr_threshold_multiplier is None else ctr_threshold_multiplier
            cost_threshold_multiplier = 3.0 if cost_threshold_multiplier is None else cost_threshold_multiplier
            
            # Update context with validated values
            context.update({
                "min_impressions": min_impressions,
                "min_clicks": min_clicks,
                "ctr_threshold_multiplier": ctr_threshold_multiplier,
                "cost_threshold_multiplier": cost_threshold_multiplier
            })

            # If customer_id is valid, clean it for logging
            cleaned_customer_id = clean_customer_id(customer_id)
            logger.info(f"Analyzing search terms for customer ID {format_customer_id(cleaned_customer_id)}")

            # Get search terms data (This call includes validation and error handling)
            try:
                search_terms = await self.get_search_terms(
                    customer_id=customer_id,
                    campaign_id=campaign_id,
                    ad_group_id=ad_group_id,
                    start_date=start_date,
                    end_date=end_date
                )
            except ValueError as ve:
                # Re-raise validation errors with proper context
                error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
                raise ValueError(f"Failed to analyze search terms: {error_details.message}")
            except Exception as e:
                # Wrap any other errors from get_search_terms
                error_details = handle_exception(e, context=context)
                raise RuntimeError(f"Failed to retrieve data for search term analysis: {error_details.message}")
            
            if not search_terms:
                logger.info(f"No search terms found for analysis for customer ID {format_customer_id(cleaned_customer_id)}")
                return {
                    "total_search_terms": 0,
                    "total_impressions": 0,
                    "total_clicks": 0,
                    "total_cost": 0,
                    "total_conversions": 0,
                    "average_cpc": 0,
                    "average_ctr": 0,
                    "average_conversion_rate": 0,
                    "top_performing_terms": [],
                    "low_performing_terms": [],
                    "potential_negative_keywords": []
                }
            
            # Calculate totals - with defensive programming for missing keys
            total_impressions = sum(term.get("impressions", 0) for term in search_terms)
            total_clicks = sum(term.get("clicks", 0) for term in search_terms)
            total_cost = sum(term.get("cost", 0) for term in search_terms)
            total_conversions = sum(term.get("conversions", 0) for term in search_terms)
            
            # Calculate averages - handle division by zero
            average_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
            average_cpc = (total_cost / total_clicks) if total_clicks > 0 else 0
            average_conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
            
            # Sort search terms by different metrics - handle missing keys
            by_clicks = sorted(search_terms, key=lambda x: x.get("clicks", 0), reverse=True)
            by_cost = sorted(search_terms, key=lambda x: x.get("cost", 0), reverse=True)
            by_conversions = sorted(search_terms, key=lambda x: x.get("conversions", 0), reverse=True)
            by_ctr = sorted(search_terms, key=lambda x: x.get("ctr", 0), reverse=True)
            
            # Identify top performing terms (high conversions or high CTR)
            top_performing = []
            for term in by_conversions[:10]:  # Top 10 by conversions
                if term.get("conversions", 0) > 0:
                    top_performing.append(term)
                    
            if len(top_performing) < 5:  # Add more from top CTR if needed
                for term in by_ctr[:10]:
                    if term not in top_performing and term.get("ctr", 0) > average_ctr * 1.5:
                        top_performing.append(term)
                        if len(top_performing) >= 5:
                            break
            
            # Identify low performing terms (high cost, low conversions)
            low_performing = []
            for term in by_cost[:20]:  # From top 20 by cost
                if term.get("conversions", 0) == 0 and term.get("cost", 0) > average_cpc * cost_threshold_multiplier:
                    low_performing.append(term)
                    if len(low_performing) >= 5:
                        break
            
            # Identify potential negative keywords (zero conversions, lots of impressions, low CTR)
            potential_negatives = []
            for term in search_terms:
                if (term.get("conversions", 0) == 0 and 
                    term.get("impressions", 0) > min_impressions and 
                    term.get("clicks", 0) > min_clicks and 
                    term.get("ctr", 0) < average_ctr * ctr_threshold_multiplier):
                    potential_negatives.append(term)
                    if len(potential_negatives) >= 5:
                        break
            
            logger.info(f"Completed search term analysis for customer ID {format_customer_id(cleaned_customer_id)} - found {len(search_terms)} terms")
            
            return {
                "total_search_terms": len(search_terms),
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "total_cost": total_cost,
                "total_conversions": total_conversions,
                "average_cpc": average_cpc,
                "average_ctr": average_ctr,
                "average_conversion_rate": average_conversion_rate,
                "top_performing_terms": top_performing[:5],
                "low_performing_terms": low_performing[:5],
                "potential_negative_keywords": potential_negatives[:5]
            }

        except ValueError as ve:
            # Format validation errors with proper context
            error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
            logger.warning(f"Validation error during search term analysis: {error_details.message}")
            raise ve
        except Exception as e:
            # Handle all other errors
            error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
            logger.error(f"Error analyzing search terms: {error_details.message}")
            raise RuntimeError(f"Failed to analyze search terms: {error_details.message}") from e 