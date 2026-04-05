import time
from typing import Optional

from flask import g, request
from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "route", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "route", "status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

HTTP_REQUEST_ERRORS_TOTAL = Counter(
    "http_request_errors_total",
    "Total HTTP error responses",
    ["method", "route", "status", "error_type"],
)

DB_QUERY_DURATION_SECONDS = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

DB_ERRORS_TOTAL = Counter(
    "db_errors_total",
    "Total database errors",
    ["operation", "error_type"],
)

DB_POOL_IN_USE = Gauge(
    "db_pool_in_use",
    "Number of DB connections currently in use",
)

DB_POOL_AVAILABLE = Gauge(
    "db_pool_available",
    "Estimated available DB connections in pool",
)

DB_RETRY_ATTEMPTS_TOTAL = Counter(
    "db_retry_attempts_total",
    "Total database retry attempts",
    ["function_name", "error_type"],
)

DB_RETRIES_EXHAUSTED_TOTAL = Counter(
    "db_retries_exhausted_total",
    "Total exhausted retries for DB operations",
    ["function_name", "error_type"],
)

DB_RETRY_BACKOFF_SECONDS = Histogram(
    "db_retry_backoff_seconds",
    "Database retry backoff duration in seconds",
    ["function_name"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0),
)

CACHE_OPERATIONS_TOTAL = Counter(
    "cache_operations_total",
    "Total cache operations by result",
    ["operation", "result"],
)

CACHE_OPERATION_DURATION_SECONDS = Histogram(
    "cache_operation_duration_seconds",
    "Cache operation duration in seconds",
    ["operation", "result"],
    buckets=(0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1),
)

CACHE_HITS_TOTAL = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_name"],
)

CACHE_MISSES_TOTAL = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_name"],
)

SHORT_URL_CREATE_TOTAL = Counter(
    "short_url_create_total",
    "Total short URLs created",
)

SHORT_URL_REDIRECT_TOTAL = Counter(
    "short_url_redirect_total",
    "Total short URL redirects",
)

SHORT_URL_NOT_FOUND_TOTAL = Counter(
    "short_url_not_found_total",
    "Total short URL not found responses",
)

def _route_label() -> str:
    if request.url_rule and request.url_rule.rule:
        return request.url_rule.rule
    return request.path

def setup_http_metrics(app) -> None:
    @app.before_request
    def _metrics_before_request() -> None:
        g.request_started_at = time.perf_counter()

    @app.after_request
    def _metrics_after_request(response):
        started = getattr(g, "request_started_at", None)
        if started is None:
            return response

        route = _route_label()
        if route in ("/metrics", "/health", "/ready"):
            return response

        duration = time.perf_counter() - started
        method = request.method
        status = str(response.status_code)

        HTTP_REQUESTS_TOTAL.labels(method=method, route=route, status=status).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(method=method, route=route, status=status).observe(duration)

        if response.status_code >= 400:
            error_type = "client_error" if response.status_code < 500 else "server_error"
            HTTP_REQUEST_ERRORS_TOTAL.labels(
                method=method,
                route=route,
                status=status,
                error_type=error_type,
            ).inc()

        return response

def observe_db_pool_state(pool) -> None:
    in_use = len(getattr(pool, "_in_use", []))
    max_connections: Optional[int] = getattr(pool, "_max_connections", None)
    available = max(max_connections - in_use, 0) if isinstance(max_connections, int) else 0

    DB_POOL_IN_USE.set(in_use)
    DB_POOL_AVAILABLE.set(available)
