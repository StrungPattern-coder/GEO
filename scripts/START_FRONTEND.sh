#!/bin/bash

# Complete Quick Start - Frontend Only
# No Docker required!

set -e

echo "════════════════════════════════════════════════════════════"
echo "🚀 Project GEO - Frontend Testing"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if node_modules exists
if [ ! -d "apps/web/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd apps/web
    npm install
    cd ../..
    echo "✓ Dependencies installed"
    echo ""
fi

echo "✓ Frontend ready"
echo ""

echo "════════════════════════════════════════════════════════════"
echo "🎯 Starting Frontend Development Server"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Frontend will start on: http://localhost:3000"
echo ""
echo "✨ Option D Features to Test:"
echo "  • Theme Toggle (dark/light mode)"
echo "  • Copy buttons"
echo "  • Export functionality"
echo "  • Latency timer"
echo "  • Toast notifications"
echo ""
echo "Press Ctrl+C to stop"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd apps/web
npm run dev
