# Cursor Rules for Trading Agent Project

This directory contains comprehensive cursor rules organized by domain and technology stack to guide AI-assisted development in the Trading Agent project.

## Structure

The cursor rules are organized into the following files:

- **`python.md`** - Python/Backend specific rules
  - Async/await patterns
  - FastAPI endpoints
  - SQLAlchemy patterns
  - ML model integration
  - Type hints and type safety
  - Structured logging

- **`typescript.md`** - TypeScript/Frontend rules
  - Next.js and React patterns
  - TypeScript best practices
  - Component structure
  - API integration
  - WebSocket patterns
  - State management

- **`project.md`** - Project-specific conventions
  - File structure and organization
  - Structured logging patterns
  - Error handling conventions
  - Configuration management
  - Shared state patterns
  - Health monitoring

- **`general.md`** - General code quality standards
  - Naming conventions
  - Code organization
  - Documentation requirements
  - Testing patterns
  - Performance considerations
  - Security best practices

## Usage

These rules are automatically picked up by Cursor AI when working on the Trading Agent project. They provide context and guidelines for:

- Code generation and suggestions
- Code review and refactoring
- Best practices enforcement
- Consistent code style across the project

## Project Overview

The Trading Agent project is a sophisticated AI trading system with:

- **Backend**: FastAPI-based Python backend with async support
- **Frontend**: Next.js TypeScript frontend with React
- **ML Models**: Multiple machine learning models (XGBoost, LightGBM, Random Forest, LSTM, Transformer)
- **Database**: SQLAlchemy with SQLite/PostgreSQL
- **Real-time**: WebSocket support for live updates
- **Monitoring**: Prometheus metrics and Grafana dashboards

## Key Technologies

### Backend
- Python 3.9+
- FastAPI
- SQLAlchemy
- AsyncIO
- Pydantic
- Structlog

### Frontend
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Radix UI
- SWR

### Machine Learning
- scikit-learn
- XGBoost
- LightGBM
- PyTorch (for deep learning models)

## Quick Reference

### Common Patterns

**Async Function with Retry:**
```python
async def fetch_with_retry(fetch_func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return await fetch_func()
        except Exception as e:
            if attempt == max_retries - 1:
                return None
            await asyncio.sleep(2 ** attempt)
```

**Structured Logging:**
```python
self.logger.info(
    "operation_name",
    "Human-readable message",
    {"context": "data", "key": "value"}
)
```

**FastAPI Endpoint:**
```python
@app.get("/api/v1/endpoint", response_model=ResponseModel, tags=["Tag"])
async def endpoint_function(request: RequestModel):
    """Endpoint description."""
    # Implementation
```

**React Component with TypeScript:**
```typescript
interface ComponentProps {
  prop1: string;
  prop2?: number;
}

export function Component({ prop1, prop2 = 0 }: ComponentProps) {
  // Implementation
}
```

## Contributing

When adding new patterns or conventions:

1. Update the appropriate rule file
2. Include examples
3. Explain the reasoning
4. Keep rules focused and specific

## Questions?

Refer to the specific rule files for detailed guidelines. For project-specific questions, consult the main project README or architecture documentation.

