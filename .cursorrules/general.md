# General Code Quality Standards

## Overview
General code quality standards, naming conventions, documentation requirements, and best practices applicable across all languages and components in the Trading Agent project.

## Naming Conventions

### Python
- **Functions and variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private attributes/methods**: `_leading_underscore` (single underscore)
- **Protected attributes/methods**: `_leading_underscore` (convention, not enforced)
- **Module names**: `snake_case`

```python
# Good naming
MAX_RETRIES = 5
update_interval = 300

class TradingAgent:
    def __init__(self):
        self.logger = get_component_logger("trading_agent")
        self._internal_state = {}  # Private
    
    async def fetch_market_data(self):
        """Public method."""
        pass
    
    def _validate_data(self):
        """Private method."""
        pass
```

### TypeScript/JavaScript
- **Functions and variables**: `camelCase`
- **Classes and Components**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE` or `UPPER_CAMEL_CASE`
- **Interfaces and Types**: `PascalCase`
- **Props**: `camelCase`

```typescript
// Good naming
const MAX_RETRIES = 5;
const updateInterval = 300;

interface PortfolioStatus {
  balance: number;
  equity: number;
}

export function PortfolioStatus({ 
  initialBalance 
}: PortfolioStatusProps) {
  const [balance, setBalance] = useState(initialBalance);
}
```

### Files and Directories
- **Python files**: `snake_case.py`
- **TypeScript components**: `PascalCase.tsx`
- **TypeScript utilities**: `camelCase.ts`
- **Directories**: `snake_case` or `kebab-case`
- **Config files**: `kebab-case.yaml` or `snake_case.yaml`

## Code Organization

### File Structure
- Keep files focused and single-purpose
- Maximum 500-800 lines per file (aim for 300-500)
- Extract large classes/modules into separate files
- Group related functionality together

### Import Organization
1. Standard library imports
2. Third-party imports
3. Local imports (from src.*, @/...)
4. Type checking imports (in TYPE_CHECKING block)

```python
# Standard library
import asyncio
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, TYPE_CHECKING

# Third-party
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import structlog

# Local imports
from src.core.config import settings
from src.core.logger import logger
from src.trading.paper_engine import PaperTradingEngine

# Type checking (avoids circular imports)
if TYPE_CHECKING:
    from src.ml.predictor import TradingPredictor
```

### Function/Method Length
- Keep functions focused and small
- Aim for 20-50 lines per function
- Maximum 100 lines (consider breaking into smaller functions)
- Extract complex logic into separate functions

### Class Organization
1. Class constants
2. `__init__` / constructor
3. Public methods
4. Protected methods (prefixed with `_`)
5. Private methods (prefixed with `_`)

## Documentation

### Docstrings
- Include docstrings for all public functions and classes
- Use descriptive docstrings explaining purpose, parameters, and return values
- Include examples for complex functions
- Document exceptions that may be raised

```python
async def fetch_data_with_retry(
    fetch_func: Callable,
    max_retries: int = 5,
    operation_name: str = "fetch"
) -> Optional[Dict]:
    """Fetch data with exponential backoff retry logic.
    
    Args:
        fetch_func: Function to call (async or sync)
        max_retries: Maximum number of retry attempts
        operation_name: Name of operation for logging
    
    Returns:
        Result from fetch_func, or None if all retries fail
    
    Raises:
        None (always returns None on failure)
    
    Example:
        >>> async def fetch_ticker():
        ...     return {"price": 50000}
        >>> result = await fetch_data_with_retry(fetch_ticker)
        >>> print(result)
        {"price": 50000}
    """
    # Implementation
```

### Comments
- Use comments to explain "why", not "what"
- Avoid obvious comments that just repeat code
- Explain complex logic or algorithms
- Document business rules and domain knowledge
- Use TODO comments sparingly and include context

```python
# Good: Explains why
# Use exponential backoff to avoid overwhelming the API during rate limits
wait_time = min(2 ** attempt, 60)

# Bad: Obvious comment
# Increment attempt counter
attempt += 1
```

### README and Documentation
- Maintain up-to-date README files
- Document architecture decisions
- Include setup and installation instructions
- Document configuration options
- Provide usage examples

## Code Quality

### Readability
- Write self-documenting code with clear variable names
- Avoid deep nesting (max 3-4 levels)
- Use early returns to reduce nesting
- Extract magic numbers into named constants
- Use meaningful variable names

```python
# Good: Clear and readable
max_position_value = portfolio.balance * MAX_POSITION_PCT
if expected_value > max_position_value:
    logger.error(f"Position size too large: ${expected_value:.2f}")
    return None

# Bad: Hard to understand
if v > b * 0.1:
    logger.error(f"Too large: {v}")
    return None
```

### Error Handling
- Always handle errors explicitly
- Don't ignore errors silently
- Provide meaningful error messages
- Log errors with full context
- Use appropriate exception types

```python
# Good: Explicit error handling
try:
    result = await fetch_data()
    if not result:
        logger.warning("No data returned")
        return None
except aiohttp.ClientError as e:
    logger.error(f"Network error: {e}", exc_info=True)
    return None
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise

# Bad: Silent failure
try:
    result = await fetch_data()
except:
    pass
```

### Type Safety
- Use type hints in Python
- Use TypeScript strict mode
- Avoid `any` types
- Validate types at runtime when necessary (Pydantic, Zod)

### Testing
- Write tests for critical functionality
- Test error cases and edge cases
- Mock external dependencies
- Maintain good test coverage (>80% for critical paths)
- Use descriptive test names

```python
def test_fetch_data_with_retry_success():
    """Test successful data fetch after retry."""
    # Test implementation

def test_fetch_data_with_retry_max_retries_exceeded():
    """Test failure after max retries."""
    # Test implementation
```

## Performance Considerations

### Async/Await
- Use async I/O for concurrent operations
- Avoid blocking operations in async code
- Use asyncio.gather() for concurrent operations
- Use asyncio.create_task() for fire-and-forget operations

### Caching
- Cache expensive operations (model predictions, API responses)
- Use appropriate cache TTLs
- Invalidate cache when data changes
- Monitor cache hit rates

### Database
- Use connection pooling
- Batch database operations when possible
- Use indexes for frequently queried fields
- Avoid N+1 query problems

### Frontend
- Lazy load heavy components
- Optimize bundle size
- Use React.memo for expensive components
- Debounce/throttle frequent operations

## Security

### Secrets Management
- Never commit secrets to version control
- Use environment variables for sensitive data
- Provide `.env.example` with required variables
- Validate required environment variables on startup

### Input Validation
- Validate all user inputs
- Sanitize data before database operations
- Use Pydantic models for API validation
- Validate file uploads

### Error Messages
- Don't expose sensitive information in error messages
- Log detailed errors server-side
- Return user-friendly error messages to clients

## Git and Version Control

### Commit Messages
- Use clear, descriptive commit messages
- Follow conventional commit format when possible
- Reference issue numbers when applicable
- Keep commits focused and atomic

```bash
# Good commit messages
feat: Add multi-timeframe model support
fix: Handle database connection errors gracefully
refactor: Extract retry logic into reusable function
docs: Update API documentation

# Bad commit messages
fix stuff
update
changes
```

### Branch Naming
- Use descriptive branch names
- Prefix with feature/, fix/, refactor/, etc.
- Include issue/feature number if applicable

```bash
feature/add-multi-model-support
fix/database-connection-error
refactor/extract-retry-logic
```

## Dependencies

### Dependency Management
- Pin dependency versions in requirements.txt / package.json
- Update dependencies regularly
- Review dependency changes
- Use dependency vulnerability scanners
- Document why dependencies are needed

### Version Pinning
- Pin exact versions for production
- Use version ranges for development dependencies if appropriate
- Document dependency version rationale for major updates

## Code Review

### Review Checklist
- Code follows project conventions
- Error handling is appropriate
- Tests are included for new functionality
- Documentation is updated
- No security vulnerabilities
- Performance considerations addressed

### Review Feedback
- Be constructive and specific
- Explain the reasoning behind suggestions
- Focus on code quality, not personal preferences
- Approve when standards are met

## Continuous Improvement

### Refactoring
- Refactor code regularly to improve maintainability
- Extract reusable patterns
- Remove dead code
- Simplify complex logic
- Improve test coverage

### Learning
- Stay updated with best practices
- Share knowledge with team
- Document lessons learned
- Improve based on feedback

