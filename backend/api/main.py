"""FastAPI main application for AI Trading Agent."""

import asyncio
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import settings, trading_config
from src.core.database import SessionLocal, init_db
from src.core.logger import logger, get_component_logger
from src.data.delta_client import DeltaExchangeClient
from src.ml.predictor import TradingPredictor
from src.ml.multi_model_predictor import MultiModelPredictor
from src.trading.paper_engine import PaperTradingEngine
from src.risk.risk_manager import RiskManager
from src.monitoring.health_check import get_health_check
from src.shared_state import shared_state
from backend.monitoring.prometheus_metrics import metrics_collector, get_metrics_response
from backend.api.diagnostic import router as diagnostic_router

# Helper to parse ISO timestamps safely
def parse_dt_or_none(value):
    try:
        if not value:
            return None
        from datetime import datetime
        return datetime.fromisoformat(value)
    except Exception:
        return None
from backend.cache.prediction_cache import PredictionCache

# Global instances
health_check_instance = get_health_check()
websocket_clients: List[WebSocket] = []
websocket_clients_lock = threading.Lock()
prediction_cache = PredictionCache(ttl_seconds=300)  # 5 minute cache to match signal generation interval

# Fallback instances for when trading agent isn't running
fallback_predictor: Optional[TradingPredictor] = None
fallback_delta_client: Optional[DeltaExchangeClient] = None


def get_trading_engine() -> Optional[PaperTradingEngine]:
    """Get trading engine from shared state."""
    return shared_state.trading_engine


def get_predictor():
    """Get predictor from shared state with fallback.
    
    Returns predictor (TradingPredictor, MultiModelPredictor, or ModelCoordinator).
    """
    if shared_state.predictor is not None:
        return shared_state.predictor
    return fallback_predictor


def get_delta_client() -> Optional[DeltaExchangeClient]:
    """Get delta client from shared state with fallback."""
    if shared_state.delta_client is not None:
        return shared_state.delta_client
    return fallback_delta_client


def get_risk_manager() -> Optional[RiskManager]:
    """Get risk manager from shared state."""
    return shared_state.risk_manager


def check_trading_agent_available() -> bool:
    """Check if trading agent is available (with fallback support)."""
    # If trading agent is running, use it
    if shared_state.is_trading_agent_running and shared_state.trading_engine is not None:
        return True
    # Otherwise, check if fallbacks are available for read-only operations
    return fallback_predictor is not None or fallback_delta_client is not None


# Pydantic models for API
class TradeRequest(BaseModel):
    """Trade execution request."""
    symbol: str = Field(..., example="BTCUSD")
    side: Optional[str] = Field(None, example="BUY", description="BUY or SELL, if not provided will use AI signal")
    confidence: Optional[float] = Field(None, ge=0, le=1, example=0.75)
    force: bool = Field(False, description="Force trade even if signal confidence is low")


class TradeResponse(BaseModel):
    """Trade execution response."""
    status: str
    message: str
    data: Optional[Dict] = None


class PredictionResponse(BaseModel):
    """AI prediction response."""
    symbol: str
    prediction: str
    confidence: float
    is_actionable: bool
    timestamp: datetime
    individual_predictions: Optional[List[Dict]] = None
    data_quality: float
    # Add missing fields for better frontend compatibility
    model_name: Optional[str] = None
    features_used: Optional[List[str]] = None


class PortfolioStatus(BaseModel):
    """Portfolio status response."""
    balance: float
    equity: float
    num_positions: int
    total_pnl: float
    total_pnl_percent: float
    daily_pnl: float
    positions: List[Dict]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    uptime_seconds: float
    models_loaded: int
    last_signal: Optional[datetime]
    last_trade: Optional[datetime]
    circuit_breaker_active: bool
    error_count: int
    signals_count: int
    trades_count: int


class InternalBroadcastRequest(BaseModel):
    """Internal broadcast request from trading agent."""
    type: str = Field(..., example="trade")
    data: Dict = Field(..., example={"symbol": "BTCUSD", "status": "filled"})


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    global fallback_predictor, fallback_delta_client
    
    from src.utils.timestamp import get_time_display
    
    logger.info("Starting FastAPI application...", **get_time_display())
    
    # Initialize database
    init_db()
    
    # Initialize fallback instances for when trading agent isn't running
    try:
        logger.info("Initializing fallback instances...", **get_time_display())
        
        # Check if multi-model is enabled
        multi_model_config = trading_config.model.get('multi_model', {})
        multi_model_enabled = multi_model_config.get('enabled', False)
        
        if multi_model_enabled:
            strategy = multi_model_config.get('strategy', 'confirmation')
            fallback_predictor = MultiModelPredictor(strategy=strategy)
            logger.info(f"Fallback multi-model predictor initialized", strategy=strategy, **get_time_display())
        else:
            fallback_predictor = TradingPredictor()
            logger.info("Fallback predictor initialized", **get_time_display())
        
        fallback_delta_client = DeltaExchangeClient()
        logger.info("Fallback Delta client initialized", **get_time_display())
        
    except Exception as e:
        logger.error(f"Failed to initialize fallback instances: {e}", **get_time_display())
        fallback_predictor = None
        fallback_delta_client = None
    
    # Wait for trading agent to register components with proper synchronization
    logger.info("Waiting for trading agent to register components...", **get_time_display())
    
    # Wait up to 30 seconds for trading agent with better synchronization
    agent_connected = False
    for i in range(30):
        if (shared_state.is_trading_agent_running and 
            shared_state.trading_engine is not None and
            shared_state.predictor is not None):
            logger.info("Trading agent connected with all components!", **get_time_display())
            agent_connected = True
            break
        await asyncio.sleep(1)
    
    if not agent_connected:
        logger.warning("Trading agent not connected - using fallback mode for read-only operations", **get_time_display())
    
    # Initialize health check
    health_check_instance.heartbeat()
    
    logger.info("FastAPI application started successfully", **get_time_display())
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...", **get_time_display())


# Initialize component logger
api_logger = get_component_logger("backend_api")

app = FastAPI(
    title="AI Trading Agent API",
    description="Production-ready AI trading agent with ML predictions and risk management",
    version="1.0.0",
    lifespan=lifespan
)

api_logger.info("initialization", "FastAPI application created", {
    "title": "AI Trading Agent API",
    "version": "1.0.0"
})

# CORS middleware
import os
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Environment-specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include diagnostic router
app.include_router(diagnostic_router)


# Global exception handlers with CORS headers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler that ensures CORS headers on all errors."""
    logger.error(f"Unhandled exception", 
                error=str(exc), 
                path=request.url.path,
                method=request.method,
                exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "error": "Internal Server Error",
            "path": request.url.path
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with CORS headers."""
    logger.warning(f"Validation error", 
                  error=str(exc),
                  path=request.url.path)
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "error": "Validation Error"
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


# Dependency for database session
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "name": "AI Trading Agent API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health_check_endpoint():
    """Health check endpoint that prefers bot-written health file for cross-process accuracy."""
    import time
    start_time = time.time()
    
    api_logger.info("api_request", "Health check endpoint called")
    
    try:
        # Prefer cross-process health written by the trading agent
        from pathlib import Path
        import json
        health_path = Path("bot_health.json")
        if health_path.exists():
            data = json.loads(health_path.read_text())
            last_hb = data.get('last_heartbeat')
            last_hb_dt = parse_dt_or_none(last_hb)
            
            # Check if heartbeat is recent (within 2 minutes)
            recent = False
            heartbeat_age = None
            if last_hb_dt is not None:
                heartbeat_age = (datetime.utcnow() - last_hb_dt.replace(tzinfo=None)).total_seconds()
                recent = heartbeat_age < 120
            
            is_alive = bool(data.get('is_alive'))
            cb_active = bool(data.get('circuit_breaker_active', False))
            models_loaded = int(data.get('models_loaded', 0))
            
            # Determine health status
            if not is_alive or not recent:
                status = "critical"  # Bot not running or stale heartbeat
            elif cb_active or models_loaded == 0:
                status = "degraded"  # Circuit breaker active or no models loaded
            else:
                status = "healthy"
            
            logger.debug(
                "Health check from bot_health.json",
                status=status,
                is_alive=is_alive,
                recent=recent,
                heartbeat_age=heartbeat_age,
                models_loaded=models_loaded,
                circuit_breaker=cb_active
            )
            
            duration_ms = (time.time() - start_time) * 1000
            api_logger.info("api_response", "Health check completed successfully", {
                "status": status,
                "is_alive": is_alive,
                "models_loaded": models_loaded,
                "circuit_breaker_active": cb_active,
                "duration_ms": duration_ms
            })
            
            return HealthResponse(
                status=status,
                timestamp=datetime.utcnow(),
                uptime_seconds=float(data.get('uptime_seconds', 0)),
                models_loaded=models_loaded,
                last_signal=parse_dt_or_none(data.get('last_signal')),
                last_trade=parse_dt_or_none(data.get('last_trade')),
                circuit_breaker_active=cb_active,
                error_count=int(data.get('errors_count', 0)),
                signals_count=int(data.get('signals_count', 0)),
                trades_count=int(data.get('trades_count', 0))
            )
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        api_logger.error("api_error", "Failed to read bot_health.json", {
            "error": str(e),
            "duration_ms": duration_ms
        }, error=e)

    # Fallback to in-process health if file not available
    api_logger.info("api_fallback", "Using fallback health check (bot_health.json not available)")
    status = health_check_instance.get_status()
    shared_status = shared_state.get_status()
    
    # Determine fallback health
    is_healthy = (
        not status.get('circuit_breaker_active', False) and 
        shared_status.get('is_trading_agent_running', False) and
        status.get('models_loaded', 0) > 0
    )
    
    duration_ms = (time.time() - start_time) * 1000
    api_logger.info("api_response", "Fallback health check completed", {
        "status": "healthy" if is_healthy else "degraded",
        "duration_ms": duration_ms
    })
    
    return HealthResponse(
        status="healthy" if is_healthy else "degraded",
        timestamp=datetime.utcnow(),
        uptime_seconds=status.get('uptime_seconds', 0),
        models_loaded=status.get('models_loaded', 0),
        last_signal=parse_dt_or_none(status['last_signal']) if isinstance(status.get('last_signal'), str) else status.get('last_signal'),
        last_trade=parse_dt_or_none(status['last_trade']) if isinstance(status.get('last_trade'), str) else status.get('last_trade'),
        circuit_breaker_active=status.get('circuit_breaker_active', False),
        error_count=status.get('errors_count', 0),
        signals_count=status.get('signals_count', 0),
        trades_count=status.get('trades_count', 0)
    )


@app.get("/api/v1/status", tags=["Health"])
async def get_system_status():
    """Get detailed system status including shared state."""
    try:
        health_status = health_check_instance.get_status()
        shared_status = shared_state.get_status()
        
        return {
            "health": health_status,
            "shared_state": shared_status,
            "api_status": "running",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Status check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Status check failed")


@app.get("/api/v1/predict", response_model=PredictionResponse, tags=["Trading"])
async def get_prediction(symbol: str = "BTCUSD", timeframe: str = "4h", force_refresh: bool = False):
    """
    Get AI trading prediction for a symbol (with intelligent caching).
    
    Args:
        symbol: Trading symbol (e.g., BTCUSD)
        timeframe: Timeframe (e.g., 4h, 1h, 15m) - defaults to 4h for production models
        force_refresh: Force regenerate prediction (bypass cache)
    
    Returns:
        AI prediction with confidence score
    """
    predictor = get_predictor()
    if not predictor:
        raise HTTPException(status_code=503, detail="Prediction service unavailable - no predictor available")
    
    try:
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_signal = prediction_cache.get(symbol, timeframe)
            if cached_signal:
                logger.debug("Returning cached prediction", symbol=symbol, timeframe=timeframe, 
                           age_seconds=int(cached_signal.get('cache_age', 0)))
                return PredictionResponse(**cached_signal)
        
        # Generate new prediction
        source = 'trading_agent' if shared_state.is_trading_agent_running else 'fallback'
        logger.info("Generating fresh prediction", symbol=symbol, timeframe=timeframe, source=source)
        signal = predictor.get_latest_signal(symbol, timeframe)
        
        if not signal:
            raise HTTPException(status_code=404, detail="No signal available")
        
        # Record signal
        health_check_instance.record_signal(signal)
        
        # Prepare response data
        response_data = {
            'symbol': signal.get('symbol', symbol),
            'prediction': signal.get('prediction', 'HOLD'),
            'confidence': signal.get('confidence', 0.0),
            'is_actionable': signal.get('is_actionable', False),
            'timestamp': signal.get('timestamp', datetime.utcnow()),
            'individual_predictions': signal.get('individual_predictions'),
            'data_quality': signal.get('data_quality', 0.0),
            'cache_age': 0,
            'source': source  # Add source information
        }
        
        # Cache the response
        prediction_cache.set(symbol, timeframe, response_data)
        logger.debug("Cached new prediction", symbol=symbol, timeframe=timeframe, source=source)
        
        return PredictionResponse(**response_data)
    except Exception as e:
        logger.error(f"Prediction error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/trade", response_model=TradeResponse, tags=["Trading"])
async def execute_trade(request: TradeRequest, background_tasks: BackgroundTasks):
    """
    Execute a trade based on AI signal or manual input.
    
    Args:
        request: Trade request with symbol and optional side/confidence
    
    Returns:
        Trade execution result
    """
    trading_engine = get_trading_engine()
    predictor = get_predictor()
    if not trading_engine or not predictor:
        raise HTTPException(status_code=503, detail="Trading agent not available")
    
    try:
        # Get current price
        delta_client = get_delta_client()
        if not delta_client:
            raise HTTPException(status_code=503, detail="Delta client not available")
        ticker = delta_client.get_ticker(request.symbol)
        if not ticker:
            raise HTTPException(status_code=404, detail="Unable to fetch market data")
        
        current_price = float(ticker.get('close', 0))
        if current_price == 0:
            raise HTTPException(status_code=400, detail="Invalid price data")
        
        # Get signal if not provided
        if not request.side:
            signal = predictor.get_latest_signal(request.symbol, "4h")
            if not signal or not signal.get('is_actionable'):
                return TradeResponse(
                    status="skipped",
                    message="No actionable signal available",
                    data=signal
                )
            
            side = signal.get('prediction', 'HOLD')
            confidence = signal.get('confidence', 0.0)
            atr = signal.get('atr', current_price * 0.02)
        else:
            side = request.side
            confidence = request.confidence or 0.75
            atr = current_price * 0.02  # Default 2% ATR
        
        # Execute trade
        result = trading_engine.execute_signal(
            symbol=request.symbol,
            signal=side,
            confidence=confidence,
            current_price=current_price,
            atr=atr
        )
        
        # Record trade in background
        if result['status'] == 'filled':
            background_tasks.add_task(health_check_instance.record_trade, result)
            background_tasks.add_task(broadcast_to_websockets, {
                'type': 'trade',
                'data': result
            })
        
        return TradeResponse(
            status=result['status'],
            message=f"Trade {result['status']}",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Trade execution error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/portfolio/status", response_model=PortfolioStatus, tags=["Portfolio"])
async def get_portfolio_status():
    """Get current portfolio status."""
    trading_engine = get_trading_engine()
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading agent not available")
    
    try:
        status = trading_engine.get_status()
        portfolio = status['portfolio']
        
        return PortfolioStatus(
            balance=portfolio['balance'],
            equity=portfolio['equity'],
            num_positions=portfolio['num_positions'],
            total_pnl=portfolio['total_pnl'],
            total_pnl_percent=portfolio['total_pnl_pct'],
            daily_pnl=portfolio.get('daily_pnl', 0.0),
            positions=[p.__dict__ if hasattr(p, '__dict__') else p for p in portfolio['positions']]
        )
    except Exception as e:
        logger.error(f"Portfolio status error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/positions", tags=["Portfolio"])
async def get_positions():
    """Get all active positions."""
    trading_engine = get_trading_engine()
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading agent not available")
    
    try:
        positions = trading_engine.portfolio.get_positions()
        return {
            "count": len(positions),
            "positions": [
                {
                    "symbol": p.symbol,
                    "side": p.side,
                    "entry_price": p.entry_price,
                    "size": p.size,
                    "stop_loss": p.stop_loss,
                    "take_profit": p.take_profit,
                    "unrealized_pnl": p.unrealized_pnl,
                    "timestamp": p.timestamp
                }
                for p in positions
            ]
        }
    except Exception as e:
        logger.error(f"Positions error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/test", tags=["Test"])
async def test_endpoint():
    """Test endpoint to verify backend is working with new code."""
    return {"message": "Backend is working with new code", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/v1/analytics/daily", tags=["Analytics"])
async def get_daily_analytics(db = Depends(get_db)):
    """Get daily analytics and risk metrics with preference for equity snapshots."""
    from src.core.database import Trade, EquitySnapshot
    from datetime import timezone
    import math

    def _max_drawdown_from_equity(series):
        peak = series[0]
        mdd = 0.0
        for v in series:
            if v > peak:
                peak = v
            dd = (v - peak) / peak if peak > 0 else 0
            if dd < mdd:
                mdd = dd
        return mdd

    def _log_returns(series):
        out = []
        for i in range(1, len(series)):
            a, b = series[i-1], series[i]
            if a > 0 and b > 0:
                out.append(math.log(b / a))
        return out

    try:
        now_utc = datetime.now(timezone.utc)
        start = now_utc - timedelta(days=30)

        # Prefer equity snapshots
        snaps = (
            db.query(EquitySnapshot)
            .filter(EquitySnapshot.timestamp >= start)
            .order_by(EquitySnapshot.timestamp.asc())
            .all()
        )
        if snaps and len(snaps) >= 10:
            equity = [s.equity for s in snaps if s.equity and s.equity > 0]
            if len(equity) >= 2:
                rets = _log_returns(equity)
                if rets:
                    avg = sum(rets)/len(rets)
                    std = (sum((r-avg)**2 for r in rets)/max(1, len(rets)-1))**0.5 if len(rets)>1 else 0
                    neg = [r for r in rets if r < 0]
                    dstd = (sum(r**2 for r in neg)/max(1, len(neg)))**0.5 if neg else 0
                    sharpe = (avg/std) if std>0 else None
                    sortino = (avg/dstd) if dstd>0 else None
                    mdd = _max_drawdown_from_equity(equity)

                    # win rate (optional) from trades
                    trades = db.query(Trade).filter(Trade.is_closed == True, Trade.closed_at >= start).all()
                    win_rate = (len([t for t in trades if (t.pnl or 0) > 0])/len(trades)) if trades else None

                    trading_engine = get_trading_engine()
                    portfolio_data = trading_engine.get_status()['portfolio'] if trading_engine else {}

                    return {
                        "date": datetime.utcnow().date().isoformat(),
                        "portfolio": portfolio_data,
                        "risk_metrics": {
                            "sharpe_ratio": round(sharpe, 2) if sharpe is not None else None,
                            "sortino_ratio": round(sortino, 2) if sortino is not None else None,
                            "max_drawdown": round(mdd, 4),
                            "win_rate": round(win_rate, 2) if win_rate is not None else None,
                        },
                        "source": "equity_snapshots",
                    }

        # Fallback to closed trades
        trades = db.query(Trade).filter(Trade.is_closed == True, Trade.closed_at >= start).all()
        if trades:
            wins = [t for t in trades if (t.pnl or 0) > 0]
            win_rate = len(wins)/len(trades) if trades else None
            rets = [(t.pnl_percent or 0)/100 for t in trades]
            avg = sum(rets)/len(rets) if rets else 0
            std = (sum((r-avg)**2 for r in rets)/max(1, len(rets)-1))**0.5 if len(rets)>1 else 0
            sharpe = (avg/std) if std>0 else None
            neg = [r for r in rets if r < 0]
            dstd = (sum(r**2 for r in neg)/max(1, len(neg)))**0.5 if neg else 0
            sortino = (avg/dstd) if dstd>0 else None
            cum = 0.0; peak = 0.0; mdd = 0.0
            for r in rets:
                cum += r
                peak = max(peak, cum)
                mdd = min(mdd, cum-peak)

            trading_engine = get_trading_engine()
            portfolio_data = trading_engine.get_status()['portfolio'] if trading_engine else {}

            return {
                "date": datetime.utcnow().date().isoformat(),
                "portfolio": portfolio_data,
                "risk_metrics": {
                    "sharpe_ratio": round(sharpe, 2) if sharpe is not None else None,
                    "sortino_ratio": round(sortino, 2) if sortino is not None else None,
                    "max_drawdown": round(mdd, 4),
                    "win_rate": round(win_rate, 2) if win_rate is not None else None,
                },
                "source": "trades",
            }

        return {
            "date": datetime.utcnow().date().isoformat(),
            "risk_metrics": {
                "sharpe_ratio": None,
                "sortino_ratio": None,
                "max_drawdown": None,
                "win_rate": None,
            },
            "message": "Not enough data yet (collecting equity snapshots).",
            "source": "none",
        }
        
    except Exception as e:
        logger.error(f"Analytics error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/positions/{symbol}/close", tags=["Portfolio"])
async def close_position(symbol: str, background_tasks: BackgroundTasks):
    """Close a specific position."""
    trading_engine = get_trading_engine()
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading agent not available")
    
    try:
        # Get current price
        delta_client = get_delta_client()
        if not delta_client:
            raise HTTPException(status_code=503, detail="Delta client not available")
        ticker = delta_client.get_ticker(symbol)
        if not ticker:
            raise HTTPException(status_code=404, detail="Unable to fetch market data")
        
        current_price = float(ticker.get('close', 0))
        
        result = trading_engine._close_position(symbol, current_price, 'manual')
        
        if result['status'] == 'closed':
            background_tasks.add_task(broadcast_to_websockets, {
                'type': 'position_closed',
                'data': result
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Close position error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class PositionUpdateRequest(BaseModel):
    """Position update request."""
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


@app.put("/api/v1/positions/{symbol}", tags=["Portfolio"])
async def update_position(symbol: str, request: PositionUpdateRequest, background_tasks: BackgroundTasks):
    """Update stop-loss or take-profit for a position."""
    trading_engine = get_trading_engine()
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Trading agent not available")
    
    try:
        position = None
        for p in trading_engine.portfolio.get_positions():
            if p.symbol == symbol:
                position = p
                break
        
        if not position:
            raise HTTPException(status_code=404, detail="Position not found")
        
        if request.stop_loss is not None:
            position.stop_loss = request.stop_loss
        
        if request.take_profit is not None:
            position.take_profit = request.take_profit
        
        background_tasks.add_task(broadcast_to_websockets, {
            'type': 'position_updated',
            'data': {
                'symbol': symbol,
                'stop_loss': position.stop_loss,
                'take_profit': position.take_profit
            }
        })
        
        return {
            'status': 'updated',
            'symbol': symbol,
            'stop_loss': position.stop_loss,
            'take_profit': position.take_profit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update position error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/trades/history", tags=["Trading"])
async def get_trade_history(limit: int = 50, db = Depends(get_db)):
    """Get trade history."""
    try:
        from src.core.database import Trade
        trades = db.query(Trade).order_by(Trade.timestamp.desc()).limit(limit).all()
        
        return {
            'count': len(trades),
            'trades': [
                {
                    'id': t.id,
                    'symbol': t.symbol,
                    'side': t.side,
                    'entry_price': float(t.entry_price) if t.entry_price else None,
                    'exit_price': float(t.exit_price) if t.exit_price else None,
                    'size': float(t.size) if t.size else None,
                    'pnl': float(t.pnl) if t.pnl else None,
                    'pnl_percent': float(t.pnl_percent) if t.pnl_percent else None,
                    'timestamp': t.timestamp,
                    'closed_at': t.closed_at,
                    'close_reason': t.close_reason,
                    'holding_period': t.holding_period,
                    'signal_confidence': float(t.signal_confidence) if t.signal_confidence else None
                }
                for t in trades
            ]
        }
    except Exception as e:
        logger.error(f"Trade history error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class RiskSettingsUpdate(BaseModel):
    """Risk settings update request."""
    max_daily_loss_percent: Optional[float] = None
    max_drawdown_percent: Optional[float] = None
    max_consecutive_losses: Optional[int] = None
    stop_loss_atr_multiplier: Optional[float] = None
    take_profit_risk_reward: Optional[float] = None
    min_confidence: Optional[float] = None


@app.post("/api/v1/settings/risk", tags=["Settings"])
async def update_risk_settings(request: RiskSettingsUpdate):
    """Update risk management settings."""
    try:
        import yaml
        from pathlib import Path
        
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if request.max_daily_loss_percent is not None:
            config['risk_management']['max_daily_loss_percent'] = request.max_daily_loss_percent
        
        if request.max_drawdown_percent is not None:
            config['risk_management']['max_drawdown_percent'] = request.max_drawdown_percent
        
        if request.max_consecutive_losses is not None:
            config['risk_management']['max_consecutive_losses'] = request.max_consecutive_losses
        
        if request.stop_loss_atr_multiplier is not None:
            config['risk_management']['stop_loss_atr_multiplier'] = request.stop_loss_atr_multiplier
        
        if request.take_profit_risk_reward is not None:
            config['risk_management']['take_profit_risk_reward'] = request.take_profit_risk_reward
        
        if request.min_confidence is not None:
            config['signal_filters']['min_confidence'] = request.min_confidence
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        return {
            'status': 'updated',
            'message': 'Risk settings updated successfully. Restart required for changes to take effect.',
            'settings': config
        }
        
    except Exception as e:
        logger.error(f"Update settings error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/settings/risk", tags=["Settings"])
async def get_risk_settings():
    """Get current risk management settings."""
    try:
        return {
            'risk_management': trading_config.risk_management,
            'signal_filters': trading_config.signal_filters,
            'position_sizing': trading_config.position_sizing
        }
    except Exception as e:
        logger.error(f"Get settings error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/market/ticker/{symbol}", tags=["Market Data"])
async def get_ticker(symbol: str):
    """Get current market ticker data."""
    delta_client = get_delta_client()
    if not delta_client:
        raise HTTPException(status_code=503, detail="Market data service unavailable")
    
    try:
        ticker = delta_client.get_ticker(symbol)
        if not ticker:
            raise HTTPException(status_code=404, detail=f"Ticker data not found for {symbol}")
        
        return ticker
    except Exception as e:
        logger.error(f"Ticker error", error=str(e), symbol=symbol, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/market/ohlc/{symbol}", tags=["Market Data"])
async def get_ohlc(symbol: str, resolution: str = "4h", limit: int = 100):
    """Get OHLC candle data."""
    delta_client = get_delta_client()
    if not delta_client:
        raise HTTPException(status_code=503, detail="Delta client not initialized")
    
    try:
        df = delta_client.get_ohlc_candles(symbol, resolution, limit)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Convert to list of dicts
        candles = df.to_dict('records')
        
        return {
            "symbol": symbol,
            "resolution": resolution,
            "count": len(candles),
            "candles": candles
        }
    except Exception as e:
        logger.error(f"OHLC error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NEW ACTIVITY SYSTEM ENDPOINTS
# ============================================================================

@app.get("/api/v1/activities/recent", tags=["Activities"])
async def get_recent_activities(
    limit: int = 10,
    since: Optional[str] = None
):
    """
    Get recent trading activities with real-time data.
    
    Args:
        limit: Maximum number of activities to return (default: 10)
        since: ISO timestamp to filter activities after this time
        
    Returns:
        List of recent activities with UTC timestamps
    """
    try:
        import sys
        import os
        # Add project root to path
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from src.monitoring.activity_manager import activity_manager
        
        # Parse since parameter if provided
        since_dt = None
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid 'since' timestamp format. Use ISO format.")
        
        # Get activities
        activities = activity_manager.get_recent_activities(limit=limit, since=since_dt)
        
        return {
            "activities": activities,
            "total": len(activities),
            "limit": limit,
            "since": since,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Recent activities error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load activities: {str(e)}")


@app.websocket("/api/v1/activities/stream")
async def websocket_activity_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time activity streaming.
    
    Clients can connect to receive live activity updates as they happen.
    Includes automatic reconnection handling and heartbeat.
    """
    await websocket.accept()
    
    try:
        import sys
        import os
        # Add project root to path
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from src.monitoring.activity_manager import activity_manager
        
        # Add connection to activity manager
        activity_manager.add_websocket_connection(websocket)
        
        logger.info("WebSocket activity stream connected")
        
        # Send initial heartbeat
        await websocket.send_json({
            "type": "heartbeat",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Connected to activity stream"
        })
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for client messages (ping/pong)
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                if message == "ping":
                    await websocket.send_text("pong")
                elif message == "heartbeat":
                    await websocket.send_json({
                        "type": "heartbeat",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "message": "Heartbeat received"
                    })
                    
            except asyncio.TimeoutError:
                # Send periodic heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "message": "Periodic heartbeat"
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket activity stream disconnected")
    except Exception as e:
        logger.error(f"WebSocket activity stream error: {e}")
    finally:
        # Remove connection from activity manager
        try:
            activity_manager.remove_websocket_connection(websocket)
        except:
            pass


# ============================================================================
# INTERNAL BROADCAST ENDPOINT
# ============================================================================

@app.post("/api/v1/internal/broadcast", tags=["Internal"])
async def receive_broadcast_from_agent(request: InternalBroadcastRequest):
    """
    Internal endpoint for trading agent to broadcast events to WebSocket clients.
    
    This enables real-time updates when the bot trades autonomously.
    Should only be called by the trading agent process.
    
    Args:
        request: Broadcast request with event type and data
        
    Returns:
        Success status
    """
    try:
        logger.info(
            "Received broadcast from trading agent",
            event_type=request.type,
            has_data=bool(request.data)
        )
        
        # Broadcast to all connected WebSocket clients
        await broadcast_to_websockets({
            'type': request.type,
            'data': request.data
        })
        
        logger.debug(
            "Broadcast sent to WebSocket clients",
            event_type=request.type,
            client_count=len(websocket_clients)
        )
        
        return {
            "status": "success",
            "message": "Event broadcasted",
            "clients_notified": len(websocket_clients)
        }
        
    except Exception as e:
        logger.error("Failed to broadcast event", error=str(e), exc_info=True)
        # Don't fail the request - trading agent should continue
        return {
            "status": "error",
            "message": str(e),
            "clients_notified": 0
        }


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint."""
    return get_metrics_response()


# ============================================================================
# WEBSOCKET FOR REAL-TIME UPDATES
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    
    # Thread-safe client addition
    with websocket_clients_lock:
        websocket_clients.append(websocket)
        total_clients = len(websocket_clients)
    
    logger.info(f"WebSocket client connected", total_clients=total_clients)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Echo back for ping/pong
            if data == "ping":
                await websocket.send_json({"type": "pong", "data": {}})
    
    except WebSocketDisconnect:
        with websocket_clients_lock:
            total_clients = len(websocket_clients)
        logger.info(f"WebSocket client disconnected", total_clients=total_clients)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Thread-safe client removal
        with websocket_clients_lock:
            if websocket in websocket_clients:
                websocket_clients.remove(websocket)
                total_clients = len(websocket_clients)
                logger.info(f"WebSocket client removed", total_clients=total_clients)


async def broadcast_to_websockets(message: Dict):
    """Broadcast message to all connected WebSocket clients."""
    # Get a copy of clients list to avoid modification during iteration
    with websocket_clients_lock:
        clients_copy = websocket_clients.copy()
    
    disconnected = []
    
    for client in clients_copy:
        try:
            await client.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send to WebSocket client", error=str(e))
            disconnected.append(client)
    
    # Remove disconnected clients with thread safety
    if disconnected:
        with websocket_clients_lock:
            for client in disconnected:
                if client in websocket_clients:
                    websocket_clients.remove(client)


# ============================================================================
# NOTE: Trading loop removed - handled by src/main.py bot
# Backend API is data-only, no duplicate trading execution
# ============================================================================


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


