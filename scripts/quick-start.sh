#!/bin/bash

# Quick Start Script for Project GEO
# Options D & E Testing

set -e

echo "════════════════════════════════════════════════════════════"
echo "🚀 Project GEO - Quick Start"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if Docker is running (multiple detection methods)
DOCKER_RUNNING=false

# Method 1: Check docker ps
if docker ps > /dev/null 2>&1; then
    DOCKER_RUNNING=true
# Method 2: Check docker info
elif docker info > /dev/null 2>&1; then
    DOCKER_RUNNING=true
# Method 3: Check docker version
elif docker version > /dev/null 2>&1; then
    DOCKER_RUNNING=true
fi

if [ "$DOCKER_RUNNING" = false ]; then
    echo "❌ Docker is not accessible. Please ensure Docker is running."
    echo "   Tried: docker ps, docker info, docker version"
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Ask user which mode
echo "Choose startup mode:"
echo "  1) Docker Compose (Full stack - Recommended)"
echo "  2) Local Development (Backend + Frontend separately)"
echo ""
read -p "Enter choice (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "🐳 Starting Docker Compose..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Start services
    docker-compose -f docker-compose.prod.yml up -d
    
    echo ""
    echo "⏳ Waiting for services to start (30 seconds)..."
    sleep 30
    
    # Check health
    echo ""
    echo "🔍 Checking service health..."
    
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "  ✓ Backend is healthy"
    else
        echo "  ⚠️  Backend not responding yet (may need more time)"
    fi
    
    if curl -s http://localhost:3000 > /dev/null; then
        echo "  ✓ Frontend is healthy"
    else
        echo "  ⚠️  Frontend not responding yet (may need more time)"
    fi
    
    if curl -s http://localhost:7474 > /dev/null; then
        echo "  ✓ Neo4j is healthy"
    else
        echo "  ⚠️  Neo4j not responding yet (may need more time)"
    fi
    
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "🎉 Services Started!"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "Access Points:"
    echo "  🌐 Frontend:   http://localhost:3000"
    echo "  🔧 Backend:    http://localhost:8000"
    echo "  💾 Neo4j:      http://localhost:7474"
    echo "  📊 Prometheus: http://localhost:9090"
    echo "  📈 Grafana:    http://localhost:3001 (admin/admin)"
    echo ""
    echo "Health Checks:"
    echo "  curl http://localhost:8000/health"
    echo "  curl http://localhost:8000/health/ready"
    echo ""
    echo "View Logs:"
    echo "  docker-compose logs -f backend"
    echo "  docker-compose logs -f frontend"
    echo ""
    echo "Stop Services:"
    echo "  docker-compose -f docker-compose.prod.yml down"
    echo ""
    echo "Opening frontend in browser..."
    sleep 2
    open http://localhost:3000 || xdg-open http://localhost:3000 || echo "Please open http://localhost:3000 manually"
    
elif [ "$choice" = "2" ]; then
    echo ""
    echo "🔧 Local Development Mode"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "You'll need 3 terminals:"
    echo ""
    echo "Terminal 1 - Neo4j (Docker):"
    echo "  docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \\"
    echo "    -e NEO4J_AUTH=neo4j/password \\"
    echo "    -e NEO4J_PLUGINS='[\"apoc\"]' \\"
    echo "    neo4j:5.13"
    echo ""
    echo "Terminal 2 - Backend:"
    echo "  cd $(pwd)"
    echo "  .venv/bin/python -m uvicorn src.backend.api.main_enhanced:app \\"
    echo "    --reload --host 0.0.0.0 --port 8000"
    echo ""
    echo "Terminal 3 - Frontend:"
    echo "  cd $(pwd)/apps/web"
    echo "  npm run dev"
    echo ""
    echo "Then access:"
    echo "  🌐 Frontend:   http://localhost:3000"
    echo "  🔧 Backend:    http://localhost:8000"
    echo ""
else
    echo "Invalid choice. Exiting."
    exit 1
fi

echo "════════════════════════════════════════════════════════════"
