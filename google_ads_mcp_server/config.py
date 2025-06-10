#!/usr/bin/env python
# flake8: noqa
"""
Configuration Module

This module manages application configuration, loading from environment variables
with reasonable defaults.
"""

import os
import logging
from enum import Enum
from typing import Dict, Any, Optional

from dotenv import load_dotenv, find_dotenv

# Load environment variables early so APP_ENV is available when the
# configuration instance is created. find_dotenv searches parent
# directories to locate the .env file regardless of the current
# working directory.
load_dotenv(find_dotenv())

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
        # General configuration
        DEBUG = os.environ.get("DEBUG", "false").lower() in ("true", "1", "yes")
        LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

        # Cache configuration
        USE_CACHE = os.environ.get("USE_CACHE", "true").lower() in ("true", "1", "yes")
        CACHE_TTL = int(os.environ.get("CACHE_TTL", "3600"))  # 1 hour default

        # Database configuration
        DB_TYPE = os.environ.get("DB_TYPE", "sqlite")
        DB_PATH = os.environ.get("DB_PATH")  # For SQLite

        # PostgreSQL configuration
        POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
        POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", "5432"))
        POSTGRES_DATABASE = os.environ.get("POSTGRES_DATABASE")
        POSTGRES_USER = os.environ.get("POSTGRES_USER")
        POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
        POSTGRES_SSL_MODE = os.environ.get("POSTGRES_SSL_MODE", "prefer")

        # API configuration
        API_HOST = os.environ.get("API_HOST", "0.0.0.0")
        API_PORT = int(os.environ.get("API_PORT", "8000"))

        # Google Ads configuration
        GOOGLE_ADS_CONFIG_PATH = os.environ.get("GOOGLE_ADS_CONFIG_PATH")
        GOOGLE_ADS_LOGIN_CUSTOMER_ID = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
        GOOGLE_ADS_CLIENT_CUSTOMER_ID = os.environ.get("GOOGLE_ADS_CLIENT_CUSTOMER_ID")

        # Common settings across all environments
        common_settings = {
            "app_name": "Google Ads MCP Server",
            "version": os.environ.get("APP_VERSION", "1.0.0"),
            "port": API_PORT,
            "log_level": LOG_LEVEL,
            "cache_enabled": USE_CACHE,
            "cache_ttl": CACHE_TTL,
            "debug": DEBUG,
            "allow_cors": True,
            "cors_origins": ["*"],
            "rate_limit_enabled": False,
            "rate_limit_requests": 0,  # Default rate limit
            "enable_account_hierarchy": False,
            "enable_detailed_reporting": False,
            "enable_claude_artifacts": False,
            "db_type": DB_TYPE,
            "db_path": DB_PATH,
            "postgres_host": POSTGRES_HOST,
            "postgres_port": POSTGRES_PORT,
            "postgres_database": POSTGRES_DATABASE,
            "postgres_user": POSTGRES_USER,
            "postgres_password": POSTGRES_PASSWORD,
            "postgres_ssl_mode": POSTGRES_SSL_MODE,
            "api_host": API_HOST,
            "api_port": API_PORT,
            "google_ads_config_path": GOOGLE_ADS_CONFIG_PATH,
            "google_ads_login_customer_id": GOOGLE_ADS_LOGIN_CUSTOMER_ID,
            "google_ads_client_customer_id": GOOGLE_ADS_CLIENT_CUSTOMER_ID,
        }
        
        # Environment-specific settings
        env_specific_settings = {
            Environment.DEV: {
                "rate_limit_enabled": False,
            },
            Environment.TEST: {
                "rate_limit_enabled": True,
                "rate_limit_requests": 120,  # requests per minute
            },
            Environment.PROD: {
                "rate_limit_enabled": True,
                "rate_limit_requests": 60,  # requests per minute
            }
        }
        
        # Merge settings
        settings = common_settings.copy()
        settings.update(env_specific_settings[self.env])
        
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

def get_database_config() -> Dict[str, Any]:
    """
    Get database configuration based on DB_TYPE.
    
    Returns:
        Dictionary with database configuration parameters
    """
    if config.get("db_type") == "sqlite":
        return {
            "db_path": config.get("db_path"),
            "auto_clean_interval": int(os.environ.get("DB_AUTO_CLEAN_INTERVAL", "3600"))
        }
    elif config.get("db_type") == "postgres":
        # Only include non-None values
        db_config = {}
        if config.get("postgres_host"):
            db_config["host"] = config.get("postgres_host")
        if config.get("postgres_port"):
            db_config["port"] = config.get("postgres_port")
        if config.get("postgres_database"):
            db_config["database"] = config.get("postgres_database")
        if config.get("postgres_user"):
            db_config["user"] = config.get("postgres_user")
        if config.get("postgres_password"):
            db_config["password"] = config.get("postgres_password")
        if config.get("postgres_ssl_mode"):
            db_config["ssl_mode"] = config.get("postgres_ssl_mode")
            
        # Add pool configuration if specified
        pool_min = os.environ.get("POSTGRES_POOL_MIN_SIZE")
        if pool_min:
            db_config["pool_min_size"] = int(pool_min)
        pool_max = os.environ.get("POSTGRES_POOL_MAX_SIZE")
        if pool_max:
            db_config["pool_max_size"] = int(pool_max)
            
        return db_config
    else:
        raise ValueError(f"Unsupported database type: {config.get('db_type')}")
        
def get_google_ads_client_config() -> Dict[str, Any]:
    """
    Get Google Ads client configuration.
    
    Returns:
        Dictionary with Google Ads client configuration parameters
    """
    return {
        "use_cache": config.get("cache_enabled"),
        "cache_ttl": config.get("cache_ttl"),
        "db_type": config.get("db_type"),
        "db_config": get_database_config()
    } 