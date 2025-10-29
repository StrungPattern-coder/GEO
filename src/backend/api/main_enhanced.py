"""
Enhanced FastAPI application with production-ready features:
- Structured JSON logging
- Prometheus metrics
- Health/readiness endpoints
- Graceful shutdown
- Request tracking
"""
import signal
import sys
import json
import logging
from contextlib import asynccontextmanager
from typing import Optional, Callable, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
import time

# Import our modules
from .schemas import AskRequest, AskResponse, Fact
from ..graph.client import GraphClient
from ..ingest.ingestor import Ingestor
from ..rag.llm import LLM
from ..rag.pipeline import RAGPipeline
from ..config import settings

# Import production features with proper defaults
_HAS_PROD_FEATURES = False

# Type hints for optional features
setup_logging: Optional[Callable] = None
set_trace_id: Optional[Callable] = None
track_request: Optional[Callable] = None
track_request_duration: Optional[Callable] = None
track_rag_query: Optional[Callable] = None
track_rag_duration: Optional[Callable] = None
track_facts_retrieved: Optional[Callable] = None
metrics_endpoint: Optional[Callable] = None
active_requests: Optional[Any] = None
health_router: Optional[Any] = None

# Default logger function
def get_logger(name: str) -> logging.Logger:
    """Get logger - will be replaced if production features available."""
    return logging.getLogger(name)

try:
    from ..logging_config import setup_logging as _setup_logging
    from ..logging_config import get_logger as _get_logger
    from ..logging_config import set_trace_id as _set_trace_id
    from ..metrics import (
        track_request as _track_request,
        track_request_duration as _track_request_duration,
        track_rag_query as _track_rag_query,
        track_rag_duration as _track_rag_duration,
        track_facts_retrieved as _track_facts_retrieved,
        metrics_endpoint as _metrics_endpoint,
        active_requests as _active_requests
    )
    from .health import router as _health_router
    
    # Assign to module-level variables
    setup_logging = _setup_logging
    get_logger = _get_logger  # type: ignore
    set_trace_id = _set_trace_id
    track_request = _track_request
    track_request_duration = _track_request_duration
    track_rag_query = _track_rag_query
    track_rag_duration = _track_rag_duration
    track_facts_retrieved = _track_facts_retrieved
    metrics_endpoint = _metrics_endpoint
    active_requests = _active_requests
    health_router = _health_router
    
    _HAS_PROD_FEATURES = True
except ImportError as e:
    _HAS_PROD_FEATURES = False
    # Keep default logger

# Setup logging
if _HAS_PROD_FEATURES and setup_logging:
    log_level = getattr(settings, 'log_level', "INFO")
    use_json = getattr(settings, 'use_json_logging', False)
    setup_logging(level=log_level, use_json=use_json)

logger = get_logger(__name__)

# Global state for graceful shutdown
_shutting_down = False

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting GEO API service", extra={"version": "2.0.0"})
    
    # Initialize global resources
    global graph, llm, rag
    graph = GraphClient()
    graph.ensure_indexes()
    llm = LLM()
    rag = RAGPipeline(graph, llm)
    
    logger.info("Service initialized successfully")
    
    yield
    
    # Shutdown
    global _shutting_down
    _shutting_down = True
    logger.info("Shutting down gracefully...")
    
    # Close database connections
    if hasattr(graph, '_driver') and graph._driver:
        try:
            graph._driver.close()
            logger.info("Neo4j connection closed")
        except Exception as e:
            logger.error(f"Error closing Neo4j: {e}")
    
    logger.info("Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="GEO API",
    description="Generative Engine Optimization - Trustworthy AI Answers",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include health router
if _HAS_PROD_FEATURES and health_router:
    app.include_router(health_router)

# Metrics endpoint
if _HAS_PROD_FEATURES and metrics_endpoint:
    @app.get("/metrics")
    async def prometheus_metrics():
        """Prometheus metrics endpoint."""
        if metrics_endpoint:
            return metrics_endpoint()
        return {"error": "Metrics not available"}

# Request tracking middleware
@app.middleware("http")
async def request_tracking_middleware(request: Request, call_next):
    # Check if shutting down
    if _shutting_down:
        return HTTPException(status_code=503, detail="Service shutting down")
    
    # Generate trace ID
    trace_id_value = ""
    if _HAS_PROD_FEATURES and set_trace_id:
        trace_id_value = set_trace_id()
        request.state.trace_id = trace_id_value
    
    # Track active requests
    if _HAS_PROD_FEATURES and active_requests:
        active_requests.inc()
    
    start_time = time.time()
    method = request.method
    path = request.url.path
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        status = response.status_code
        
        # Log request
        logger.info(
            f"{method} {path} {status}",
            extra={
                "method": method,
                "path": path,
                "status": status,
                "duration_ms": int(duration * 1000),
                "trace_id": trace_id_value
            }
        )
        
        # Track metrics
        if _HAS_PROD_FEATURES:
            if track_request:
                track_request(method, path, status)
            if track_request_duration:
                track_request_duration(method, path, duration)
            if active_requests:
                active_requests.dec()
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"{method} {path} ERROR: {str(e)}",
            extra={
                "method": method,
                "path": path,
                "error": str(e),
                "duration_ms": int(duration * 1000),
                "trace_id": trace_id_value
            },
            exc_info=True
        )
        
        if _HAS_PROD_FEATURES:
            if track_request:
                track_request(method, path, 500)
            if active_requests:
                active_requests.dec()
        
        raise

# Rate limiting middleware
_rl_cache = {}

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    # Optional API key
    if settings.api_key:
        key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
        if key != settings.api_key:
            raise HTTPException(status_code=401, detail="Unauthorized")
    
    ip = request.client.host if request.client else "anon"
    now = time.time()
    w = _rl_cache.get(ip, [])
    w = [t for t in w if now - t < 5]  # 5s window
    if len(w) > 10:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    w.append(now)
    _rl_cache[ip] = w
    return await call_next(request)

# Helper function
def to_fact_model(d: dict) -> Fact:
    return Fact(
        id=str(d.get("id") or ""),
        subject=str(d.get("subject") or ""),
        predicate=str(d.get("predicate") or ""),
        object=str(d.get("object") or ""),
        source_url=str(d.get("source_url") or ""),
        truth_weight=d.get("truth_weight", 0.5),
        score=d.get("score"),
        ts=str(d.get("ts") or "") or None,
        idx=d.get("idx"),
        corroboration_count=d.get("corroboration_count"),
        recency_weight=d.get("recency_weight"),
        trust_score=d.get("trust_score"),
        trust_explain=d.get("trust_explain"),
    )

# API Endpoints
@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """Answer a query with citations."""
    start = time.time()
    
    try:
        answer, raw_facts = rag.answer(req.query, k=req.max_facts)
        
        if _HAS_PROD_FEATURES:
            if track_rag_query:
                track_rag_query("success")
            if track_rag_duration:
                track_rag_duration("total", time.time() - start)
            if track_facts_retrieved:
                track_facts_retrieved(len(raw_facts))
        
        return AskResponse(answer=answer, facts=[to_fact_model(f) for f in raw_facts])
    
    except Exception as e:
        if _HAS_PROD_FEATURES and track_rag_query:
            track_rag_query("error")
        logger.error(f"Error in /ask: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask/stream")
def ask_stream(req: AskRequest):
    """Stream answer generation."""
    def gen():
        start = time.time()
        try:
            # Stream facts and answer
            for chunk in rag.answer_stream(req.query, k=req.max_facts):
                if chunk["type"] == "facts":
                    # Send facts header first
                    facts = chunk["facts"]
                    if _HAS_PROD_FEATURES:
                        if track_rag_query:
                            track_rag_query("success")
                        if track_facts_retrieved:
                            track_facts_retrieved(len(facts))
                    
                    yield json.dumps({
                        "type": "header",
                        "facts": [to_fact_model(f).model_dump() for f in facts if isinstance(f, dict)]
                    }) + "\n"
                elif chunk["type"] == "text":
                    # Stream answer text
                    yield chunk["content"]
            
            if _HAS_PROD_FEATURES and track_rag_duration:
                track_rag_duration("total", time.time() - start)
        
        except Exception as e:
            if _HAS_PROD_FEATURES and track_rag_query:
                track_rag_query("error")
            logger.error(f"Error in /ask/stream: {str(e)}", exc_info=True)
            yield json.dumps({"error": str(e)})
    
    return StreamingResponse(gen(), media_type="text/plain")

@app.post("/ingest/run")
def ingest():
    """Trigger ingestion."""
    try:
        ing = Ingestor(graph)
        ing.run_all()
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Ingestion error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/geo/submit")
def geo_submit(payload: dict):
    """GEO Protocol: Submit facts and entities."""
    try:
        ents = payload.get("entities") or []
        facts = payload.get("facts") or []
        
        # Register aliases
        for e in ents:
            eid = str(e.get("id") or "").strip()
            aliases = e.get("aliases") or []
            if eid and isinstance(aliases, list):
                graph.add_aliases(eid, [str(a) for a in aliases if a])
        
        # Upsert facts
        count = 0
        for f in facts:
            if not (f.get("subject") and f.get("predicate") and f.get("object") and f.get("source_url")):
                continue
            graph.upsert_fact({
                "id": f.get("id") or f"{f.get('subject')}#{f.get('predicate')}",
                "subject": f.get("subject"),
                "predicate": f.get("predicate"),
                "object": f.get("object"),
                "source_url": f.get("source_url"),
                "source_name": f.get("source_name"),
                "ts": f.get("ts"),
                "truth_weight": float(f.get("truth_weight", 0.5)),
            })
            count += 1
        
        logger.info(f"GEO submit: {len(ents)} entities, {count} facts")
        return {"status": "ok", "facts": count}
    
    except Exception as e:
        logger.error(f"GEO submit error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config")
def get_config():
    """Get service configuration."""
    return {
        "neo4j_uri": settings.neo4j_uri,
        "llm_provider": settings.llm_provider,
        "arxiv_query": settings.arxiv_query,
        "rss_feeds": settings.rss_feeds,
    }

@app.post("/query/expand")
def expand_query_endpoint(req: dict):
    """Expand query into variants."""
    query = req.get("query", "")
    use_llm = req.get("use_llm", False)
    
    from ..rag.query_expansion import QueryExpander
    expander = QueryExpander(llm=llm if use_llm else None)
    stats = expander.get_expansion_stats(query, use_llm=use_llm)
    
    return stats

@app.post("/domain/score")
def score_domain_endpoint(req: dict):
    """Score domain reputation."""
    url = req.get("url", "")
    
    from ..rag.domain_reputation import explain_domain_score
    explanation = explain_domain_score(url)
    
    return explanation

# Graceful shutdown handlers
def shutdown_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    global _shutting_down
    _shutting_down = True
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)
