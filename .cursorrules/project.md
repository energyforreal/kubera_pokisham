# Project-Specific Cursor Rules

## Overview
Project-specific conventions and patterns for the Trading Agent project, including file structure, logging, error handling, and configuration management.

## Project Structure

### Directory Organization
```
Trading Agent/
├── backend/              # FastAPI backend
│   ├── api/              # API endpoints
│   ├── database/         # Database models and connections
│   ├── cache/            # Caching layer (Redis)
│   └── monitoring/       # Monitoring and metrics
├── src/                  # Core trading logic
│   ├── core/             # Core utilities (config, logger, database)
│   ├── data/             # Data fetching and synchronization
│   ├── ml/               # Machine learning models
│   ├── trading/          # Trading engine and execution
│   ├── risk/             # Risk management
│   ├── telegram/         # Telegram bot integration
│   └── monitoring/       # Health checks and diagnostics
├── ml_pipeline/          # ML training and evaluation
│   ├── models/           # Model implementations
│   ├── training/         # Training scripts
│   └── evaluation/       # Backtesting and evaluation
├── frontend_web/         # Next.js frontend
├── diagnostic_dashboard/ # Diagnostic dashboard
├── diagnostic_service/   # Diagnostic service
├── docs/                 # Documentation (MUST be well-organized)
│   ├── guides/           # User guides and how-to documentation
│   ├── architecture/     # System architecture and design docs
│   ├── deployment/      # Deployment and setup guides
│   ├── setup/           # Initial setup and configuration guides
│   ├── api/             # API documentation
│   └── README.md        # Documentation index
├── config/               # Configuration files
├── scripts/              # Utility scripts
├── monitoring/           # Prometheus/Grafana configs
└── logs/                 # Application logs
```

### Documentation Directory Structure
```
docs/
├── README.md             # Documentation index (main entry point)
├── guides/               # User guides and tutorials
│   ├── getting-started.md
│   ├── quick-start.md
│   ├── usage-guides.md
│   ├── bat-files.md
│   └── ...
├── architecture/         # System architecture documentation
│   ├── blueprint.md
│   ├── project-structure.md
│   └── ...
├── deployment/          # Deployment guides
│   ├── deployment-guide.md
│   ├── docker-deploy.md
│   ├── dashboard-setup.md
│   └── ...
├── setup/               # Setup and configuration guides
│   ├── credentials.md
│   ├── simple-start.md
│   └── ...
└── api/                 # API documentation
    └── ...
```

### File Naming Conventions
- Python files: `snake_case.py`
- TypeScript files: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- Configuration files: `kebab-case.yaml` or `snake_case.yaml`
- Test files: `test_*.py` or `*.test.ts` / `*.test.tsx`

### Import Path Organization
- Use absolute imports with project root in path
- For Python: `from src.core.config import settings`
- For TypeScript: Use path aliases (`@/components/...`)

```python
# Add project root to path
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import settings
from src.core.logger import logger
```

## File Organization

### Overview
**Maintaining a well-organized file structure is critical** for project maintainability, discoverability, and collaboration. All files, especially documentation, must be placed in the appropriate directories following established patterns.

### Documentation File Organization

#### Documentation Placement Rules
- **ALL `.md` files must be stored in relevant subdirectories within `docs/`**
- **DO NOT create `.md` files in the project root** unless they are essential project-level overviews
- **Only `README.md` should exist in the root** for project overview and navigation
- **Each documentation file must be placed in the appropriate `docs/` subdirectory** based on its purpose

#### Documentation Directory Structure
Use the following structure for organizing documentation files:

**`docs/guides/`** - User guides and how-to documentation
- Getting started guides
- Quick start instructions
- Usage guides and tutorials
- Feature-specific guides
- Examples: `getting-started.md`, `quick-start.md`, `usage-guides.md`, `bat-files.md`

**`docs/architecture/`** - System architecture and design documentation
- System blueprints
- Architecture diagrams
- Design decisions
- Project structure documentation
- Examples: `blueprint.md`, `project-structure.md`

**`docs/deployment/`** - Deployment and setup guides
- Production deployment guides
- Docker deployment instructions
- Service setup guides
- Dashboard setup
- Examples: `deployment-guide.md`, `docker-deploy.md`, `dashboard-setup.md`, `diagnostic-setup.md`

**`docs/setup/`** - Initial setup and configuration guides
- Credentials setup
- Configuration instructions
- Initial setup steps
- Environment setup
- Examples: `credentials.md`, `simple-start.md`, `start-instructions.md`

**`docs/api/`** - API documentation
- API endpoint documentation
- Request/response examples
- Authentication guides
- API usage examples

**`docs/README.md`** - Documentation index
- Central documentation hub
- Navigation to all documentation
- Quick links and guides

#### Documentation File Naming
- Use `kebab-case.md` for documentation files (e.g., `getting-started.md`, `deployment-guide.md`)
- Use descriptive, clear names that indicate content
- Avoid generic names like `readme.md`, `docs.md`, `guide.md` in subdirectories
- Keep names concise but informative

#### Examples of Proper Documentation Placement

```bash
# ✅ CORRECT: Documentation in appropriate directories
docs/guides/getting-started.md
docs/guides/quick-start.md
docs/architecture/blueprint.md
docs/deployment/deployment-guide.md
docs/setup/credentials.md

# ❌ INCORRECT: Documentation in root
README.md                    # ✅ OK - project overview
getting-started.md           # ❌ Move to docs/guides/
deployment.md                # ❌ Move to docs/deployment/
SETUP.md                     # ❌ Move to docs/setup/
```

### General File Organization Principles

#### Directory Structure Requirements
- **Maintain organized directory structure** - Follow established patterns
- **Group related files together** - Keep related functionality in the same directory
- **Use appropriate subdirectories** - Don't create unnecessary nesting, but don't flatten everything
- **Keep files focused and single-purpose** - Each file should have a clear, single purpose
- **Follow existing patterns** - Maintain consistency with existing structure
- **Avoid cluttering root directory** - Keep root clean with only essential files

#### Code File Organization
- **Python files** should be in appropriate module directories (`src/`, `backend/`, `ml_pipeline/`)
- **TypeScript files** should be in component/feature directories (`frontend_web/src/`)
- **Configuration files** should be in `config/` directory
- **Script files** should be in `scripts/` directory
- **Test files** should be in `tests/` or co-located with `test_` prefix

#### When Creating New Files

**Before creating a new file, ask:**
1. Does this file belong in an existing directory?
2. Should this be documentation? If yes, which `docs/` subdirectory?
3. Does this file follow naming conventions?
4. Will this file be easy to find later?
5. Does this maintain the organized structure?

**Documentation files (.md):**
- ✅ Place in appropriate `docs/` subdirectory
- ✅ Use descriptive kebab-case names
- ✅ Update `docs/README.md` with links if creating new documentation
- ❌ Never place in project root (except root `README.md`)

**Code files:**
- ✅ Place in appropriate module directory
- ✅ Follow language-specific naming conventions
- ✅ Group with related functionality
- ❌ Avoid creating new top-level directories without discussion

**Configuration files:**
- ✅ Place in `config/` directory
- ✅ Use descriptive names
- ✅ Document configuration options
- ❌ Avoid scattered config files

#### Maintaining Organization

**Regular Maintenance:**
- Review file structure periodically
- Move misplaced files to correct locations
- Remove orphaned or obsolete files
- Update documentation links when moving files
- Keep `docs/README.md` updated with accurate navigation

**Refactoring Guidelines:**
- When moving files, update all references
- Check imports, links, and documentation
- Update `.gitignore` if needed
- Document significant structural changes
- Maintain backward compatibility when possible

#### File Organization Checklist

When adding or organizing files:

- [ ] Is the file in the correct directory?
- [ ] Does it follow naming conventions?
- [ ] If it's documentation, is it in the right `docs/` subdirectory?
- [ ] Are related files grouped together?
- [ ] Is the directory structure logical and discoverable?
- [ ] Will other developers easily find this file?
- [ ] Does it maintain project organization principles?

#### Common Mistakes to Avoid

**❌ DON'T:**
- Create `.md` files in project root (except `README.md`)
- Scatter documentation files randomly
- Create deep, unnecessary directory nesting
- Mix unrelated files in the same directory
- Use inconsistent naming conventions
- Create files without considering organization
- Ignore existing directory structure

**✅ DO:**
- Place all documentation in appropriate `docs/` subdirectories
- Follow established directory patterns
- Group related files together
- Use consistent naming conventions
- Think about discoverability
- Maintain clean, organized structure
- Update documentation index when adding new docs

## Structured Logging

### Component Loggers
- Use `get_component_logger()` for component-specific logging
- Component name should match the module/class name
- Include session ID for tracking across components

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

### Log Message Format
- Use structured logging with operation names
- Include relevant context in context dictionary
- Use appropriate log levels:
  - DEBUG: Detailed diagnostic information
  - INFO: General informational messages
  - WARNING: Warning messages (non-critical issues)
  - ERROR: Error messages (operation failures)
  - CRITICAL: Critical errors (system may not continue)

```python
# Good: Structured log with context
self.logger.info(
    "model_prediction",
    "AI prediction generated",
    {
        "symbol": symbol,
        "prediction": signal['prediction'],
        "confidence": signal['confidence'],
        "timeframe": timeframe,
        "num_models": len(models)
    }
)

# Bad: Simple string logging
logger.info(f"Prediction: {prediction}")
```

### Error Logging
- Always include `exc_info=True` for exceptions
- Include operation context
- Log the error type and message
- Include relevant state information

```python
try:
    result = await some_operation()
except Exception as e:
    self.logger.error(
        "operation_failed",
        f"Operation failed: {str(e)}",
        {
            "operation": "some_operation",
            "error_type": type(e).__name__,
            "symbol": self.symbol,
            "state": self.get_state()
        },
        error=e,
        exc_info=True
    )
```

## Error Handling Patterns

### Graceful Degradation
- Continue operation when non-critical components fail
- Log failures but don't crash the system
- Use fallback mechanisms when available

```python
# Telegram bot is non-critical - continue without it
try:
    self.telegram_bot = TradingBot(self.trading_engine, predictor)
    await self.telegram_bot.initialize()
    await self.telegram_bot.start()
    logger.info("Telegram bot initialized")
except Exception as e:
    logger.warning(f"Telegram bot failed to start: {e}")
    logger.warning("Trading will continue WITHOUT Telegram notifications")
    self.telegram_bot = None
    # Don't raise - continue without Telegram
```

### Retry Logic
- Use exponential backoff for retries
- Limit maximum retry attempts
- Log retry attempts
- Return None or raise after max retries

```python
async def fetch_with_retry(fetch_func, max_retries=5, operation_name="fetch"):
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
                logger.error(f"{operation_name} failed after {max_retries} attempts: {e}")
                return None
            
            wait_time = min(2 ** attempt, 60)  # Exponential backoff, max 60s
            logger.warning(f"{operation_name} failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
            await asyncio.sleep(wait_time)
```

### Circuit Breakers
- Check circuit breakers before executing operations
- Log circuit breaker triggers
- Skip operations when circuit breaker is active
- Provide clear feedback about circuit breaker status

```python
circuit_status = self.trading_engine.circuit_breaker.check_all_breakers(
    self.trading_engine.portfolio.balance,
    self.trading_engine.portfolio.initial_balance
)

if circuit_status['triggered']:
    logger.warning(
        "Circuit breaker active - skipping trade execution",
        reason=circuit_status['reason'],
        details=circuit_status
    )
    await asyncio.sleep(self.update_interval)
    continue
```

## Configuration Management

### Configuration Access
- Use `settings` and `trading_config` from `src.core.config`
- Access nested config with `.get()` for optional values
- Provide sensible defaults
- Validate configuration on startup

```python
from src.core.config import settings, trading_config

# Required config with defaults
symbol = trading_config.trading.get('symbol', 'BTCUSD')
update_interval = trading_config.trading.get('update_interval', 300)
min_confidence = trading_config.signal_filters.get('min_confidence', 0.60)

# Nested config access
multi_model_config = trading_config.model.get('multi_model', {})
multi_model_enabled = multi_model_config.get('enabled', False)
strategy = multi_model_config.get('strategy', 'confirmation')
```

### Environment Variables
- Use `.env` file for sensitive configuration
- Provide `.env.example` with required variables
- Load environment variables using `python-dotenv`
- Validate required environment variables on startup

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    delta_api_key: str
    delta_api_secret: str
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

## Shared State Management

### Shared State Pattern
- Use `shared_state` module for cross-process communication
- Register components with shared state
- Access shared state from API endpoints
- Handle cases where components aren't registered

```python
from src.shared_state import shared_state

# Register components
shared_state.set_trading_agent_components(
    self.trading_engine,
    self.predictor,
    self.delta_client,
    self.risk_manager
)

# Access from API
def get_trading_engine() -> Optional[PaperTradingEngine]:
    """Get trading engine from shared state."""
    return shared_state.trading_engine

def get_predictor():
    """Get predictor from shared state with fallback."""
    if shared_state.predictor is not None:
        return shared_state.predictor
    return fallback_predictor
```

## Database Patterns

### Database Initialization
- Initialize database on startup
- Create tables if they don't exist
- Handle database connection errors gracefully
- Use connection pooling

```python
from src.core.database import SessionLocal, init_db

# Initialize database
init_db()
self.db = SessionLocal()

# Use in endpoints
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Database Sessions
- Always close sessions in finally blocks
- Use dependency injection in FastAPI
- Handle database errors appropriately
- Use transactions for atomic operations

## Health Monitoring

### Health Check Pattern
- Update health status regularly
- Track key metrics (uptime, models loaded, errors)
- Write health status to file for cross-process access
- Include health status in API responses

```python
from src.monitoring.health_check import get_health_check

health_check = get_health_check()
health_check.heartbeat()
health_check.update_models_loaded(model_count)
health_check.update_circuit_breaker(is_active)

# Health status
status = health_check.get_status()
```

### Diagnostic Reporting
- Report key events to diagnostic service
- Include context in diagnostic reports
- Handle diagnostic service failures gracefully
- Use async reporting to avoid blocking

```python
from src.monitoring.diagnostic_reporter import get_diagnostic_reporter

diagnostic_reporter = get_diagnostic_reporter()
await diagnostic_reporter.report_trade_execution(trade_result)
await diagnostic_reporter.report_signal_generation(signal)
await diagnostic_reporter.report_error(error_message, context)
```

## API Integration Patterns

### Backend API Communication
- Use aiohttp for async HTTP requests
- Handle connection errors gracefully
- Include timeout for requests
- Don't block trading loop on API failures

```python
async def notify_backend_api(event_type: str, data: dict, backend_url: str = "http://localhost:8000"):
    """Notify backend API of events for real-time WebSocket broadcasts."""
    if aiohttp is None:
        logger.warning("aiohttp not available - skipping backend notification")
        return
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{backend_url}/api/v1/internal/broadcast",
                json={'type': event_type, 'data': data},
                timeout=aiohttp.ClientTimeout(total=2)
            ) as response:
                if response.status == 200:
                    logger.debug("Backend notified successfully", event_type=event_type)
    except Exception as e:
        logger.debug(f"Failed to notify backend (non-critical)", event_type=event_type, error=str(e))
    # Never raise exceptions - notification failures should not stop trading
```

## Activity Tracking

### Activity Logging
- Log all significant activities (trades, signals, errors)
- Include timestamps and context
- Use activity manager for centralized activity tracking
- Support WebSocket streaming for real-time updates

```python
from src.monitoring.activity_manager import activity_manager

activity_manager.log_activity(
    'trade',
    f"Trade executed: {signal['prediction']} {quantity} {symbol} @ ${price:,.2f}",
    {
        'symbol': symbol,
        'action': signal['prediction'],
        'quantity': quantity,
        'price': price,
        'pnl': pnl,
        'status': status
    },
    'success'
)
```

## File Management

### Log File Cleanup
- Clean up old log files on startup
- Configure log retention (e.g., 30 days)
- Compress old log files
- Monitor log directory size

```python
from src.core.logger import cleanup_logs_on_startup

# Clean up old logs on startup
cleanup_stats = cleanup_logs_on_startup()
logger.info("log_cleanup", "Log cleanup completed", {"stats": cleanup_stats})
```

## Development Workflow

### Windows Batch Files (.bat)

#### Purpose
- The project includes `.bat` files for Windows development workflow
- These scripts simplify starting and stopping services on Windows
- They provide error checking and user-friendly messages

#### Available Batch Files

**`start_trading_bot.bat`**
- Starts the trading bot using `run_bot_safe.py`
- Checks for Python installation before starting
- Provides clear instructions for stopping (Ctrl+C)
- Use this for production-like bot execution

**`stop_trading_bot.bat`**
- Stops the trading bot gracefully
- Handles cleanup and process termination
- Use when you need to stop the bot cleanly

**`Kubera Pokisham Enhanced v2.0.bat`**
- Enhanced launcher with additional features
- May include multiple service startup
- Check documentation for specific usage

#### Usage Guidelines

```batch
# Start the trading bot
start_trading_bot.bat

# Stop the trading bot
stop_trading_bot.bat
```

#### When to Use .bat Files vs Direct Python Execution

**Use .bat files when:**
- Developing on Windows
- Need convenient one-click startup
- Want error checking and user messages
- Working with production-like workflows
- Sharing development setup with team members

**Use direct Python execution when:**
- Running in integrated terminal/IDE
- Need fine-grained control over arguments
- Debugging specific issues
- Cross-platform compatibility required

```python
# Direct Python execution for debugging
python run_bot_safe.py

# Or with explicit Python path
python -m src.main
```

#### Best Practices
- Always check Python is installed before running
- Use `start_trading_bot.bat` for standard development
- Keep .bat files simple and maintainable
- Document any custom .bat files in project README
- Test .bat files after environment changes

### Cursor Browser Debugging

#### Overview
Cursor includes a built-in browser functionality that makes debugging localhost services extremely convenient and effective. Use this instead of switching to external browsers for a seamless debugging experience.

#### Why Use Cursor's Browser
- **Integrated Experience**: No need to switch windows between editor and browser
- **Quick Access**: Fast navigation to localhost URLs
- **Debugging Tools**: Access to console and network tools within Cursor
- **Efficient Workflow**: See code changes and test immediately
- **Context Preservation**: Keep your focus in the development environment

#### Available Services

The project runs several localhost services that can be accessed via Cursor's browser:

**FastAPI Backend**
- **Main API**: `http://localhost:8000`
- **API Documentation (Swagger UI)**: `http://localhost:8000/docs`
- **Alternative Docs (ReDoc)**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/api/v1/health`
- **Metrics (Prometheus)**: `http://localhost:8000/metrics`

**Next.js Frontend**
- **Main Dashboard**: `http://localhost:3001`
- **Alternative Port**: Check `frontend_web/package.json` for configured port

**Grafana Monitoring**
- **Grafana Dashboard**: `http://localhost:3000`
- Default credentials: `admin/admin` (change in production)
- Access monitoring dashboards and metrics

**Prometheus**
- **Prometheus UI**: `http://localhost:9090`
- View collected metrics
- Query metrics data

#### Usage Workflow

**1. Starting Services**
```bash
# Start FastAPI backend (in terminal)
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

# Start Next.js frontend (in separate terminal)
cd frontend_web
npm run dev

# Or use batch files on Windows
start_trading_bot.bat
```

**2. Opening in Cursor Browser**
- Use Cursor's browser navigation tools to open localhost URLs
- Navigate directly to `http://localhost:8000/docs` for API testing
- Open `http://localhost:3001` to view the frontend dashboard
- Access `http://localhost:3000` for Grafana monitoring

**3. Debugging Workflow**
1. Make code changes in Cursor editor
2. Services auto-reload (with `--reload` flag)
3. Immediately test in Cursor browser
4. Check console/network in browser tools
5. Iterate quickly without context switching

#### Testing API Endpoints

**Using FastAPI Docs (Swagger UI)**
```
http://localhost:8000/docs
```
- Interactive API documentation
- Test endpoints directly in browser
- See request/response schemas
- No need for Postman or curl

**Example: Testing Trade Execution**
1. Navigate to `http://localhost:8000/docs`
2. Find `/api/v1/trade` endpoint
3. Click "Try it out"
4. Enter trade parameters
5. Execute and see response
6. Check logs in Cursor terminal

#### Frontend Development

**Hot Reload Workflow**
1. Edit React components in Cursor
2. Save changes
3. Next.js auto-reloads in browser
4. See changes instantly in Cursor browser
5. Debug with React DevTools if available

**API Integration Testing**
1. Make API call from frontend
2. See network request in browser dev tools
3. Check backend logs in Cursor terminal
4. Verify response data
5. Iterate on both frontend and backend

#### Monitoring and Debugging

**Grafana Dashboard**
```
http://localhost:3000
```
- Monitor system health in real-time
- View trading metrics
- Check model performance
- Observe error rates and alerts

**Prometheus Metrics**
```
http://localhost:9090
```
- Query raw metrics
- Create custom queries
- Debug metric collection
- Verify instrumentation

#### Best Practices

**Development Workflow**
- Keep Cursor browser open to localhost during development
- Use bookmarks/favorites for frequently accessed URLs
- Test API changes immediately after implementation
- Monitor services while making changes
- Use browser dev tools for frontend debugging

**Quick Testing Checklist**
1. ✅ Backend health: `http://localhost:8000/api/v1/health`
2. ✅ API docs accessible: `http://localhost:8000/docs`
3. ✅ Frontend loads: `http://localhost:3001`
4. ✅ WebSocket connections work
5. ✅ Metrics being collected: `http://localhost:8000/metrics`

**Debugging Tips**
- Use browser console for frontend errors
- Check network tab for API request/response details
- Monitor terminal logs for backend errors
- Use React DevTools for component debugging
- Check Grafana for system-wide metrics

**Integration Testing**
- Test full workflow: Frontend → API → Backend → Database
- Verify WebSocket real-time updates
- Check error handling end-to-end
- Validate data flow through system
- Test with Cursor browser before deploying

## Testing Patterns

### Integration Testing
- Test component integration
- Mock external dependencies (API calls, database)
- Test error scenarios
- Test graceful degradation

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_trading_agent_integration():
    """Test trading agent with mocked dependencies."""
    mock_delta_client = MagicMock()
    mock_predictor = MagicMock()
    
    agent = TradingAgent()
    agent.delta_client = mock_delta_client
    agent.predictor = mock_predictor
    
    # Test integration
    await agent.initialize()
    assert agent.is_running == False  # Not started yet
```

## Code Organization

### Module Imports
- Group imports: standard library, third-party, local
- Use TYPE_CHECKING for forward references
- Avoid circular imports
- Use absolute imports

### Class Organization
- Keep related methods together
- Use private methods (prefixed with `_`) for internal operations
- Document public APIs with docstrings
- Separate initialization, business logic, and cleanup

## Best Practices

### Single Responsibility
- Each class/function should have a single responsibility
- Keep functions focused and small
- Extract complex logic into separate functions
- Use composition over inheritance

### Error Recovery
- Design systems to recover from errors
- Log errors with full context
- Continue operation when possible
- Provide fallback mechanisms

### Performance
- Use async I/O for concurrent operations
- Cache expensive operations (model predictions, API responses)
- Batch database operations
- Monitor performance metrics

