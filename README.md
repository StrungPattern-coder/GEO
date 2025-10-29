# GEO Alpha v0.1

A prototype Generative Engine demonstrating Generative Engine Optimization (GEO):
- Consciousness Stream (ingestion)
- Neural Weaver (knowledge graph)
- Synthesis Core (RAG answer generation with source citations)

## Modules
- backend/ingest: Fetch arXiv + RSS, normalize, truth-weight stub
- backend/graph: Neo4j driver utilities, schema bootstrap
- backend/rag: Retrieval over graph + LLM wrapper (Ollama or API)
- backend/api: FastAPI service exposing /ask
- frontend: Minimal web UI

## Quickstart
1) Create and activate a Python 3.11+ virtualenv.
2) Install Python deps from requirements.txt.
3) Start Neo4j Desktop and set NEO4J_URI/USER/PASSWORD.
4) (Optional) Install Ollama and pull a model (e.g., llama3 or mistral).
5) Run API, then open the frontend.

See docs/DEVELOPMENT.md for details.
