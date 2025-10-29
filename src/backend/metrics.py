"""
Prometheus metrics for monitoring.
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from functools import wraps
import time
from typing import Callable

# Request metrics
request_count = Counter(
    'geo_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'geo_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# RAG pipeline metrics
rag_query_count = Counter(
    'geo_rag_queries_total',
    'Total RAG queries processed',
    ['status']
)

rag_query_duration = Histogram(
    'geo_rag_query_duration_seconds',
    'RAG query duration in seconds',
    ['phase']  # retrieval, generation, total
)

rag_facts_retrieved = Histogram(
    'geo_rag_facts_retrieved',
    'Number of facts retrieved per query',
    buckets=[0, 1, 2, 5, 10, 20, 50]
)

# Cache metrics
cache_hits = Counter(
    'geo_cache_hits_total',
    'Total cache hits',
    ['cache_type']  # semantic, http, etc.
)

cache_misses = Counter(
    'geo_cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# Database metrics
neo4j_query_duration = Histogram(
    'geo_neo4j_query_duration_seconds',
    'Neo4j query duration in seconds',
    ['operation']  # create_fact, find_facts, etc.
)

neo4j_errors = Counter(
    'geo_neo4j_errors_total',
    'Total Neo4j errors',
    ['error_type']
)

# Ingestion metrics
ingestion_count = Counter(
    'geo_ingestion_total',
    'Total papers/sources ingested',
    ['source_type']  # arxiv, rss, geo_submit
)

ingestion_errors = Counter(
    'geo_ingestion_errors_total',
    'Total ingestion errors',
    ['source_type', 'error_type']
)

# System metrics
active_requests = Gauge(
    'geo_active_requests',
    'Number of active requests'
)

pdf_extractions = Counter(
    'geo_pdf_extractions_total',
    'Total PDF extractions',
    ['status']  # success, failure, cached
)

deduplication_checks = Counter(
    'geo_deduplication_checks_total',
    'Total deduplication checks',
    ['result']  # duplicate, unique
)

def track_request(method: str, endpoint: str, status: int):
    """Track HTTP request metrics."""
    request_count.labels(method=method, endpoint=endpoint, status=status).inc()

def track_request_duration(method: str, endpoint: str, duration: float):
    """Track HTTP request duration."""
    request_duration.labels(method=method, endpoint=endpoint).observe(duration)

def track_rag_query(status: str):
    """Track RAG query."""
    rag_query_count.labels(status=status).inc()

def track_rag_duration(phase: str, duration: float):
    """Track RAG query duration by phase."""
    rag_query_duration.labels(phase=phase).observe(duration)

def track_facts_retrieved(count: int):
    """Track number of facts retrieved."""
    rag_facts_retrieved.observe(count)

def track_cache(cache_type: str, hit: bool):
    """Track cache hit/miss."""
    if hit:
        cache_hits.labels(cache_type=cache_type).inc()
    else:
        cache_misses.labels(cache_type=cache_type).inc()

def metrics_endpoint():
    """Generate Prometheus metrics endpoint response."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

def timed_operation(metric: Histogram, *labels):
    """Decorator to time operations and record to histogram."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                metric.labels(*labels).observe(duration)
        return wrapper
    return decorator

# Example usage:
# @timed_operation(neo4j_query_duration, "create_fact")
# def create_fact(...):
#     ...
