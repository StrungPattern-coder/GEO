# GEO Development Guide

Prereqs:
- Python 3.11+
- Neo4j Desktop running locally (bolt://localhost:7687)
- Optional: Ollama with a local model (e.g., llama3)

Setup:
1) Create a virtualenv and install requirements.txt.
2) Copy .env.example to .env and set credentials.
3) Start Neo4j and create a blank DB, note user/password.
4) Run the API: `uvicorn src.backend.api.main:app --reload`.
5) Open src/frontend/index.html in a browser.
6) Ingest data: POST to http://localhost:8000/ingest/run (or run tests/smoke.py).

Notes:
- Change LLM provider in .env: LLM_PROVIDER=ollama|openai|anthropic.
- For ollama, install and `ollama pull llama3`.
- For OpenAI/Anthropic, set API keys.
