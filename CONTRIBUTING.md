# Contributing to GEO

Thank you for your interest in contributing to GEO (Generative Engine Optimization)! This document provides guidelines for contributing to the project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Style Guidelines](#style-guidelines)

## Code of Conduct

Be respectful, professional, and inclusive. We welcome contributions from everyone.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/GEO.git
   cd GEO
   ```
3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites
- Python 3.13+
- Node.js 18+
- Ollama (for local LLM)
- Docker & Docker Compose (optional)

### Backend Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start backend
./scripts/START_LOCAL.sh
```

### Frontend Setup
```bash
cd apps/web
npm install
npm run dev
```

### Start Ollama
```bash
ollama serve
ollama pull qwen2.5:3b  # Or your preferred model
```

## Making Changes

### Project Structure
```
GEO/
├── apps/web/              # Next.js frontend
├── src/backend/           # Python backend
│   ├── api/              # FastAPI endpoints
│   ├── rag/              # RAG pipeline
│   ├── search/           # Web search
│   └── graph/            # Neo4j integration
├── tests/                # Test files
├── docs/                 # Documentation
└── scripts/              # Utility scripts
```

### Code Organization
- **Backend code** goes in `src/backend/`
- **Frontend code** goes in `apps/web/`
- **Tests** go in `tests/`
- **Documentation** goes in `docs/`
- **Scripts** go in `scripts/`

## Testing

### Run Backend Tests
```bash
pytest tests/
```

### Run Frontend Tests
```bash
cd apps/web
npm test
```

### Manual Testing
1. Start backend: `./scripts/START_LOCAL.sh`
2. Start frontend: `cd apps/web && npm run dev`
3. Open http://localhost:3000
4. Test chat functionality

## Submitting Changes

1. **Commit your changes** with clear messages:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request** on GitHub:
   - Provide a clear title and description
   - Reference any related issues
   - Include screenshots for UI changes

### Commit Message Format
Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

## Style Guidelines

### Python (Backend)
- Follow [PEP 8](https://pep8.org/)
- Use type hints
- Write docstrings for functions/classes
- Maximum line length: 100 characters
- Use `black` for formatting: `black src/`

### TypeScript/React (Frontend)
- Follow [Airbnb Style Guide](https://github.com/airbnb/javascript)
- Use functional components with hooks
- Use TypeScript for type safety
- Use Tailwind CSS for styling
- Format with Prettier: `npm run format`

### Documentation
- Use Markdown for all docs
- Keep docs up to date with code changes
- Add examples for new features
- Update CHANGELOG.md for notable changes

## Questions?

- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions
- **Security**: Email security issues privately

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
