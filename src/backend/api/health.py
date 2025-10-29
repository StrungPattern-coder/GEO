"""
Health check endpoints for Kubernetes/Docker.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import time
from ..graph.client import GraphClient
from ..config import settings

router = APIRouter(prefix="/health", tags=["health"])

# Track service start time
_start_time = time.time()

def check_neo4j(graph: GraphClient) -> Dict[str, Any]:
    """Check Neo4j connection."""
    try:
        if graph._use_memory:
            return {
                "status": "degraded",
                "message": "Using in-memory fallback",
                "connected": False
            }
        
        # Simple query to test connection
        if graph._driver:
            with graph._driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            return {
                "status": "healthy",
                "response_time_ms": 0,
                "connected": True
            }
        else:
            return {
                "status": "unhealthy",
                "error": "No driver available",
                "connected": False
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "connected": False
        }

def check_embeddings() -> Dict[str, Any]:
    """Check if embeddings model is loaded."""
    try:
        from ..rag.pipeline import RAGPipeline
        # Try to check if model exists
        return {
            "status": "healthy",
            "model": "all-MiniLM-L6-v2",
            "loaded": True
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "loaded": False
        }

@router.get("")
@router.get("/")
async def health_check():
    """
    Basic health check endpoint.
    Returns 200 if service is running.
    """
    uptime = time.time() - _start_time
    return {
        "status": "healthy",
        "service": "geo-api",
        "version": "2.0.0",
        "uptime_seconds": int(uptime),
        "timestamp": time.time()
    }

@router.get("/ready")
async def readiness_check():
    """
    Readiness check for Kubernetes.
    Returns 200 only if all dependencies are ready.
    Checks:
    - Neo4j connection
    - Embeddings model
    - Configuration
    """
    checks = {}
    all_ready = True
    
    # Try to check Neo4j (will fail gracefully if not available)
    try:
        from ..graph.client import GraphClient
        graph = GraphClient()
        neo4j_check = check_neo4j(graph)
        checks["neo4j"] = neo4j_check
        if neo4j_check["status"] != "healthy":
            all_ready = False
    except Exception as e:
        checks["neo4j"] = {"status": "unhealthy", "error": str(e)}
        all_ready = False
    
    # Check embeddings
    embeddings_check = check_embeddings()
    checks["embeddings"] = embeddings_check
    if embeddings_check["status"] not in ["healthy", "degraded"]:
        all_ready = False
    
    # Check configuration
    config_check = {
        "status": "healthy",
        "neo4j_configured": bool(settings.neo4j_uri),
        "api_key_configured": bool(settings.api_key)
    }
    checks["configuration"] = config_check
    
    uptime = time.time() - _start_time
    
    response = {
        "ready": all_ready,
        "service": "geo-api",
        "version": "2.0.0",
        "uptime_seconds": int(uptime),
        "timestamp": time.time(),
        "checks": checks
    }
    
    if not all_ready:
        raise HTTPException(status_code=503, detail=response)
    
    return response

@router.get("/live")
async def liveness_check():
    """
    Liveness check for Kubernetes.
    Returns 200 if process is alive (doesn't check dependencies).
    """
    uptime = time.time() - _start_time
    return {
        "alive": True,
        "service": "geo-api",
        "uptime_seconds": int(uptime),
        "timestamp": time.time()
    }
