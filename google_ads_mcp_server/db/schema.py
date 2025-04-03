"""
SQLite Database Schema for Google Ads MCP Server

This module defines the SQLite database schema used for caching Google Ads API responses
and other persistent data storage needs in the Google Ads MCP Server.
"""

# SQL statements for creating tables

# Cache table for storing API responses
CREATE_API_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS api_cache (
    cache_key TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    query_type TEXT NOT NULL,
    query_hash TEXT NOT NULL,
    response_data TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    metadata TEXT
);
"""

# Create indexes for the api_cache table
CREATE_API_CACHE_CUSTOMER_INDEX = """
CREATE INDEX IF NOT EXISTS idx_api_cache_customer_id ON api_cache(customer_id);
"""

CREATE_API_CACHE_QUERY_TYPE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_api_cache_query_type ON api_cache(query_type);
"""

CREATE_API_CACHE_EXPIRY_INDEX = """
CREATE INDEX IF NOT EXISTS idx_api_cache_expires_at ON api_cache(expires_at);
"""

# Account KPI cache for dashboard and visualization data
CREATE_ACCOUNT_KPI_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS account_kpi_cache (
    cache_key TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    segmentation TEXT,
    kpi_data TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);
"""

CREATE_ACCOUNT_KPI_CACHE_ACCOUNT_INDEX = """
CREATE INDEX IF NOT EXISTS idx_account_kpi_cache_account_id ON account_kpi_cache(account_id);
"""

CREATE_ACCOUNT_KPI_CACHE_DATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_account_kpi_cache_dates ON account_kpi_cache(start_date, end_date);
"""

CREATE_ACCOUNT_KPI_CACHE_EXPIRY_INDEX = """
CREATE INDEX IF NOT EXISTS idx_account_kpi_cache_expires_at ON account_kpi_cache(expires_at);
"""

# Campaign data cache
CREATE_CAMPAIGN_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS campaign_cache (
    cache_key TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    campaign_id TEXT,
    start_date TEXT,
    end_date TEXT,
    campaign_data TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);
"""

CREATE_CAMPAIGN_CACHE_CUSTOMER_INDEX = """
CREATE INDEX IF NOT EXISTS idx_campaign_cache_customer_id ON campaign_cache(customer_id);
"""

CREATE_CAMPAIGN_CACHE_CAMPAIGN_INDEX = """
CREATE INDEX IF NOT EXISTS idx_campaign_cache_campaign_id ON campaign_cache(campaign_id);
"""

CREATE_CAMPAIGN_CACHE_EXPIRY_INDEX = """
CREATE INDEX IF NOT EXISTS idx_campaign_cache_expires_at ON campaign_cache(expires_at);
"""

# Keyword data cache
CREATE_KEYWORD_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS keyword_cache (
    cache_key TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    ad_group_id TEXT,
    start_date TEXT,
    end_date TEXT,
    keyword_data TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);
"""

CREATE_KEYWORD_CACHE_CUSTOMER_INDEX = """
CREATE INDEX IF NOT EXISTS idx_keyword_cache_customer_id ON keyword_cache(customer_id);
"""

CREATE_KEYWORD_CACHE_AD_GROUP_INDEX = """
CREATE INDEX IF NOT EXISTS idx_keyword_cache_ad_group_id ON keyword_cache(ad_group_id);
"""

CREATE_KEYWORD_CACHE_EXPIRY_INDEX = """
CREATE INDEX IF NOT EXISTS idx_keyword_cache_expires_at ON keyword_cache(expires_at);
"""

# Search terms data cache
CREATE_SEARCH_TERM_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS search_term_cache (
    cache_key TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    campaign_id TEXT,
    ad_group_id TEXT,
    start_date TEXT,
    end_date TEXT,
    search_term_data TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);
"""

CREATE_SEARCH_TERM_CACHE_CUSTOMER_INDEX = """
CREATE INDEX IF NOT EXISTS idx_search_term_cache_customer_id ON search_term_cache(customer_id);
"""

CREATE_SEARCH_TERM_CACHE_CAMPAIGN_INDEX = """
CREATE INDEX IF NOT EXISTS idx_search_term_cache_campaign_id ON search_term_cache(campaign_id);
"""

CREATE_SEARCH_TERM_CACHE_AD_GROUP_INDEX = """
CREATE INDEX IF NOT EXISTS idx_search_term_cache_ad_group_id ON search_term_cache(ad_group_id);
"""

CREATE_SEARCH_TERM_CACHE_EXPIRY_INDEX = """
CREATE INDEX IF NOT EXISTS idx_search_term_cache_expires_at ON search_term_cache(expires_at);
"""

# Budget data cache
CREATE_BUDGET_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS budget_cache (
    cache_key TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    budget_id TEXT,
    start_date TEXT,
    end_date TEXT,
    budget_data TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);
"""

CREATE_BUDGET_CACHE_CUSTOMER_INDEX = """
CREATE INDEX IF NOT EXISTS idx_budget_cache_customer_id ON budget_cache(customer_id);
"""

CREATE_BUDGET_CACHE_BUDGET_INDEX = """
CREATE INDEX IF NOT EXISTS idx_budget_cache_budget_id ON budget_cache(budget_id);
"""

CREATE_BUDGET_CACHE_EXPIRY_INDEX = """
CREATE INDEX IF NOT EXISTS idx_budget_cache_expires_at ON budget_cache(expires_at);
"""

# User tables for multi-user support
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    user_data TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_USER_ACCOUNT_ACCESS_TABLE = """
CREATE TABLE IF NOT EXISTS user_account_access (
    user_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    access_level TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, customer_id)
);
"""

CREATE_USER_ACCOUNT_ACCESS_USER_INDEX = """
CREATE INDEX IF NOT EXISTS idx_user_account_access_user_id ON user_account_access(user_id);
"""

CREATE_USER_ACCOUNT_ACCESS_CUSTOMER_INDEX = """
CREATE INDEX IF NOT EXISTS idx_user_account_access_customer_id ON user_account_access(customer_id);
"""

# Configuration tables
CREATE_SYSTEM_CONFIG_TABLE = """
CREATE TABLE IF NOT EXISTS system_config (
    config_key TEXT PRIMARY KEY,
    config_data TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_USER_CONFIG_TABLE = """
CREATE TABLE IF NOT EXISTS user_config (
    user_id TEXT NOT NULL,
    config_key TEXT NOT NULL,
    config_data TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, config_key)
);
"""

CREATE_USER_CONFIG_USER_INDEX = """
CREATE INDEX IF NOT EXISTS idx_user_config_user_id ON user_config(user_id);
"""

# Collect all creation statements
ALL_TABLES = [
    CREATE_API_CACHE_TABLE,
    CREATE_ACCOUNT_KPI_CACHE_TABLE,
    CREATE_CAMPAIGN_CACHE_TABLE,
    CREATE_KEYWORD_CACHE_TABLE,
    CREATE_SEARCH_TERM_CACHE_TABLE,
    CREATE_BUDGET_CACHE_TABLE,
]

CREATE_USER_TABLES_SQL = [
    CREATE_USERS_TABLE,
    CREATE_USER_ACCOUNT_ACCESS_TABLE,
]

CREATE_CONFIG_TABLES_SQL = [
    CREATE_SYSTEM_CONFIG_TABLE,
    CREATE_USER_CONFIG_TABLE,
]

ALL_INDEXES = [
    CREATE_API_CACHE_CUSTOMER_INDEX,
    CREATE_API_CACHE_QUERY_TYPE_INDEX,
    CREATE_API_CACHE_EXPIRY_INDEX,
    CREATE_ACCOUNT_KPI_CACHE_ACCOUNT_INDEX,
    CREATE_ACCOUNT_KPI_CACHE_DATE_INDEX,
    CREATE_ACCOUNT_KPI_CACHE_EXPIRY_INDEX,
    CREATE_CAMPAIGN_CACHE_CUSTOMER_INDEX,
    CREATE_CAMPAIGN_CACHE_CAMPAIGN_INDEX,
    CREATE_CAMPAIGN_CACHE_EXPIRY_INDEX,
    CREATE_KEYWORD_CACHE_CUSTOMER_INDEX,
    CREATE_KEYWORD_CACHE_AD_GROUP_INDEX,
    CREATE_KEYWORD_CACHE_EXPIRY_INDEX,
    CREATE_SEARCH_TERM_CACHE_CUSTOMER_INDEX,
    CREATE_SEARCH_TERM_CACHE_CAMPAIGN_INDEX,
    CREATE_SEARCH_TERM_CACHE_AD_GROUP_INDEX,
    CREATE_SEARCH_TERM_CACHE_EXPIRY_INDEX,
    CREATE_BUDGET_CACHE_CUSTOMER_INDEX,
    CREATE_BUDGET_CACHE_BUDGET_INDEX,
    CREATE_BUDGET_CACHE_EXPIRY_INDEX,
    CREATE_USER_ACCOUNT_ACCESS_USER_INDEX,
    CREATE_USER_ACCOUNT_ACCESS_CUSTOMER_INDEX,
    CREATE_USER_CONFIG_USER_INDEX,
]

# Query to clean up expired cache entries
CLEAN_EXPIRED_CACHE = """
DELETE FROM {table} WHERE expires_at < datetime('now', 'utc');
"""

# Query to get cache statistics
GET_CACHE_STATS = """
SELECT
    (SELECT COUNT(*) FROM api_cache) AS api_cache_count,
    (SELECT COUNT(*) FROM account_kpi_cache) AS account_kpi_cache_count,
    (SELECT COUNT(*) FROM campaign_cache) AS campaign_cache_count,
    (SELECT COUNT(*) FROM keyword_cache) AS keyword_cache_count,
    (SELECT COUNT(*) FROM search_term_cache) AS search_term_cache_count,
    (SELECT COUNT(*) FROM budget_cache) AS budget_cache_count;
"""

# Dictionary mapping entity types to their cache tables
CACHE_TABLES = {
    'api': 'api_cache',
    'account_kpi': 'account_kpi_cache',
    'campaign': 'campaign_cache',
    'keyword': 'keyword_cache',
    'search_term': 'search_term_cache',
    'budget': 'budget_cache',
} 