#!/bin/bash

# Restart Backend with Real-Time Web Search

echo "🔄 Restarting GEO Backend with Real-Time Web Search..."
echo ""

# Kill any existing backend
pkill -f "uvicorn src.backend.api.main_enhanced" || true
sleep 2

# Start fresh
cd /Users/sriram_kommalapudi/Projects/GEO
source .venv/bin/activate

echo "✅ Starting backend on http://0.0.0.0:8000"
echo ""
echo "Features enabled:"
echo "  • Real-time web search (DuckDuckGo)"
echo "  • Query expansion"
echo "  • Domain reputation scoring"
echo "  • Hybrid ranking (BM25 + embeddings)"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python -m uvicorn src.backend.api.main_enhanced:app --reload --host 0.0.0.0 --port 8000
