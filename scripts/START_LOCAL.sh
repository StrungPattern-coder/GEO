#!/bin/bash

# Local Development Startup (No Docker Required)
# This runs everything locally for testing Options D & E

set -e

echo "════════════════════════════════════════════════════════════"
echo "🚀 Project GEO - Local Development Mode"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check Python venv
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install fastapi uvicorn neo4j-driver python-dotenv prometheus-client
fi

echo "✓ Python environment ready"
echo ""

# Check if frontend exists
if [ ! -d "apps/web" ]; then
    echo "⚠️  Frontend not found at apps/web"
    echo "   Creating minimal structure..."
    mkdir -p apps/web/src/pages
fi

echo "✓ Frontend structure ready"
echo ""

# Check for Neo4j (optional)
echo "💾 Neo4j Status:"
if curl -s http://localhost:7474 > /dev/null 2>&1; then
    echo "   ✓ Neo4j is running at localhost:7474"
else
    echo "   ⚠️  Neo4j not detected (optional for testing)"
    echo "   To start Neo4j with Docker CLI:"
    echo "   /usr/local/bin/docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \\"
    echo "     -e NEO4J_AUTH=neo4j/password neo4j:5.13"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "🎯 Starting Backend..."
echo "════════════════════════════════════════════════════════════"
echo ""

# Start backend
echo "Backend will start on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""
echo "To test health:"
echo "  curl http://localhost:8000/health"
echo ""
echo "To test metrics:"
echo "  curl http://localhost:8000/metrics"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run backend
.venv/bin/python -m uvicorn src.backend.api.main_enhanced:app --reload --host 0.0.0.0 --port 8000
