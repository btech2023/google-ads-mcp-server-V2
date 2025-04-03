#!/usr/bin/env python
"""
Monitoring and observability module for Google Ads MCP Server.
This module configures OpenTelemetry and Prometheus metrics.
"""

import os
import time
import logging
from typing import Callable, Dict, Any

# OpenTelemetry
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

# Prometheus
from prometheus_client import Counter, Histogram, Gauge, Info, REGISTRY, PROCESS_COLLECTOR, PLATFORM_COLLECTOR
from prometheus_fastapi_instrumentator import Instrumentator, metrics as prom_metrics

# Structured logging
import structlog
from structlog.contextvars import merge_contextvars

# Logger
logger = logging.getLogger("monitoring")

# Global metrics
# Google Ads API metrics
GOOGLE_ADS_REQUESTS = Counter(
    "google_ads_mcp_google_ads_requests_total",
    "Total Google Ads API requests",
    ["endpoint", "status"]
)

GOOGLE_ADS_REQUEST_LATENCY = Histogram(
    "google_ads_mcp_google_ads_request_duration_seconds",
    "Google Ads API request duration in seconds",
    ["endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 30.0, 60.0)
)

# MCP server metrics
MCP_REQUESTS = Counter(
    "google_ads_mcp_mcp_requests_total",
    "Total MCP requests",
    ["tool", "status"]
)

MCP_REQUEST_LATENCY = Histogram(
    "google_ads_mcp_mcp_request_duration_seconds",
    "MCP request duration in seconds",
    ["tool"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 30.0, 60.0)
)

# Service health metrics
SERVICE_INFO = Info(
    "google_ads_mcp_service_info",
    "Information about the Google Ads MCP service"
)

CACHE_HITS = Counter(
    "google_ads_mcp_cache_hits_total",
    "Total cache hits"
)

CACHE_MISSES = Counter(
    "google_ads_mcp_cache_misses_total",
    "Total cache misses"
)

HEALTH_CHECK_UP = Gauge(
    "google_ads_mcp_health_check_up",
    "Health check status (1 = UP, 0 = DOWN)"
)


def init_monitoring(app, app_name: str = "google-ads-mcp-server"):
    """
    Initialize all monitoring components for the application.
    
    Args:
        app: FastAPI application to instrument
        app_name: Name of the application for telemetry
    """
    app_version = os.environ.get("APP_VERSION", "1.0.0")
    app_env = os.environ.get("APP_ENV", "dev")
    
    # Set service info for Prometheus
    SERVICE_INFO.info({
        "version": app_version,
        "environment": app_env,
        "name": app_name
    })
    
    # Configure OpenTelemetry if enabled
    if os.environ.get("ENABLE_OTEL", "false").lower() == "true":
        logger.info("Initializing OpenTelemetry...")
        _init_opentelemetry(app, app_name, app_version, app_env)
    
    # Configure Prometheus metrics
    logger.info("Initializing Prometheus metrics...")
    _init_prometheus(app)
    
    # Configure structured logging
    logger.info("Initializing structured logging...")
    _init_structured_logging(app_name, app_version, app_env)
    
    logger.info("Monitoring initialization complete")


def _init_opentelemetry(app, app_name, app_version, app_env):
    """Initialize OpenTelemetry tracing and metrics."""
    # Create resource with service info
    resource = Resource.create({
        SERVICE_NAME: app_name,
        "service.version": app_version,
        "environment": app_env
    })
    
    # Set up tracing
    trace_provider = TracerProvider(resource=resource)
    
    # Configure exporters based on environment variables
    otel_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    
    if otel_endpoint:
        # Set up OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=otel_endpoint)
        trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Register the tracer provider
    trace.set_tracer_provider(trace_provider)
    
    # Set up metrics if endpoint is configured
    if otel_endpoint:
        # Create metrics provider
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=otel_endpoint),
            export_interval_millis=60000  # Export metrics every 60 seconds
        )
        metrics_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(metrics_provider)
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument HTTPX for outgoing requests
    HTTPXClientInstrumentor().instrument()


def _init_prometheus(app):
    """Initialize Prometheus metrics for FastAPI."""
    # Create instrumentator
    instrumentator = Instrumentator()
    
    # Add default metrics
    instrumentator.add(
        prom_metrics.latency(
            metric_name="google_ads_mcp_http_request_duration_seconds",
            buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 30.0, 60.0)
        )
    )
    instrumentator.add(
        prom_metrics.requests(
            metric_name="google_ads_mcp_http_requests_total"
        )
    )
    
    # Instrument app and expose metrics endpoint
    instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=True)


def _init_structured_logging(app_name, app_version, app_env):
    """Initialize structured logging with structlog."""
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    
    # Set global context variables
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        service=app_name,
        version=app_version,
        environment=app_env
    )


# Monitoring decorator for Google Ads API calls
def monitor_google_ads_api(endpoint: str) -> Callable:
    """
    Decorator to monitor Google Ads API calls.
    
    Args:
        endpoint: The Google Ads API endpoint being called
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                GOOGLE_ADS_REQUESTS.labels(endpoint=endpoint, status=status).inc()
                GOOGLE_ADS_REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
                
        return wrapper
    return decorator


# Monitoring decorator for MCP tools
def monitor_mcp_tool(tool_name: str) -> Callable:
    """
    Decorator to monitor MCP tool executions.
    
    Args:
        tool_name: The name of the MCP tool being executed
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                MCP_REQUESTS.labels(tool=tool_name, status=status).inc()
                MCP_REQUEST_LATENCY.labels(tool=tool_name).observe(duration)
                
        return wrapper
    return decorator


# Cache monitoring functions
def record_cache_hit():
    """Record a cache hit."""
    CACHE_HITS.inc()


def record_cache_miss():
    """Record a cache miss."""
    CACHE_MISSES.inc()


# Health check monitoring
def update_health_status(is_up: bool):
    """
    Update the health check status metric.
    
    Args:
        is_up: True if the service is healthy, False otherwise
    """
    HEALTH_CHECK_UP.set(1 if is_up else 0) 