# Changelog

All notable changes to the GEO project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Real-time web search with DuckDuckGo integration
- Ollama LLM support for local AI synthesis
- Intelligent conversational query detection
- Chat interface with conversation history
- Domain reputation scoring (GEO Protocol)
- Inline citation system with clickable references
- Streaming response generation
- Query expansion disabled by default for speed
- Dark/light theme support
- Toast notifications for UX feedback

### Changed
- Migrated from static database to real-time web search
- Optimized query processing (3-10 seconds response time)
- Organized documentation into `docs/` folder
- Organized scripts into `scripts/` folder
- Improved project structure for enterprise standards

### Fixed
- Frontend streaming display issues
- ThemeProvider context blocking
- Mock LLM generating templates instead of answers
- Query expansion performance (reduced from 6 to 1-3 queries)

## [0.1.0] - 2025-10-29

### Added
- Initial project setup
- Neo4j graph database integration
- FastAPI backend with health checks
- Next.js frontend with TypeScript
- Docker Compose for local development
- Basic RAG pipeline
- Prometheus metrics
- Structured logging

### Security
- API key authentication support
- Rate limiting middleware
- CORS configuration for local development
