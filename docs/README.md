# GEO (Generative Engine)

End-to-end prototype: FastAPI backend + Next.js UI for trustworthy answers with citations.

Quick start
- Backend: set env in `.env` (optional), then start Uvicorn serving FastAPI on :8000
- UI: `cd apps/web && npm install && npm run dev` (serves on :3000)

API
- POST /ingest/run: one-off ingestion (arXiv/rss based on env)
- POST /ask: { query, max_facts } -> { answer, facts[] }
- POST /ask/stream: streams answer; first line is JSON with facts
- GET /config: view current backend config
- POST /ingest/schedule?every_minutes=60: naive background scheduler

Env (.env)
- NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD (optional; falls back to in-memory)
- LLM_PROVIDER: mock | ollama | openai | anthropic
- OLLAMA_MODEL, OPENAI_API_KEY, ANTHROPIC_API_KEY
- ARXIV_QUERY, RSS_FEEDS (comma-separated)

Notes
- Retrieval uses hybrid signals (term hits, BM25, embeddings if available) plus trust (truth_weight, corroboration) and recency (exp. decay).
- UI shows inline [n] markers with hover and click-to-scroll highlighting; fact cards show trust/corroboration/recency.
- Rate limiting is a naive in-memory middleware. For production, use a real gateway/redis limiter.
