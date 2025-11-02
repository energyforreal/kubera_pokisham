# Cursorrules Guidelines Deviations Report

## Executive Summary

This report identifies deviations from the cursorrules guidelines across the Trading Agent project. Issues are categorized by severity (High/Medium/Low) and type.

## Critical Issues Found

### 1. Python Code Issues

#### High Priority

**1.1 Incorrect Logging Format** 
- **Rule Violated**: `project.md` - Structured logging format must be `logger.info("operation_name", "message", {context})`
- **Issue**: Many locations use f-strings or direct string formatting instead of structured format
- **Files Affected**:
  - `src/main.py`: 85+ instances
  - `src/data/delta_client.py`: Lines 65, 74, 139-140
  - `src/monitoring/health_check.py`: Lines 97, 125, 183, 186, 199
  - `src/telegram/bot.py`: Lines 101, 148
  - `src/ml/model_coordinator.py`: Multiple instances
  - `src/data/data_sync.py`: Multiple instances
  - `src/data/multi_timeframe_sync.py`: Multiple instances
  - `src/monitoring/activity_manager.py`: Multiple instances
  - `src/ml/multi_model_predictor.py`: Multiple instances
  - `src/ml/generic_model.py`: Lines 30, 64, 106
  - `src/data/data_validator.py`: Lines 81, 163
  - `src/risk/position_sizer.py`: Line 71
  - `src/ml/trainer.py`: Lines 208, 236

- **Examples**:
  ```python
  # WRONG:
  logger.error(f"Error stopping Telegram bot: {e}", exc_info=True)
  logger.warning(f"Failed to save health check to {self.health_file}", error=str(e))
  logger.debug(f"API request", method=method, endpoint=endpoint)
  
  # CORRECT:
  self.logger.error(
      "bot_stop_failed",
      f"Error stopping Telegram bot: {e}",
      {"bot_running": self.is_running},
      error=e,
      exc_info=True
  )
  self.logger.warning(
      "health_save_failed",
      f"Failed to save health check to {self.health_file}",
      {"health_file": str(self.health_file)},
      error=e
  )
  self.logger.debug(
      "api_request",
      "API request initiated",
      {"method": method, "endpoint": endpoint}
  )
  ```

**1.2 Missing Return Type Annotations**
- **Rule Violated**: `python.md` - All function signatures must include type hints
- **Files Affected**:
  - `src/data/delta_client.py`: Line 32 - `_generate_signature()` returns tuple but annotated as `str`
  - `src/telegram/bot.py`: 
    - Line 54: `async def initialize(self):` - Missing return type (`-> None`)
    - Line 70: `async def start(self):` - Missing return type (`-> None`)
    - Line 84: `async def stop(self):` - Missing return type (`-> None`)
    - Line 109: `async def notify_signal(self, signal: dict):` - Missing return type
    - Line 117: `async def notify_trade(self, trade_result: dict):` - Missing return type
    - Line 125: `async def notify_risk_alert(self, alert: dict):` - Missing return type
    - Line 133: `async def send_daily_report(self, report: dict):` - Missing return type
    - Line 141: `def cleanup(self):` - Missing return type (`-> None`)
  - `backend/api/main.py`:
    - Line 61: `def get_predictor():` - Missing return type annotation
  - `src/monitoring/health_check.py`: Several methods missing return types
  - `src/telegram/handlers.py`: All async methods missing return type annotations

- **Examples**:
  ```python
  # WRONG:
  async def initialize(self):
      """Initialize the bot application."""
      
  def cleanup(self):
      """Cleanup resources."""
      
  # CORRECT:
  async def initialize(self) -> None:
      """Initialize the bot application."""
      
  def cleanup(self) -> None:
      """Cleanup resources."""
  ```

**1.3 Missing Type Hints in Helper Functions**
- **Rule Violated**: `python.md` - All function signatures must include type hints
- **Files Affected**:
  - `backend/api/main.py`: Line 35 - `parse_dt_or_none(value)` missing type hints
  - `src/main.py`: Line 261 - `async def _fetch_with_retry(...)` missing some type hints

- **Examples**:
  ```python
  # WRONG:
  def parse_dt_or_none(value):
      try:
          if not value:
              return None
          from datetime import datetime
          return datetime.fromisoformat(value)
      except Exception:
          return None
  
  # CORRECT:
  def parse_dt_or_none(value: Optional[str]) -> Optional[datetime]:
      try:
          if not value:
              return None
          from datetime import datetime
          return datetime.fromisoformat(value)
      except Exception:
          return None
  ```

**1.4 Incorrect Return Type in `_generate_signature`**
- **Rule Violated**: `python.md` - Type hints must match actual return types
- **File**: `src/data/delta_client.py`, Line 32
- **Issue**: Function returns tuple `(signature, timestamp)` but annotated as `str`
- **Fix**:
  ```python
  # WRONG:
  def _generate_signature(self, method: str, endpoint: str, payload: str = "") -> str:
      # ... returns (signature, timestamp)
  
  # CORRECT:
  def _generate_signature(self, method: str, endpoint: str, payload: str = "") -> tuple[str, str]:
      # ... returns (signature, timestamp)
  ```

#### Medium Priority

**1.5 Using Bare `logger` Instead of Component Logger**
- **Rule Violated**: `project.md` - Use `get_component_logger()` for component-specific logging
- **Files Affected**:
  - `src/main.py`: Multiple instances of `logger.` instead of `self.logger.`
  - `src/telegram/bot.py`: Lines 88, 92, 95, 98, 101, 106, 146, 148
  - `src/trading/paper_engine.py`: Lines 195, 206, 223, 263, 326, 430, 437
  - `src/risk/risk_manager.py`: Line 287
  - `src/ml/trainer.py`: Multiple instances
  - `src/monitoring/health_check.py`: Line 125

- **Examples**:
  ```python
  # WRONG:
  logger.info("Stopping Telegram bot...")
  
  # CORRECT:
  self.logger.info("bot_stop", "Stopping Telegram bot...")
  ```

**1.6 Mixed Logging Patterns**
- **Rule Violated**: `project.md` - Consistent structured logging format
- **Files Affected**: 
  - `src/trading/paper_engine.py`: Mix of structured and unstructured logging
  - `src/risk/risk_manager.py`: Inconsistent logging patterns
  - `src/main.py`: Mix of both patterns throughout

#### Low Priority

**1.7 Import Organization Issues**
- **Rule Violated**: `python.md` - Standard library → third-party → local imports
- **Files Affected**: 
  - `backend/api/main.py`: Line 43 - Import statement in middle of code (should be at top)
- **Example**:
  ```python
  # WRONG (Line 43):
  from backend.cache.prediction_cache import PredictionCache
  # This import is after other code
  
  # CORRECT: Move to top with other imports
  ```

### 2. TypeScript Code Issues

#### High Priority

**2.1 Use of `any` Type**
- **Rule Violated**: `typescript.md` - Avoid `any`, use proper types
- **Files Affected**:
  - `frontend_web/src/services/api.ts`:
    - Line 80: `individual_predictions?: any[];` 
    - Line 94: `positions: any[];`
    - Line 141: `updateRiskSettings: (data: any) =>`
    - Line 155: `private listeners: Map<string, Function[]>`
    - Line 203: `on(eventType: string, callback: Function)`
    - Line 210: `off(eventType: string, callback: Function)`
    - Line 220: `private emit(eventType: string, data: any)`
  - `frontend_web/src/components/DataImport.tsx`:
    - Line 48: `const trade: any = {};`

- **Examples**:
  ```typescript
  // WRONG:
  individual_predictions?: any[];
  positions: any[];
  updateRiskSettings: (data: any) => ...
  
  // CORRECT:
  individual_predictions?: IndividualPrediction[];
  positions: Position[];
  updateRiskSettings: (data: RiskSettingsUpdate) => ...
  ```

**2.2 Using `Function` Type Instead of Proper Function Types**
- **Rule Violated**: `typescript.md` - Use proper function types
- **File**: `frontend_web/src/services/api.ts`, Lines 155, 203, 210
- **Examples**:
  ```typescript
  // WRONG:
  private listeners: Map<string, Function[]>
  on(eventType: string, callback: Function)
  
  // CORRECT:
  private listeners: Map<string, ((data: unknown) => void)[]>
  on(eventType: string, callback: (data: unknown) => void)
  ```

#### Medium Priority

**2.3 Missing Return Type Annotations**
- **Rule Violated**: `typescript.md` - Functions should have explicit return types
- **Files Affected**:
  - `frontend_web/src/services/api.ts`:
    - Line 157: `connect() { ... }` - Missing return type (`void`)
    - Line 203: `on(eventType: string, callback: Function) { ... }` - Missing return type
    - Line 210: `off(eventType: string, callback: Function) { ... }` - Missing return type
    - Line 227: `disconnect() { ... }` - Missing return type (`void`)
  - `frontend_web/src/components/DataImport.tsx`:
    - Line 28: `export default function DataImport() { ... }` - Missing return type (`JSX.Element`)

- **Examples**:
  ```typescript
  // WRONG:
  connect() {
      // ...
  }
  
  // CORRECT:
  connect(): void {
      // ...
  }
  ```

**2.4 Missing Type Definitions for Positions and Predictions**
- **Rule Violated**: `typescript.md` - Define types for all API responses
- **File**: `frontend_web/src/services/api.ts`
- **Issue**: Missing interfaces for `Position` and `IndividualPrediction` types
- **Fix Needed**:
  ```typescript
  interface Position {
    symbol: string;
    side: 'BUY' | 'SELL';
    entry_price: number;
    size: number;
    stop_loss?: number;
    take_profit?: number;
    unrealized_pnl: number;
    timestamp: string;
  }
  
  interface IndividualPrediction {
    model_name: string;
    prediction: string;
    confidence: number;
    // ... other fields
  }
  ```

## Summary by File

### Python Files

| File | Issues Count | Priority |
|------|-------------|----------|
| `src/main.py` | 85+ logging format issues | High |
| `src/data/delta_client.py` | 3 issues (logging, return type) | High |
| `src/telegram/bot.py` | 10 issues (missing return types, logging) | High |
| `src/monitoring/health_check.py` | 5+ issues (logging format) | High |
| `src/ml/model_coordinator.py` | Multiple logging issues | High |
| `src/data/data_sync.py` | Multiple logging issues | High |
| `backend/api/main.py` | 2 issues (import order, missing return type) | Medium |
| `src/trading/paper_engine.py` | Multiple logging issues | Medium |
| `src/risk/risk_manager.py` | Logging issues | Medium |

### TypeScript Files

| File | Issues Count | Priority |
|------|-------------|----------|
| `frontend_web/src/services/api.ts` | 8+ issues (any types, Function types) | High |
| `frontend_web/src/components/DataImport.tsx` | 2 issues (any type) | High |

## Recommendations

### Priority 1 (High) - Immediate Fixes

1. **Standardize Logging Format**
   - Convert all f-string logging to structured format: `logger.info("operation_name", "message", {context})`
   - Replace bare `logger` with component loggers: `self.logger`
   - Estimated effort: 2-3 days

2. **Add Missing Return Type Annotations**
   - Add `-> None` to all async functions that don't return values
   - Fix `_generate_signature()` return type
   - Add return types to TypeScript functions
   - Estimated effort: 1 day

3. **Replace `any` Types in TypeScript**
   - Create proper interfaces for all types
   - Replace `any[]` with typed arrays
   - Replace `Function` with proper function types
   - Estimated effort: 1 day

### Priority 2 (Medium) - Short-term Fixes

1. **Fix Import Organization**
   - Move misplaced imports to top of files
   - Ensure proper grouping (stdlib → third-party → local)

2. **Add Missing Type Definitions**
   - Create interfaces for `Position`, `IndividualPrediction`, etc.
   - Update API client with proper types

### Priority 3 (Low) - Long-term Improvements

1. **Audit All Files for Consistency**
   - Systematic review of all Python files
   - Systematic review of all TypeScript files
   - Document patterns for future development

## Testing Recommendations

After fixing these issues:
1. Run type checking: `mypy src/` for Python, `tsc --noEmit` for TypeScript
2. Verify logging format consistency
3. Check that all component loggers are being used correctly
4. Ensure no new `any` types are introduced

## Conclusion

The project has several deviations from cursorrules guidelines, primarily:
- **Incorrect logging format** (most common issue)
- **Missing type annotations** (Python return types, TypeScript `any` types)
- **Inconsistent component logger usage**

Most issues are fixable with systematic refactoring. The logging format issues are the most widespread and should be addressed first as they affect code consistency and maintainability.

