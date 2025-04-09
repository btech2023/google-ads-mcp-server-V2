"""
Keyword Management Module

This module provides functionality for managing Google Ads keywords.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Import utilities
from google_ads_mcp_server.utils.logging import get_logger
from google_ads_mcp_server.utils.validation import (
    validate_customer_id,
    validate_ad_group_id,
    validate_campaign_id,
    validate_keyword_id,
    validate_enum,
    validate_date_format,
    validate_date_range,
    validate_list_not_empty,
    validate_list_of_strings,
    validate_list_of_dicts,
    validate_positive_integer,
    validate_string_length
)
from google_ads_mcp_server.utils.error_handler import (
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
from google_ads_mcp_server.utils.formatting import clean_customer_id, format_customer_id

logger = get_logger(__name__)

# Define constants for valid enum values
VALID_KEYWORD_STATUSES = ["ENABLED", "PAUSED", "REMOVED"]
VALID_KEYWORD_MATCH_TYPES = ["EXACT", "PHRASE", "BROAD"]

class KeywordService:
    """Service for managing Google Ads keywords."""
    
    def __init__(self, google_ads_service):
        """
        Initialize the Keyword service.
        
        Args:
            google_ads_service: The Google Ads service instance
        """
        self.google_ads_service = google_ads_service
        self.ga_service = google_ads_service.client.get_service("GoogleAdsService")
        logger.info("KeywordService initialized")
    
    async def get_keywords(self, customer_id: str, ad_group_id: Optional[str] = None, 
                          status_filter: Optional[str] = None, 
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get keywords for a customer, optionally filtered by ad_group_id and status.
        
        Args:
            customer_id: Google Ads customer ID
            ad_group_id: Optional ad group ID to filter by
            status_filter: Optional filter for keyword status (ENABLED, PAUSED, REMOVED)
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            List of keyword data with metrics
        """
        context = {
            "customer_id": customer_id,
            "ad_group_id": ad_group_id,
            "status_filter": status_filter,
            "start_date": start_date,
            "end_date": end_date,
            "method": "get_keywords"
        }

        try:
            # --- Validation ---
            validation_errors = []
            
            if not validate_customer_id(customer_id):
                validation_errors.append(f"Invalid customer ID format: {customer_id}")
            
            if ad_group_id and not validate_ad_group_id(ad_group_id):
                 validation_errors.append(f"Invalid ad_group_id format: {ad_group_id}")
            
            if status_filter and not validate_enum(status_filter, VALID_KEYWORD_STATUSES):
                validation_errors.append(f"Invalid status_filter: {status_filter}. Must be one of {VALID_KEYWORD_STATUSES}")

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

            logger.info(f"Getting keywords for customer ID {format_customer_id(cleaned_customer_id)} (AdGroup: {ad_group_id or 'All'})")

            # Get data from the Google Ads service
            keywords = await self.google_ads_service.get_keywords(
                start_date=start_date,
                end_date=end_date,
                ad_group_id=ad_group_id,
                status_filter=status_filter,
                customer_id=cleaned_customer_id
            )
            
            logger.info(f"Retrieved {len(keywords)} keywords")
            return keywords

        except ValueError as ve:
            error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
            logger.warning(f"Validation error getting keywords: {error_details.message}")
            raise ve
        except Exception as e:
            # Handle Google Ads API exceptions specifically
            if "GoogleAdsException" in str(type(e)):
                error_details = handle_google_ads_exception(e, context=context)
                logger.error(f"Google Ads API error getting keywords: {error_details.message}")
            else:
                error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
                logger.error(f"Error getting keywords: {error_details.message}")
                
            raise RuntimeError(f"Failed to get keywords: {error_details.message}") from e
    
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
    
    async def add_keywords(self, customer_id: str, ad_group_id: str, keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add keywords to an ad group.
        
        Args:
            customer_id: Google Ads customer ID
            ad_group_id: Ad group ID to add keywords to
            keywords: List of keyword specs, each containing:
                - text: Keyword text
                - match_type: Match type (EXACT, PHRASE, BROAD)
                - status: Status (ENABLED, PAUSED)
                - cpc_bid_micros: Optional CPC bid in micros
            
        Returns:
            Dictionary with creation results
        """
        context = {
            "customer_id": customer_id,
            "ad_group_id": ad_group_id,
            "keyword_count": len(keywords) if keywords else 0,
            "method": "add_keywords"
        }

        try:
            # --- Validation ---
            validation_errors = []
            
            if not validate_customer_id(customer_id):
                validation_errors.append(f"Invalid customer ID format: {customer_id}")
            
            if not validate_ad_group_id(ad_group_id):
                 validation_errors.append(f"Invalid ad_group_id format: {ad_group_id}")
            
            if not validate_list_of_dicts(keywords, required_keys=['text', 'match_type'], allow_empty=False):
                validation_errors.append("keywords must be a non-empty list of dictionaries, each with 'text' and 'match_type' keys")
                # Early return if the basic structure is invalid
                if validation_errors:
                    raise ValueError("; ".join(validation_errors))

            # Validate each keyword
            keyword_validation_errors = []
            validated_keywords = []
            
            for idx, kw in enumerate(keywords):
                keyword_errors = []
                
                # Validate keyword text - should not be too long (80 chars max for Google Ads)
                if not validate_string_length(kw.get('text', ''), min_length=1, max_length=80):
                    keyword_errors.append(f"Keyword text must be between 1-80 characters: '{kw.get('text', '')}'")
                
                # Validate match type
                if not validate_enum(kw.get('match_type', ''), VALID_KEYWORD_MATCH_TYPES):
                    keyword_errors.append(f"Invalid match_type '{kw.get('match_type', '')}'. Must be one of {VALID_KEYWORD_MATCH_TYPES}")
                
                # Validate status if provided
                if 'status' in kw and kw['status'] is not None and not validate_enum(kw['status'], VALID_KEYWORD_STATUSES):
                    keyword_errors.append(f"Invalid status '{kw['status']}'. Must be one of {VALID_KEYWORD_STATUSES}")
                
                # Validate bid if provided
                if 'cpc_bid_micros' in kw and kw['cpc_bid_micros'] is not None:
                    if not validate_positive_integer(kw['cpc_bid_micros']):
                        keyword_errors.append(f"Invalid cpc_bid_micros: must be a positive integer")
                
                # If any errors were found, add them to the validation errors list
                if keyword_errors:
                    keyword_validation_errors.append(f"Keyword at index {idx}: {', '.join(keyword_errors)}")
                else:
                    validated_keywords.append(kw)
            
            # Add keyword-specific validation errors if any
            if keyword_validation_errors:
                validation_errors.append("Keyword validation errors: " + "; ".join(keyword_validation_errors))
            
            # If there were any validation errors, raise ValueError with all errors
            if validation_errors:
                raise ValueError("; ".join(validation_errors))

            # Proceed with validated data
            cleaned_customer_id = clean_customer_id(customer_id)
            context["customer_id"] = cleaned_customer_id
            
            logger.info(f"Adding {len(validated_keywords)} keywords to ad group {ad_group_id} for customer ID {format_customer_id(cleaned_customer_id)}")

            # Add keywords using the GoogleAdsService
            result = await self.google_ads_service.add_keywords(
                customer_id=cleaned_customer_id,
                ad_group_id=ad_group_id,
                keywords=validated_keywords
            )
            
            success_count = len(result.get("successful_operations", []))
            error_count = len(result.get("failed_operations", []))
            logger.info(f"Added {success_count} keywords successfully with {error_count} failures")
            
            return result

        except ValueError as ve:
            error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
            logger.warning(f"Validation error adding keywords: {error_details.message}")
            raise ve
        except Exception as e:
            # Handle Google Ads API exceptions specifically
            if "GoogleAdsException" in str(type(e)):
                error_details = handle_google_ads_exception(e, context=context)
                logger.error(f"Google Ads API error adding keywords: {error_details.message}")
            else:
                error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
                logger.error(f"Error adding keywords: {error_details.message}")
                
            raise RuntimeError(f"Failed to add keywords: {error_details.message}") from e
    
    async def update_keywords(self, customer_id: str, keyword_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update existing keywords.
        
        Args:
            customer_id: Google Ads customer ID
            keyword_updates: List of keyword update specs, each containing:
                - id: Keyword criterion ID
                - status: Optional new status (ENABLED, PAUSED, REMOVED)
                - cpc_bid_micros: Optional new CPC bid in micros
            
        Returns:
            Dictionary with update results
        """
        context = {
            "customer_id": customer_id,
            "update_count": len(keyword_updates) if keyword_updates else 0,
            "method": "update_keywords"
        }

        try:
            # --- Validation ---
            validation_errors = []
            
            if not validate_customer_id(customer_id):
                validation_errors.append(f"Invalid customer ID format: {customer_id}")
            
            if not validate_list_of_dicts(keyword_updates, required_keys=['id'], allow_empty=False):
                validation_errors.append("keyword_updates must be a non-empty list of dictionaries, each with an 'id' key")
                # Early return if the basic structure is invalid
                if validation_errors:
                    raise ValueError("; ".join(validation_errors))

            # Validate each update
            update_validation_errors = []
            validated_updates = []
            
            for idx, update in enumerate(keyword_updates):
                update_errors = []
                
                # Validate keyword ID
                if not validate_keyword_id(update.get('id', '')):
                    update_errors.append(f"Invalid keyword id format: {update.get('id', '')}")
                
                # Validate status if provided
                if 'status' in update and update['status'] is not None:
                    if not validate_enum(update['status'], VALID_KEYWORD_STATUSES):
                        update_errors.append(f"Invalid status '{update['status']}'. Must be one of {VALID_KEYWORD_STATUSES}")
                
                # Validate bid if provided
                if 'cpc_bid_micros' in update and update['cpc_bid_micros'] is not None:
                    if not validate_positive_integer(update['cpc_bid_micros']):
                        update_errors.append(f"Invalid cpc_bid_micros: must be a positive integer")
                
                # Ensure at least one updateable field is provided
                if not any(k in update for k in ['status', 'cpc_bid_micros'] if update.get(k) is not None):
                    update_errors.append(f"No updateable fields (status, cpc_bid_micros) provided")
                
                # If any errors were found, add them to the validation errors list
                if update_errors:
                    update_validation_errors.append(f"Update at index {idx}: {', '.join(update_errors)}")
                else:
                    validated_updates.append(update)
            
            # Add update-specific validation errors if any
            if update_validation_errors:
                validation_errors.append("Keyword update validation errors: " + "; ".join(update_validation_errors))
            
            # If there were any validation errors, raise ValueError with all errors
            if validation_errors:
                raise ValueError("; ".join(validation_errors))

            # Proceed with validated data
            cleaned_customer_id = clean_customer_id(customer_id)
            context["customer_id"] = cleaned_customer_id
            
            logger.info(f"Updating {len(validated_updates)} keywords for customer ID {format_customer_id(cleaned_customer_id)}")

            # Update keywords using the GoogleAdsService
            result = await self.google_ads_service.update_keywords(
                customer_id=cleaned_customer_id,
                keyword_updates=validated_updates
            )
            
            success_count = len(result.get("successful_operations", []))
            error_count = len(result.get("failed_operations", []))
            logger.info(f"Updated {success_count} keywords successfully with {error_count} failures")
            
            return result

        except ValueError as ve:
            error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
            logger.warning(f"Validation error updating keywords: {error_details.message}")
            raise ve
        except Exception as e:
            # Handle Google Ads API exceptions specifically
            if "GoogleAdsException" in str(type(e)):
                error_details = handle_google_ads_exception(e, context=context)
                logger.error(f"Google Ads API error updating keywords: {error_details.message}")
            else:
                error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
                logger.error(f"Error updating keywords: {error_details.message}")
                
            raise RuntimeError(f"Failed to update keywords: {error_details.message}") from e
    
    async def remove_keywords(self, customer_id: str, keyword_ids: List[str]) -> Dict[str, Any]:
        """
        Remove keywords (set status to REMOVED).
        
        Args:
            customer_id: Google Ads customer ID
            keyword_ids: List of keyword criterion IDs to remove
            
        Returns:
            Dictionary with removal results
        """
        context = {
            "customer_id": customer_id,
            "keyword_id_count": len(keyword_ids) if keyword_ids else 0,
            "method": "remove_keywords"
        }

        try:
            # --- Validation ---
            validation_errors = []
            
            if not validate_customer_id(customer_id):
                validation_errors.append(f"Invalid customer ID format: {customer_id}")
            
            if not validate_list_not_empty(keyword_ids):
                 validation_errors.append("keyword_ids must be a non-empty list")
            elif not validate_list_of_strings(keyword_ids):
                 validation_errors.append("keyword_ids must contain only string values")
            else:
                # Validate individual keyword IDs
                id_validation_errors = []
                validated_ids = []
                
                for idx, kw_id in enumerate(keyword_ids):
                    if not validate_keyword_id(kw_id):
                        id_validation_errors.append(f"Keyword ID at index {idx}: Invalid format: {kw_id}")
                    else:
                        validated_ids.append(kw_id)
                
                # Add ID-specific validation errors if any
                if id_validation_errors:
                    validation_errors.append("Keyword ID validation errors: " + "; ".join(id_validation_errors))
            
            # If there were any validation errors, raise ValueError with all errors
            if validation_errors:
                raise ValueError("; ".join(validation_errors))

            # Proceed with validated data
            cleaned_customer_id = clean_customer_id(customer_id)
            context["customer_id"] = cleaned_customer_id
            
            logger.info(f"Removing {len(validated_ids)} keywords for customer ID {format_customer_id(cleaned_customer_id)}")

            # Remove keywords using the GoogleAdsService
            result = await self.google_ads_service.remove_keywords(
                customer_id=cleaned_customer_id,
                keyword_ids=validated_ids
            )
            
            success_count = len(result.get("successful_operations", []))
            error_count = len(result.get("failed_operations", []))
            logger.info(f"Removed {success_count} keywords successfully with {error_count} failures")
            
            return result

        except ValueError as ve:
            error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
            logger.warning(f"Validation error removing keywords: {error_details.message}")
            raise ve
        except Exception as e:
            # Handle Google Ads API exceptions specifically
            if "GoogleAdsException" in str(type(e)):
                error_details = handle_google_ads_exception(e, context=context)
                logger.error(f"Google Ads API error removing keywords: {error_details.message}")
            else:
                error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
                logger.error(f"Error removing keywords: {error_details.message}")
                
            raise RuntimeError(f"Failed to remove keywords: {error_details.message}") from e
