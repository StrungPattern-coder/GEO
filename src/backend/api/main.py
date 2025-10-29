from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .schemas import AskRequest, AskResponse, Fact
from ..graph.client import GraphClient
from ..ingest.ingestor import Ingestor
from ..rag.llm import LLM
from ..rag.pipeline import RAGPipeline
from fastapi.responses import StreamingResponse

app = FastAPI(title="GEO Alpha API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the UI from the same server for simplicity
app.mount("/ui", StaticFiles(directory="src/frontend", html=True), name="ui")

graph = GraphClient()
graph.ensure_indexes()
llm = LLM()
rag = RAGPipeline(graph, llm)
from ..config import settings

# Simple rate limit per-IP (very naive, in-memory)
_rl_cache = {}

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    # Optional API key
    if settings.api_key:
        key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
        if key != settings.api_key:
            raise HTTPException(status_code=401, detail="Unauthorized")
    ip = request.client.host if request.client else "anon"
    import time
    now = time.time()
    w = _rl_cache.get(ip, [])
    w = [t for t in w if now - t < 5]  # 5s window
    if len(w) > 10:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    w.append(now)
    _rl_cache[ip] = w
    return await call_next(request)

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

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    answer, raw_facts = rag.answer(req.query, k=req.max_facts)
    return AskResponse(answer=answer, facts=[to_fact_model(f) for f in raw_facts])

@app.post("/ask/stream")
def ask_stream(req: AskRequest):
    def gen():
        answer, raw_facts = rag.answer(req.query, k=req.max_facts)
        import json
        yield json.dumps({
            "type": "header",
            "facts": [to_fact_model(f).model_dump() for f in raw_facts]
        }) + "\n"
        # mock streaming: send chunks of the answer
        chunk = max(1, len(answer)//5)
        for i in range(0, len(answer), chunk):
            yield answer[i:i+chunk]
    return StreamingResponse(gen(), media_type="text/plain")

@app.post("/ingest/run")
def ingest():
    ing = Ingestor(graph)
    ing.run_all()
    return {"status": "ok"}

@app.post("/geo/submit")
def geo_submit(payload: dict):
    # Expected schema: { entities: [{id, type?, aliases?[]}], facts: [{subject, predicate, object, source_url, truth_weight?, ts?}] }
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
    return {"status": "ok", "facts": count}

@app.get("/config")
def get_config():
    from ..config import settings
    return {
        "neo4j_uri": settings.neo4j_uri,
        "llm_provider": settings.llm_provider,
        "arxiv_query": settings.arxiv_query,
        "rss_feeds": settings.rss_feeds,
    }

@app.post("/query/expand")
def expand_query_endpoint(req: dict):
    """
    Expand a query into multiple variants for better retrieval.
    
    Body: {"query": "your query", "use_llm": true}
    """
    query = req.get("query", "")
    use_llm = req.get("use_llm", False)
    
    from ..rag.query_expansion import QueryExpander
    expander = QueryExpander(llm=llm if use_llm else None)
    stats = expander.get_expansion_stats(query, use_llm=use_llm)
    
    return stats

@app.post("/domain/score")
def score_domain_endpoint(req: dict):
    """
    Score a domain's reputation.
    
    Body: {"url": "https://example.com"}
    """
    url = req.get("url", "")
    
    from ..rag.domain_reputation import explain_domain_score
    explanation = explain_domain_score(url)
    
    return explanation

@app.post("/ingest/schedule")
def ingest_schedule(every_minutes: int = 60):
    # best-effort naive scheduler using background thread timer
    import threading, time
    def job():
        while True:
            ing = Ingestor(graph)
            try:
                ing.run_all()
            except Exception:
                pass
            time.sleep(max(60, every_minutes * 60))
    t = threading.Thread(target=job, daemon=True)
    t.start()
    return {"status": "scheduled", "interval_min": every_minutes}

