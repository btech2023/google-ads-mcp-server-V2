#!/usr/bin/env python
"""
Configuration management for Google Ads MCP Server
"""

import os
import logging
from enum import Enum
from typing import Dict, Any, Optional

logger = logging.getLogger("config-manager")

class Environment(Enum):
    """Environment types supported by the application."""
    DEV = "dev"
    TEST = "test"
    PROD = "prod"

class Config:
    """Configuration manager for the Google Ads MCP Server."""
    
    def __init__(self):
        """Initialize the configuration manager."""
        self.env_name = os.environ.get("APP_ENV", "dev")
        self.env = Environment(self.env_name)
        self.settings = self._load_settings()
        
        logger.info(f"Loaded configuration for {self.env.value} environment")
    
    def _load_settings(self) -> Dict[str, Any]:
        """
        Load settings based on environment.
        
        Returns:
            Dict of configuration settings
        """
        # Common settings across all environments
        common_settings = {
            "app_name": "Google Ads MCP Server",
            "version": os.environ.get("APP_VERSION", "1.0.0"),
            "port": int(os.environ.get("PORT", "8000")),
            "log_level": os.environ.get("LOG_LEVEL", "INFO"),
            "cache_enabled": os.environ.get("CACHE_ENABLED", "true").lower() == "true",
            "cache_ttl": int(os.environ.get("CACHE_TTL", "3600")),
        }
        
        # Environment-specific settings
        env_specific_settings = {
            Environment.DEV: {
                "debug": True,
                "allow_cors": True,
                "cors_origins": ["*"],
                "rate_limit_enabled": False,
            },
            Environment.TEST: {
                "debug": True,
                "allow_cors": True,
                "cors_origins": ["*"],
                "rate_limit_enabled": True,
                "rate_limit_requests": 120,  # requests per minute
            },
            Environment.PROD: {
                "debug": False,
                "allow_cors": True,
                "cors_origins": ["https://claude.ai", "https://app.claude.ai"],
                "rate_limit_enabled": True,
                "rate_limit_requests": 60,  # requests per minute
            }
        }
        
        # Feature flags
        feature_flags = {
            "enable_account_hierarchy": os.environ.get("ENABLE_ACCOUNT_HIERARCHY", "true").lower() == "true",
            "enable_detailed_reporting": os.environ.get("ENABLE_DETAILED_REPORTING", "true").lower() == "true",
            "enable_claude_artifacts": os.environ.get("ENABLE_CLAUDE_ARTIFACTS", "true").lower() == "true",
        }
        
        # Merge settings
        settings = common_settings.copy()
        settings.update(env_specific_settings[self.env])
        settings["features"] = feature_flags
        
        return settings
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key
            default: Default value if key is not found
            
        Returns:
            Configuration value
        """
        return self.settings.get(key, default)
    
    def feature_enabled(self, feature_name: str) -> bool:
        """
        Check if a feature is enabled.
        
        Args:
            feature_name: The name of the feature
            
        Returns:
            True if feature is enabled, False otherwise
        """
        return self.settings.get("features", {}).get(feature_name, False)

# Singleton instance
config = Config() 