#!/bin/bash

# Fix Docker PATH on macOS
# Run this once: source FIX_DOCKER_PATH.sh

echo "🔧 Adding Docker to PATH..."

# Check if Docker is installed
if [ -f "/Applications/Docker.app/Contents/Resources/bin/docker" ]; then
    export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
    echo "✓ Docker CLI added to PATH for this session"
    echo ""
    docker --version
    echo ""
    echo "To make this permanent, add to your ~/.zshrc:"
    echo 'export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"'
    echo ""
    echo "Now you can run:"
    echo "  docker ps"
    echo "  docker-compose -f docker-compose.prod.yml up -d"
else
    echo "❌ Docker not found at /Applications/Docker.app"
    echo ""
    echo "Download Docker Desktop from:"
    echo "https://www.docker.com/products/docker-desktop"
fi
