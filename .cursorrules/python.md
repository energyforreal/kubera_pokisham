# Python/Backend Cursor Rules

## Overview
Guidelines for Python backend development in the Trading Agent project, covering FastAPI, async programming, SQLAlchemy, ML models, and related patterns.

## Async/Await Patterns

### General Async Guidelines
- Always use `async/await` for I/O-bound operations (database, API calls, file operations)
- Use `asyncio.create_task()` for concurrent operations that don't require immediate results
- Use `asyncio.gather()` when you need to wait for multiple async operations
- Prefer `async with` for context managers (database sessions, HTTP sessions)
- Never mix sync and async code unnecessarily

### Example Patterns
```python
# Good: Async function with proper error handling
async def fetch_data_with_retry(fetch_func, max_retries=5):
    for attempt in range(max_retries):
        try:
            if asyncio.iscoroutinefunction(fetch_func):
                return await fetch_func()
            else:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, fetch_func)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed after {max_retries} attempts: {e}")
                return None
            wait_time = min(2 ** attempt, 60)
            await asyncio.sleep(wait_time)
```

### Background Tasks
- Use `asyncio.create_task()` for fire-and-forget operations
- Ensure proper cleanup in shutdown handlers
- Use `asyncio.wait_for()` with timeouts for critical operations

```python
# Good: Background task with proper cleanup
async def start(self):
    heartbeat_task = asyncio.create_task(self.heartbeat_task())
    try:
        await self.main_loop()
    finally:
        heartbeat_task.cancel()
        try:
            await asyncio.wait_for(heartbeat_task, timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("Task cleanup timeout")
```

## Type Hints

### Required Type Annotations
- All function signatures must include type hints
- Use `Optional[T]` for nullable values
- Use `Union[T1, T2]` for multiple types
- Use `List[T]`, `Dict[K, V]` for collections (or `list[T]`, `dict[K, V]` in Python 3.9+)
- Use `TYPE_CHECKING` for forward references to avoid circular imports

```python
from typing import Optional, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.trading.paper_engine import PaperTradingEngine

def get_trading_engine() -> Optional['PaperTradingEngine']:
    return shared_state.trading_engine
```

### Async Type Hints
- Use `Coroutine[Any, Any, T]` for coroutines when needed
- Use `Callable[[...], Awaitable[T]]` for async callbacks
- Return types for async functions should be `Awaitable[T]` or just `T` (Python infers)

## FastAPI Endpoints

### Endpoint Structure
- Use Pydantic models for request/response validation
- Include proper HTTP status codes
- Use dependency injection for shared resources (database, services)
- Include proper error handling with HTTPException
- Document endpoints with docstrings and response models

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional

class TradeRequest(BaseModel):
    """Trade execution request."""
    symbol: str = Field(..., example="BTCUSD")
    side: Optional[str] = Field(None, example="BUY")
    confidence: Optional[float] = Field(None, ge=0, le=1, example=0.75)

@app.post("/api/v1/trade", response_model=TradeResponse, tags=["Trading"])
async def execute_trade(request: TradeRequest, background_tasks: BackgroundTasks):
    """Execute a trade based on AI signal or manual input."""
    trading_engine = get_trading_engine()
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading agent not available")
    
    try:
        # Implementation
        return TradeResponse(status="filled", message="Trade executed", data=result)
    except Exception as e:
        logger.error(f"Trade execution error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### Error Handling
- Use appropriate HTTP status codes (400, 404, 500, 503)
- Include descriptive error messages
- Log errors with full context
- Use CORS headers in error responses

### WebSocket Endpoints
- Handle connection lifecycle properly
- Use ping/pong for keepalive
- Clean up connections in finally blocks
- Use thread-safe connection management

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    with websocket_clients_lock:
        websocket_clients.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong", "data": {}})
    except WebSocketDisconnect:
        pass
    finally:
        with websocket_clients_lock:
            if websocket in websocket_clients:
                websocket_clients.remove(websocket)
```

## SQLAlchemy Patterns

### Database Sessions
- Always use `SessionLocal()` with dependency injection in FastAPI
- Use `async with` for async database operations
- Close sessions properly in finally blocks
- Use `db.execute()` for raw SQL when needed

```python
from sqlalchemy.orm import Session
from src.core.database import SessionLocal

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/v1/positions", tags=["Portfolio"])
async def get_positions(db: Session = Depends(get_db)):
    """Get all active positions."""
    try:
        positions = db.query(Position).filter(Position.is_closed == False).all()
        return {"count": len(positions), "positions": positions}
    except Exception as e:
        logger.error(f"Database error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
```

### Model Definitions
- Use SQLAlchemy models with proper type annotations
- Include indexes for frequently queried fields
- Use relationships properly with lazy loading considerations
- Include timestamps (created_at, updated_at)

## Structured Logging

### Logging Patterns
- Use component-specific loggers via `get_component_logger()`
- Include structured context in log messages
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Include timestamps, component names, operation names, and context

```python
from src.core.logger import get_component_logger

class TradingAgent:
    def __init__(self):
        self.logger = get_component_logger("trading_agent")
    
    async def trading_loop(self):
        self.logger.info(
            "trading_iteration",
            "Trading iteration started",
            {
                "symbol": self.symbol,
                "balance": self.trading_engine.portfolio.balance,
                "time": format_timestamp(get_current_time_utc())
            }
        )
```

### Log Message Structure
- Operation name (e.g., "trading_iteration", "model_prediction")
- Human-readable message
- Context dictionary with relevant data
- Error information with `exc_info=True` for exceptions

### Error Logging
```python
try:
    result = await some_operation()
except Exception as e:
    logger.error(
        "operation_failed",
        f"Operation failed: {str(e)}",
        {"operation": "some_operation", "error_type": type(e).__name__},
        error=e,
        exc_info=True
    )
```

## ML Model Integration

### Model Loading
- Load models using GenericTradingModel interface
- Validate model files exist before loading
- Handle model loading errors gracefully
- Track model health and errors

```python
from src.ml.generic_model import GenericTradingModel
from pathlib import Path

def load_model(model_path: str) -> Optional[GenericTradingModel]:
    """Load a trading model from file."""
    path = Path(model_path)
    if not path.exists():
        logger.error(f"Model file not found: {model_path}")
        return None
    
    try:
        model = GenericTradingModel.load(model_path)
        logger.info(f"Model loaded successfully", model_path=model_path)
        return model
    except Exception as e:
        logger.error(f"Failed to load model", model_path=model_path, error=str(e))
        return None
```

### Model Predictions
- Always validate input data before prediction
- Handle prediction errors gracefully
- Include confidence scores and metadata
- Cache predictions when appropriate

### Model Coordination
- Use ModelCoordinator for multi-model systems
- Track model performance and health
- Handle model failures without crashing the system

## Error Handling

### Exception Handling Patterns
- Catch specific exceptions when possible
- Use try/except/finally for cleanup
- Log errors with full context
- Return None or raise appropriate exceptions

```python
async def fetch_with_retry(fetch_func, max_retries=5):
    """Fetch data with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            if asyncio.iscoroutinefunction(fetch_func):
                return await fetch_func()
            else:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, fetch_func)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed after {max_retries} attempts: {e}")
                return None
            wait_time = min(2 ** attempt, 60)
            await asyncio.sleep(wait_time)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            if attempt == max_retries - 1:
                return None
            await asyncio.sleep(2 ** attempt)
```

### Graceful Degradation
- Continue operation when non-critical components fail (e.g., Telegram bot)
- Use fallback mechanisms when possible
- Log failures but don't crash the system

## Configuration Management

### Config Access
- Use `settings` and `trading_config` from `src.core.config`
- Access nested config with `.get()` for optional values
- Provide defaults for missing config values

```python
from src.core.config import settings, trading_config

symbol = trading_config.trading.get('symbol', 'BTCUSD')
update_interval = trading_config.trading.get('update_interval', 300)
min_confidence = trading_config.signal_filters.get('min_confidence', 0.60)
```

## File Structure

### Import Organization
1. Standard library imports
2. Third-party imports
3. Local imports (from src.*)
4. Type checking imports (in TYPE_CHECKING block)

```python
# Standard library
import asyncio
import signal
from datetime import datetime, timezone
from typing import Optional, Dict

# Third-party
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Local imports
from src.core.config import settings
from src.core.logger import logger
from src.trading.paper_engine import PaperTradingEngine
```

### Module Organization
- Keep related functionality together
- Use `__init__.py` for package initialization
- Separate concerns (data, ML, trading, risk, monitoring)
- Follow existing project structure

## Testing Patterns

### Test Structure
- Use pytest for testing
- Use `pytest-asyncio` for async tests
- Mock external dependencies
- Test error cases and edge cases

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_fetch_data_with_retry():
    """Test retry logic with exponential backoff."""
    mock_fetch = AsyncMock(side_effect=[
        asyncio.TimeoutError(),
        {"data": "success"}
    ])
    
    result = await fetch_data_with_retry(mock_fetch, max_retries=3)
    assert result == {"data": "success"}
    assert mock_fetch.call_count == 2
```

## Code Quality

### Best Practices
- Write self-documenting code with clear variable names
- Use docstrings for all functions and classes
- Follow PEP 8 style guide
- Keep functions focused and single-purpose
- Avoid deep nesting (max 3-4 levels)
- Use early returns to reduce nesting

### Performance
- Use async I/O for concurrent operations
- Cache expensive operations (model predictions, API responses)
- Batch database operations when possible
- Use connection pooling for databases

