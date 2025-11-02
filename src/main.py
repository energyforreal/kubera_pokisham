"""Main trading loop for Kubera Pokisham AI Trading Agent."""
# pylint: disable=import-error

import asyncio
import signal
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

# Import aiohttp with fallback handling
try:
    import aiohttp  # type: ignore[import]  # noqa: F401
except ImportError:
    aiohttp = None  # type: ignore

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import settings, trading_config
from src.core.database import SessionLocal, init_db
from src.core.logger import logger, get_component_logger, cleanup_logs_on_startup
from src.data.delta_client import DeltaExchangeClient
from src.data.data_sync import DataSyncService
from src.data.multi_timeframe_sync import MultiTimeframeDataSync
from src.ml.predictor import TradingPredictor
from src.ml.multi_model_predictor import MultiModelPredictor
from src.ml.model_coordinator import ModelCoordinator
from src.ml.cross_timeframe_aggregator import CrossTimeframeAggregator
from src.trading.paper_engine import PaperTradingEngine
from src.trading.model_position_manager import ModelPositionManager
from src.trading.intelligent_entry import IntelligentEntry
from src.telegram.bot import TradingBot, set_bot
from src.monitoring.health_check import get_health_check
from src.monitoring.diagnostic_reporter import get_diagnostic_reporter
from src.monitoring.activity_manager import activity_manager
from src.utils.timestamp import get_current_time_utc, format_timestamp, get_time_display
from src.shared_state import shared_state


# ============================================================================
# HELPER FUNCTIONS FOR REAL-TIME COMMUNICATION
# ============================================================================

async def notify_backend_api(event_type: str, data: dict, backend_url: str = "http://localhost:8000"):
    """
    Notify backend API of events for real-time WebSocket broadcasts.
    
    This enables the frontend to receive instant updates when the bot
    trades autonomously, without waiting for polling.
    
    Args:
        event_type: Type of event ('trade', 'signal', 'position_update', etc.)
        data: Event data to broadcast
        backend_url: Backend API URL (default: http://localhost:8000)
    """
    if aiohttp is None:
        logger.warning("aiohttp not available - skipping backend notification")
        return
        
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{backend_url}/api/v1/internal/broadcast",
                json={
                    'type': event_type,
                    'data': data
                },
                timeout=aiohttp.ClientTimeout(total=2)
            ) as response:
                if response.status == 200:
                    logger.debug(
                        "Backend notified successfully",
                        event_type=event_type,
                        status=response.status
                    )
                else:
                    logger.warning(
                        "Backend notification failed",
                        event_type=event_type,
                        status=response.status
                    )
    except asyncio.TimeoutError:
        logger.debug("Backend notification timeout (non-critical)", event_type=event_type)
    except aiohttp.ClientConnectionError:
        logger.debug("Backend API not reachable (non-critical)", event_type=event_type)
    except Exception as e:
        logger.debug("Failed to notify backend (non-critical)", event_type=event_type, error=str(e))
    # Never raise exceptions - notification failures should not stop trading


class TradingAgent:
    """Main trading agent orchestrator."""
    
    # PHASE 4.1: Constants
    ALERT_THROTTLE_SECONDS = 3600  # 1 hour
    ERROR_RETRY_DELAY_SECONDS = 60
    STALE_DATA_WARNING_SECONDS = 300  # 5 minutes
    STALE_DATA_ALERT_SECONDS = 600  # 10 minutes
    MAX_HOLDING_HOURS = 168  # 1 week
    SIGNAL_CONFIDENCE_HISTORY_SIZE = 20
    MIN_CONFIDENCE_SAMPLES = 10
    CONFIDENCE_DEGRADATION_THRESHOLD = 0.55
    HIGH_VOLATILITY_THRESHOLD = 5.0  # percent
    HIGH_VOLATILITY_MIN_CONFIDENCE = 0.70
    MAX_POSITION_PCT = 0.10  # 10% of balance per trade
    
    def __init__(self):
        # Initialize component logger
        self.logger = get_component_logger("trading_agent")
        
        self.is_running = False
        self.delta_client = DeltaExchangeClient()
        self.data_sync = DataSyncService()
        self.multi_tf_sync = MultiTimeframeDataSync()
        self.db = None  # Initialize as None, will be created in initialize()
        self.health_check = get_health_check()
        self.diagnostic_reporter = get_diagnostic_reporter()
        
        self.logger.info("initialization", "Trading agent instance created")
        
        # Initialize intelligent multi-model components
        # Check if multi-model is enabled
        multi_model_config = trading_config.model.get('multi_model', {})
        multi_model_enabled = multi_model_config.get('enabled', False)
        strategy = multi_model_config.get('strategy', 'confirmation')
        
        # Check if using new cross-timeframe strategy
        use_intelligent_system = strategy == 'cross_timeframe_weighted'
        
        if use_intelligent_system:
            self.logger.info("ml_system_init", "Initializing intelligent multi-timeframe system")
            
            # New intelligent system
            self.model_coordinator = ModelCoordinator()
            self.signal_aggregator = CrossTimeframeAggregator()
            self.position_manager = ModelPositionManager()
            self.entry_engine = IntelligentEntry()
            
            # Validate models loaded
            models_count = len(self.model_coordinator.all_models)
            if models_count == 0:
                error_msg = "CRITICAL: No models loaded in ModelCoordinator!"
                self.logger.error("model_loading", error_msg)
                raise RuntimeError("Model loading failed - cannot start trading. Check model files in models/ directory")
            
            self.health_check.update_models_loaded(models_count)
            self.predictor = None  # Not using old predictor
            self.logger.info(
                "ml_system_ready",
                "Intelligent system initialized successfully",
                {
                    "total_models": models_count,
                    "models_15m": len(self.model_coordinator.models_by_timeframe['15m']),
                    "models_1h": len(self.model_coordinator.models_by_timeframe['1h']),
                    "models_4h": len(self.model_coordinator.models_by_timeframe['4h'])
                }
            )
            
        elif multi_model_enabled:
            # Legacy multi-model system
            self.logger.info("ml_system_init", "Using legacy multi-model predictor", {"strategy": strategy})
            self.predictor = MultiModelPredictor(strategy=strategy)
            self.model_coordinator = None
            self.signal_aggregator = None
            self.position_manager = None
            self.entry_engine = None
            
            # Validate models loaded successfully
            models_count = len(self.predictor.models)
            if models_count == 0:
                error_msg = "CRITICAL: No models loaded! Bot cannot make predictions"
                self.logger.error("model_loading", error_msg)
                raise RuntimeError("Model loading failed - cannot start trading. Check model files in models/ directory")
            
            self.health_check.update_models_loaded(models_count)
            self.logger.info("ml_system_ready", "Multi-model predictor initialized", {"strategy": strategy, "models": models_count})
        else:
            # Single model system
            self.logger.info("ml_system_init", "Using single model predictor")
            self.predictor = TradingPredictor()
            self.model_coordinator = None
            self.signal_aggregator = None
            self.position_manager = None
            self.entry_engine = None
            
            # Validate single model loaded
            if not hasattr(self.predictor.model, 'model') or self.predictor.model.model is None:
                error_msg = "CRITICAL: Single model failed to load!"
                self.logger.error("model_loading", error_msg)
                raise RuntimeError("Model loading failed - cannot start trading. Check model file path in config")
            
            self.health_check.update_models_loaded(1)
            self.logger.info("ml_system_ready", "Single model predictor initialized")
        
        self.trading_engine = PaperTradingEngine(self.db, settings.initial_balance)
        self.telegram_bot: Optional[TradingBot] = None
        
        # Initialize risk manager
        from src.risk.risk_manager import RiskManager
        self.risk_manager = RiskManager(self.db)
        
        # Track expected model count for health checks
        if use_intelligent_system:
            self.expected_models_count = models_count
        elif multi_model_enabled:
            self.expected_models_count = models_count
        else:
            self.expected_models_count = 1
        
        # Alert throttling (prevent spam) - using class constant
        self.last_circuit_breaker_alert = None
        self.last_model_health_alert = None
        self.last_data_quality_alert = None
        
        # Daily metrics tracking (PHASE 2.2)
        self.last_daily_save_date = None
        
        # PHASE 3 enhancements
        self.startup_time = None  # Will be set in initialize() (PHASE 3.1)
        self.recent_signal_confidences = []  # PHASE 3.2
        self.total_transaction_costs = 0.0  # PHASE 3.3
        
        # PHASE 6 safety tracking
        self.consecutive_skips = 0  # PHASE 6.2
        
        # Config
        self.symbol = trading_config.trading.get('symbol', 'BTCUSD')
        self.update_interval = trading_config.trading.get('update_interval', 300)  # 5 minutes
        self.position_monitoring_interval = trading_config.trading.get('position_monitoring_interval', 300)  # 5 minutes
        self.timeframe = '15m'  # Primary timeframe for 5-minute signal alignment
        
        self.logger.info(
            "initialization_complete",
            "Trading agent initialization completed",
            {
                "symbol": self.symbol,
                "interval": self.update_interval,
                "initial_balance": settings.initial_balance,
                "expected_models": self.expected_models_count
            }
        )
    
    def _should_send_alert(self, alert_type: str, now: datetime) -> bool:
        """Check if alert should be sent based on throttling (PHASE 4.2)."""
        last_alert_attr = f'last_{alert_type}_alert'
        last_alert = getattr(self, last_alert_attr, None)
        
        if last_alert is None:
            return True
        
        seconds_since_last = (now - last_alert).total_seconds()
        return seconds_since_last > self.ALERT_THROTTLE_SECONDS
    
    def _record_alert_sent(self, alert_type: str, now: datetime):
        """Record that alert was sent (PHASE 4.2)."""
        setattr(self, f'last_{alert_type}_alert', now)
    
    async def _fetch_with_retry(self, fetch_func, max_retries=5, operation_name="fetch"):
        """Fetch data with exponential backoff retry logic."""
        for attempt in range(max_retries):
            try:
                # Check if fetch_func is async or sync
                if asyncio.iscoroutinefunction(fetch_func):
                    return await fetch_func()
                else:
                    # Run sync function in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(None, fetch_func)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == max_retries - 1:
                    logger.error(f"{operation_name} failed after {max_retries} attempts: {e}")
                    return None  # Return None instead of raising
                
                wait_time = min(2 ** attempt, 60)  # Exponential backoff, max 60s
                logger.warning(f"{operation_name} failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
            except Exception as e:
                logger.error(f"{operation_name} unexpected error: {e}")
                if attempt == max_retries - 1:
                    return None
                await asyncio.sleep(2 ** attempt)
        
        return None
    
    async def initialize(self) -> None:
        """Initialize all components."""
        start_time = time.time()
        self.logger.info("system_startup", "Starting trading agent initialization")
        
        # Clean up old logs on startup
        cleanup_stats = cleanup_logs_on_startup()
        self.logger.info("log_cleanup", "Log cleanup completed", {"stats": cleanup_stats})
        
        # PHASE 3.1: Record startup time for uptime tracking
        self.startup_time = get_current_time_utc()
        
        # Initialize database
        init_db()
        self.db = SessionLocal()  # Create database session
        self.logger.info("database_init", "Database initialized")
        
        # Initialize diagnostic reporter
        await self.diagnostic_reporter.initialize()
        self.logger.info("diagnostic_init", "Diagnostic reporter initialized")
        
        # Start data synchronization services
        asyncio.create_task(self.data_sync.start_sync())
        self.logger.info("data_sync_start", "Data synchronization service started")
        
        # Start multi-timeframe sync if using intelligent system
        if self.model_coordinator is not None:
            await self.multi_tf_sync.start()
            self.logger.info("multi_tf_sync_start", "Multi-timeframe sync service started")
        
        # Register components with shared state for API access
        # For intelligent system, use model_coordinator instead of predictor
        predictor_or_coordinator = self.model_coordinator if self.model_coordinator else self.predictor
        
        # Debug logging
        self.logger.info(
            "component_registration",
            "Registering components with shared state",
            {
                "has_model_coordinator": self.model_coordinator is not None,
                "has_predictor": self.predictor is not None,
                "has_trading_engine": self.trading_engine is not None,
                "has_delta_client": self.delta_client is not None,
                "has_risk_manager": self.risk_manager is not None
            }
        )
        
        shared_state.set_trading_agent_components(
            self.trading_engine,
            predictor_or_coordinator,
            self.delta_client,
            self.risk_manager
        )
        self.logger.info("component_registration", "Components registered with shared state")
        
        # Verify registration
        shared_status = shared_state.get_status()
        self.logger.info(
            "shared_state_status",
            "Shared state status after registration",
            {
                "is_trading_agent_running": shared_status['is_trading_agent_running'],
                "has_trading_engine": shared_status['has_trading_engine'],
                "has_predictor": shared_status['has_predictor'],
                "has_delta_client": shared_status['has_delta_client'],
                "has_risk_manager": shared_status['has_risk_manager']
            }
        )
        
        # Initialize Telegram bot (non-critical - trading continues if this fails)
        try:
            # For intelligent system, pass model_coordinator as predictor
            telegram_predictor = self.model_coordinator if self.model_coordinator else self.predictor
            self.telegram_bot = TradingBot(self.trading_engine, telegram_predictor)
            set_bot(self.telegram_bot)
            await self.telegram_bot.initialize()
            await self.telegram_bot.start()
            
            # Send startup notification
            await self.telegram_bot.notifications.send_startup_message()
            
            logger.info("✅ Telegram bot initialized and started")
        except Exception as e:
            logger.warning(f"⚠️ Telegram bot failed to start: {e}")
            logger.warning("Trading will continue WITHOUT Telegram notifications")
            self.telegram_bot = None
            # Don't raise - continue without Telegram
        
        # Log startup activity
        activity_manager.log_activity(
            'system',
            'Trading agent initialized and running',
            {'status': 'startup_complete'},
            'success'
        )
        
        logger.info("All components initialized")
    
    async def intelligent_position_monitor(self) -> None:
        """Monitor positions every 5 minutes using model-driven exits.
        
        This loop runs independently and uses continuous model evaluation
        to determine if positions should be held or exited.
        """
        logger.info("🧠 Intelligent position monitoring started - model-driven exits every 5 minutes")
        
        while self.is_running:
            try:
                # Only run if we have open positions
                positions = self.trading_engine.portfolio.get_positions()
                
                if not positions:
                    # No positions, sleep and continue
                    await asyncio.sleep(self.position_monitoring_interval)  # 5 minutes
                    continue
                
                # Get current time
                now = get_current_time_utc()
                
                # Check each position using model predictions
                for position in positions:
                    try:
                        # Fetch current price
                        ticker = await self._fetch_with_retry(
                            lambda: self.delta_client.get_ticker(position.symbol),
                            operation_name=f"ticker_fetch_{position.symbol}"
                        )
                        
                        if not ticker:
                            logger.warning(f"Could not fetch ticker for {position.symbol}")
                            continue
                        
                        current_price = float(ticker.get('close', 0))
                        
                        if current_price == 0:
                            logger.warning(f"Invalid price for {position.symbol}")
                            continue
                        
                        # Get fresh predictions from all models
                        predictions = self.model_coordinator.get_all_predictions(position.symbol)
                        
                        # Evaluate position using model-driven manager
                        evaluation = self.position_manager.evaluate_position(
                            position=position,
                            predictions=predictions,
                            current_price=current_price
                        )
                        
                        # Take action based on evaluation
                        if evaluation['action'] == 'exit':
                            logger.warning(
                                f"Model-driven EXIT triggered for {position.symbol}",
                                reason=evaluation['reason'],
                                pcs=f"{evaluation['pcs']:.2%}",
                                priority=evaluation['priority']
                            )
                            
                            # Close the position
                            result = self.trading_engine._close_position(
                                position.symbol,
                                current_price,
                                reason=f"model_exit_{evaluation['reason']}"
                            )
                            
                            if result and result['status'] == 'closed':
                                # Notify backend for real-time WebSocket broadcast
                                await notify_backend_api('position_closed', result)
                                
                                # Send Telegram notification
                                if self.telegram_bot:
                                    try:
                                        await self.telegram_bot.notify_trade(result)
                                    except Exception as e:
                                        logger.warning(f"Telegram notification failed: {e}")
                                
                                # Record metrics
                                self.trading_engine.circuit_breaker.record_trade(pnl=result['pnl'], timestamp=now)
                                self.health_check.record_trade(result)
                                await self.diagnostic_reporter.report_trade_execution(result)
                                
                                # Cleanup tracker
                                self.position_manager.cleanup_position(position.symbol)
                        
                        # Update position equity
                        price_map = {position.symbol: current_price}
                        self.trading_engine.portfolio.update_equity(price_map)
                        
                    except Exception as e:
                        logger.error(f"Error monitoring position {position.symbol}: {e}", exc_info=True)
                        continue
                
                # Sleep for 5 minutes before next check
                await asyncio.sleep(self.position_monitoring_interval)
                
            except Exception as e:
                logger.error("Error in intelligent position monitor", error=str(e), exc_info=True)
                # Continue monitoring even on error, but wait before retrying
                await asyncio.sleep(self.position_monitoring_interval)
    
    async def position_monitoring_loop(self) -> None:
        """Monitor positions every 5 minutes for stop-loss/take-profit (LEGACY).
        
        This loop runs independently to ensure timely risk management,
        while the main trading loop handles signal generation every 4 hours.
        
        Note: This is the legacy monitoring loop. Use intelligent_position_monitor for model-driven exits.
        """
        logger.info("Position monitoring loop started - checking SL/TP every 5 minutes")
        
        while self.is_running:
            try:
                # Only run if we have open positions
                positions = self.trading_engine.portfolio.get_positions()
                
                if not positions:
                    # No positions, sleep and continue
                    await asyncio.sleep(self.position_monitoring_interval)  # 5 minutes
                    continue
                
                # Get current time
                now = get_current_time_utc()
                
                # Check each position for SL/TP
                for position in positions:
                    try:
                        # Fetch current price for this position
                        ticker = await self._fetch_with_retry(
                            lambda: self.delta_client.get_ticker(position.symbol),
                            operation_name=f"ticker_fetch_{position.symbol}"
                        )
                        
                        if not ticker:
                            logger.warning(f"Could not fetch ticker for {position.symbol}")
                            continue
                        
                        current_price = float(ticker.get('close', 0))
                        
                        if current_price == 0:
                            logger.warning(f"Invalid price for {position.symbol}")
                            continue
                        
                        # Check position timeout (force close after max holding period)
                        holding_seconds = (now - position.timestamp).total_seconds()
                        holding_hours = holding_seconds / 3600
                        
                        if holding_hours > self.MAX_HOLDING_HOURS:
                            logger.warning(f"Position timeout - force closing {position.symbol} after {holding_hours:.1f}h")
                            result = self.trading_engine._close_position(position.symbol, current_price, reason='timeout')
                            
                            if result and result['status'] == 'closed':
                                # Notify backend for real-time WebSocket broadcast
                                await notify_backend_api('position_closed', result)
                                
                                # Send Telegram notification
                                if self.telegram_bot:
                                    try:
                                        await self.telegram_bot.notify_trade(result)
                                    except Exception as e:
                                        logger.warning(f"Telegram notification failed: {e}")
                                
                                # Record metrics
                                self.trading_engine.circuit_breaker.record_trade(pnl=result['pnl'], timestamp=now)
                                self.health_check.record_trade(result)
                                await self.diagnostic_reporter.report_trade_execution(result)
                            continue  # Position closed, move to next
                        
                        # Check stop-loss and take-profit
                        result = self.trading_engine.check_stop_loss_take_profit(
                            position.symbol,
                            current_price
                        )
                        
                        if result and result['status'] == 'closed':
                            # Notify backend for real-time WebSocket broadcast
                            await notify_backend_api('position_closed', result)
                            
                            # Send Telegram notification
                            if self.telegram_bot:
                                try:
                                    await self.telegram_bot.notify_trade(result)
                                except Exception as e:
                                    logger.warning(f"Telegram notification failed: {e}")
                            
                            # Record for circuit breaker tracking
                            self.trading_engine.circuit_breaker.record_trade(
                                pnl=result['pnl'],
                                timestamp=now
                            )
                            self.health_check.record_trade(result)
                            await self.diagnostic_reporter.report_trade_execution(result)
                            
                            logger.info(
                                f"Position closed via SL/TP monitoring",
                                symbol=position.symbol,
                                reason=result.get('close_reason'),
                                pnl=result.get('pnl')
                            )
                        
                        # Update position equity
                        price_map = {position.symbol: current_price}
                        self.trading_engine.portfolio.update_equity(price_map)
                        
                    except Exception as e:
                        logger.error(f"Error monitoring position {position.symbol}: {e}", exc_info=True)
                        continue
                
                # Sleep for 5 minutes before next check
                await asyncio.sleep(self.position_monitoring_interval)
                
            except Exception as e:
                logger.error("Error in position monitoring loop", error=str(e), exc_info=True)
                # Continue monitoring even on error, but wait before retrying
                await asyncio.sleep(self.position_monitoring_interval)
    
    async def trading_loop(self) -> None:
        """Main trading loop - Signal generation and trade execution.
        
        For intelligent system: Every 5 minutes for entry signals
        For legacy system: Every 5 minutes
        """
        time_info = get_time_display()
        
        # Determine interval based on system type
        if self.model_coordinator is not None:
            # Intelligent system - 5 minute entry signals
            entry_interval = trading_config.trading.get('entry_signal_interval', 300)
            self.logger.info(
                "trading_loop_start",
                "Intelligent trading loop started - entry signals every 5 minutes",
                {
                    "utc_time": time_info['utc'],
                    "local_time": time_info['local'],
                    "interval_seconds": entry_interval
                }
            )
        else:
            # Legacy system - 5 minute signals
            entry_interval = self.update_interval
            self.logger.info(
                "trading_loop_start",
                "Trading loop started - signal generation every 5 minutes",
                {
                    "utc_time": time_info['utc'],
                    "local_time": time_info['local'],
                    "interval_seconds": entry_interval
                }
            )
        
        iteration_count = 0
        while self.is_running:
            try:
                iteration_count += 1
                loop_start_time = time.time()
                
                # Record heartbeat for health monitoring
                self.health_check.heartbeat()
                shared_state.heartbeat()
                
                # Get current time
                now = get_current_time_utc()
                time_display = format_timestamp(now)
                
                # PHASE 3.1: Update uptime tracking
                if self.startup_time:
                    uptime_seconds = (now - self.startup_time).total_seconds()
                    self.health_check.status['uptime_seconds'] = uptime_seconds
                
                # Periodic model health check
                if self.model_coordinator:
                    # Intelligent system - check model coordinator
                    current_model_count = len(self.model_coordinator.all_models)
                elif self.predictor:
                    # Legacy system - check predictor
                    current_model_count = len(self.predictor.models) if hasattr(self.predictor, 'models') else (1 if hasattr(self.predictor, 'model') else 0)
                else:
                    current_model_count = 0
                
                if current_model_count != self.expected_models_count:
                    logger.error(
                        f"MODEL HEALTH CHECK FAILED: Expected {self.expected_models_count} models, found {current_model_count}"
                    )
                    
                    # PHASE 4.2: Use helper methods for throttling
                    if self.telegram_bot and self._should_send_alert('model_health', now):
                        await self.telegram_bot.notify_risk_alert({
                            'type': 'model_health',
                            'message': 'Model health check failed - model count mismatch',
                            'expected_models': self.expected_models_count,
                            'current_models': current_model_count
                        })
                        self._record_alert_sent('model_health', now)
                    
                    # Update health status
                    self.health_check.update_models_loaded(current_model_count)
                    
                    # Critical: If no models loaded, skip this iteration
                    if current_model_count == 0:
                        logger.error("CRITICAL: No models loaded - skipping trading iteration")
                        self.consecutive_skips += 1
                        if self.consecutive_skips >= 3:
                            logger.error(f"Warning: {self.consecutive_skips} consecutive skipped iterations")
                        await asyncio.sleep(self.update_interval)
                        continue
                
                # Check database connection health
                if self.db is None:
                    logger.error("Database connection is None - attempting to reconnect")
                    try:
                        from src.core.database import SessionLocal
                        self.db = SessionLocal()
                        logger.info("Database connection established")
                    except Exception as reconnect_error:
                        logger.error(f"Failed to establish database connection: {reconnect_error}")
                        await asyncio.sleep(self.position_monitoring_interval)
                        continue
                else:
                    try:
                        from sqlalchemy import text  # type: ignore[import]  # noqa: F401
                        self.db.execute(text("SELECT 1"))
                    except Exception as e:
                        logger.warning(f"Database connection issue, reconnecting: {e}")
                        try:
                            self.db.close()
                            from src.core.database import SessionLocal
                            self.db = SessionLocal()
                            logger.info("Database reconnected successfully")
                        except Exception as reconnect_error:
                            logger.error(f"Failed to reconnect database: {reconnect_error}")
                            self.db = None  # Mark as failed
                            await asyncio.sleep(self.position_monitoring_interval)
                            continue
                
                # 1. Get latest market data (PHASE 3.5: with retry logic)
                logger.info(
                    "Fetching market data",
                    symbol=self.symbol,
                    time=time_display
                )
                
                # Note: Removed "Fetching market data" log to reduce noise - this happens every cycle
                try:
                    ticker = await self._fetch_with_retry(
                        lambda: self.delta_client.get_ticker(self.symbol),
                        operation_name="ticker_fetch"
                    )
                except Exception as e:
                    logger.error(f"Failed to fetch ticker data: {e}", exc_info=True)
                    ticker = None
                
                if not ticker:
                    logger.warning("Failed to fetch ticker data")
                    self.consecutive_skips += 1
                    if self.consecutive_skips >= 3:
                        logger.error(f"Warning: {self.consecutive_skips} consecutive skipped iterations")
                    await asyncio.sleep(self.update_interval)
                    continue
                
                current_price = float(ticker.get('close', 0))
                
                if current_price == 0:
                    logger.warning("Invalid price data")
                    self.consecutive_skips += 1
                    if self.consecutive_skips >= 3:
                        logger.error(f"Warning: {self.consecutive_skips} consecutive skipped iterations")
                    await asyncio.sleep(self.update_interval)
                    continue
                
                # Validate data freshness (check if timestamp is recent)
                ticker_timestamp = ticker.get('timestamp')
                if ticker_timestamp:
                    try:
                        if isinstance(ticker_timestamp, str):
                            ticker_time = datetime.fromisoformat(ticker_timestamp.replace('Z', '+00:00'))
                        else:
                            ticker_time = datetime.fromtimestamp(ticker_timestamp / 1000, tz=timezone.utc)
                        
                        data_age_seconds = (now - ticker_time).total_seconds()
                        
                        # Alert if data is older than 5 minutes (300 seconds)
                        if data_age_seconds > 300:
                            logger.warning(
                                f"Stale market data detected",
                                age_seconds=data_age_seconds,
                                ticker_time=ticker_time.isoformat()
                            )
                            
                            # PHASE 4.2: Use helper methods for throttling
                            if self.telegram_bot and data_age_seconds > self.STALE_DATA_ALERT_SECONDS and self._should_send_alert('data_quality', now):
                                await self.telegram_bot.notify_risk_alert({
                                    'type': 'data_quality',
                                    'message': f'Stale market data: {data_age_seconds/60:.1f} minutes old',
                                    'details': f'Last update: {ticker_time.isoformat()}'
                                })
                                self._record_alert_sent('data_quality', now)
                    except Exception as e:
                        logger.warning(f"Could not validate data freshness: {e}")
                
                # 2. Update position unrealized PnL (IMPROVED - Phase 1.2)
                # NOTE: SL/TP and timeout checks moved to separate position_monitoring_loop (runs every 5 min)
                positions = self.trading_engine.portfolio.get_positions()
                price_map = {self.symbol: current_price}
                for position in positions:
                    if position.symbol not in price_map and position.symbol != self.symbol:
                        try:
                            ticker = self.delta_client.get_ticker(position.symbol)
                            if ticker:
                                price_map[position.symbol] = float(ticker.get('close', 0))
                        except Exception as e:
                            logger.warning(f"Could not fetch price for {position.symbol}: {e}")
                self.trading_engine.portfolio.update_equity(price_map)
                # Record equity snapshot for real risk metrics
                if self.db is not None:
                    try:
                        from src.core.database import EquitySnapshot, SessionLocal
                        db_session = SessionLocal()
                        try:
                            db_session.add(EquitySnapshot(
                                equity=self.trading_engine.portfolio.equity,
                                balance=self.trading_engine.portfolio.balance,
                            ))
                            db_session.commit()
                        except Exception as e:
                            logger.warning("Failed to commit equity snapshot", error=str(e))
                            db_session.rollback()
                        finally:
                            db_session.close()
                    except Exception as e:
                        logger.warning("Failed to record equity snapshot", error=str(e))
                
                # 4. Check circuit breaker BEFORE getting signal (prevent unnecessary API calls)
                circuit_status = self.trading_engine.circuit_breaker.check_all_breakers(
                    self.trading_engine.portfolio.balance,
                    self.trading_engine.portfolio.initial_balance
                )
                
                # Update health status (PHASE 1.3 - avoid duplicate check later)
                self.health_check.update_circuit_breaker(circuit_status['triggered'])
                
                if circuit_status['triggered']:
                    logger.warning(
                        "Circuit breaker active - skipping trade execution",
                        reason=circuit_status['reason'],
                        details=circuit_status
                    )
                    
                    # PHASE 4.2: Use helper methods for throttling
                    if self.telegram_bot and self._should_send_alert('circuit_breaker', now):
                        await self.telegram_bot.notify_risk_alert({
                            'type': 'circuit_breaker',
                            'reason': circuit_status['reason'],
                            'details': str(circuit_status)
                        })
                        self._record_alert_sent('circuit_breaker', now)
                    
                    await asyncio.sleep(self.update_interval)
                    continue
                
                # 5. Get AI trading signal
                logger.info(
                    "Getting trading signal",
                    time=time_display
                )
                
                # Note: Removed "Generating AI trading signal" log to reduce noise - only log the actual prediction result
                
                # Use intelligent system if available, otherwise use legacy predictor
                if self.model_coordinator is not None:
                    # Intelligent multi-timeframe system
                    predictions = self.model_coordinator.get_all_predictions(self.symbol)
                    
                    # Get ATR for volatility adjustment
                    atr = 0
                    if '15m' in predictions.get('timeframes', {}):
                        tf_15m = predictions['timeframes']['15m']
                        if tf_15m.get('status') == 'success' and tf_15m.get('models'):
                            # Extract ATR from first model (all should have same market data)
                            atr = current_price * 0.02  # Default 2% if not available
                    
                    # Aggregate signals across timeframes
                    composite_signal = self.signal_aggregator.aggregate_signals(
                        predictions_by_timeframe=predictions,
                        current_price=current_price,
                        atr=atr
                    )
                    
                    # Map to expected signal format
                    signal = {
                        'timestamp': composite_signal['timestamp'],
                        'symbol': self.symbol,
                        'timeframe': 'multi',
                        'prediction': composite_signal['signal'],
                        'confidence': composite_signal['confidence'],
                        'is_actionable': composite_signal['is_actionable'],
                        'atr': atr,
                        'current_price': current_price,
                        
                        # Additional metadata
                        'composite_breakdown': composite_signal,
                        'num_models': composite_signal.get('num_models', 0),
                        'timeframe_alignment': composite_signal.get('timeframe_alignment', {}),
                        'entry_quality': composite_signal.get('entry_quality', {})
                    }
                    
                    # Log prediction result
                    activity_manager.log_activity(
                        'prediction',
                        f"AI prediction: {composite_signal['signal']} signal for {self.symbol} (confidence: {composite_signal['confidence']:.1%})",
                        {
                            'symbol': self.symbol,
                            'prediction': composite_signal['signal'],
                            'confidence': composite_signal['confidence'],
                            'timeframe': 'multi',
                            'num_models': composite_signal.get('num_models', 0)
                        },
                        'success'
                    )
                else:
                    # Legacy predictor
                    signal = self.predictor.get_latest_signal(self.symbol, self.timeframe)
                    
                    # Log prediction result for legacy system
                    if signal:
                        activity_manager.log_activity(
                            'prediction',
                            f"AI prediction: {signal.get('prediction', 'HOLD')} signal for {self.symbol} (confidence: {signal.get('confidence', 0):.1%})",
                            {
                                'symbol': self.symbol,
                                'prediction': signal.get('prediction', 'HOLD'),
                                'confidence': signal.get('confidence', 0),
                                'timeframe': self.timeframe
                            },
                            'success'
                        )
                
                # Validate signal generation
                if not signal:
                    logger.error("Signal generation failed - received None")
                    if self.telegram_bot:
                        await self.telegram_bot.notify_risk_alert({
                            'type': 'prediction_failure',
                            'reason': 'Signal generation returned None',
                            'details': 'Check model files and data availability'
                        })
                    self.consecutive_skips += 1
                    if self.consecutive_skips >= 3:
                        logger.error(f"Warning: {self.consecutive_skips} consecutive skipped iterations")
                    await asyncio.sleep(self.update_interval)
                    continue
                
                # Check for error in signal
                if signal.get('error'):
                    logger.error(f"Signal generation error: {signal.get('error')}")
                    if self.telegram_bot:
                        await self.telegram_bot.notify_risk_alert({
                            'type': 'prediction_failure',
                            'reason': signal.get('error'),
                            'details': f"Symbol: {self.symbol}, Timeframe: {self.timeframe}"
                        })
                    self.consecutive_skips += 1
                    if self.consecutive_skips >= 3:
                        logger.error(f"Warning: {self.consecutive_skips} consecutive skipped iterations")
                    await asyncio.sleep(self.update_interval)
                    continue
                
                # Record signal generation
                self.health_check.record_signal(signal)
                # Report to diagnostic service
                await self.diagnostic_reporter.report_signal_generation(signal)
                # Notify backend for real-time WebSocket broadcast
                await notify_backend_api('signal', signal)
                
                # PHASE 3.2: Track signal confidence trends (using class constants)
                self.recent_signal_confidences.append(signal['confidence'])
                if len(self.recent_signal_confidences) > self.SIGNAL_CONFIDENCE_HISTORY_SIZE:
                    self.recent_signal_confidences.pop(0)
                
                if len(self.recent_signal_confidences) >= self.MIN_CONFIDENCE_SAMPLES:
                    try:
                        avg_confidence = sum(self.recent_signal_confidences) / len(self.recent_signal_confidences)
                        if avg_confidence < self.CONFIDENCE_DEGRADATION_THRESHOLD:
                            logger.warning(f"Model confidence degrading: {avg_confidence:.2%}")
                    except (ZeroDivisionError, TypeError) as e:
                        logger.warning(f"Error calculating average confidence: {e}")
                
                # PHASE 3.4: Adjust confidence threshold based on market volatility (using constants)
                atr = signal.get('atr', 0)
                volatility_pct = (atr / current_price) * 100 if current_price > 0 and atr > 0 else 0
                
                if volatility_pct > self.HIGH_VOLATILITY_THRESHOLD:
                    min_confidence = self.HIGH_VOLATILITY_MIN_CONFIDENCE
                    logger.info(f"High volatility ({volatility_pct:.2f}%) - requiring confidence >= {min_confidence:.0%}")
                else:
                    min_confidence = trading_config.signal_filters.get('min_confidence', 0.60)
                
                # Override is_actionable with dynamic threshold
                signal['is_actionable'] = signal['confidence'] >= min_confidence and signal['prediction'] != 'HOLD'
                
                # Send signal notification to Telegram (for all signals, not just actionable)
                if self.telegram_bot and signal.get('prediction') != 'HOLD':
                    try:
                        await self.telegram_bot.notify_signal(signal)
                    except Exception as e:
                        logger.warning(f"Telegram signal notification failed: {e}")
                
                if not signal.get('is_actionable'):
                    logger.debug("No actionable signal", signal=signal.get('prediction'))
                    self.consecutive_skips += 1
                    await asyncio.sleep(entry_interval)
                    continue
                
                # 6. Execute trade based on signal
                logger.info(
                    "Actionable signal received",
                    prediction=signal['prediction'],
                    confidence=signal['confidence']
                )
                
                # Use intelligent entry engine if available
                if self.entry_engine is not None:
                    # Check if position already exists
                    has_position = self.trading_engine.portfolio.get_position(self.symbol) is not None
                    
                    # Generate entry decision
                    entry_decision = self.entry_engine.generate_entry_signal(
                        composite_signal=signal.get('composite_breakdown', signal),
                        current_price=current_price,
                        atr=signal.get('atr', current_price * 0.02),
                        has_open_position=has_position
                    )
                    
                    if entry_decision['status'] != 'approved':
                        logger.info(
                            "Entry rejected by intelligent entry engine",
                            reason=entry_decision['reason'],
                            details=entry_decision.get('details', '')
                        )
                        self.consecutive_skips += 1
                        await asyncio.sleep(entry_interval)
                        continue
                    
                    # Entry approved - update signal with entry rationale
                    signal['entry_rationale'] = entry_decision.get('entry_rationale', '')
                    logger.info(
                        "✅ Entry APPROVED by intelligent engine",
                        rationale=signal['entry_rationale']
                    )
                
                # PHASE 6.1: Validate position size before execution
                max_position_value = self.trading_engine.portfolio.balance * self.MAX_POSITION_PCT
                expected_size = self.trading_engine.position_sizer.calculate_position_size(
                    signal['confidence'], 
                    self.trading_engine.portfolio.balance, 
                    current_price
                )
                expected_value = current_price * expected_size
                
                if expected_value > max_position_value:
                    logger.error(
                        f"Position size too large: ${expected_value:.2f} > ${max_position_value:.2f} (max {self.MAX_POSITION_PCT:.0%} of balance)"
                    )
                    self.consecutive_skips += 1
                    await asyncio.sleep(self.update_interval)
                    continue
                
                result = self.trading_engine.execute_signal(
                    symbol=self.symbol,
                    signal=signal['prediction'],
                    confidence=signal['confidence'],
                    current_price=current_price,
                    atr=signal.get('atr', current_price * 0.02),  # Default 2% ATR
                    metadata=signal
                )
                
                # Log trade execution activity
                if result['status'] == 'filled':
                    activity_manager.log_activity(
                        'trade',
                        f"Trade executed: {signal['prediction']} {result.get('quantity', 0)} {self.symbol} @ ${result.get('price', 0):,.2f}",
                        {
                            'symbol': self.symbol,
                            'action': signal['prediction'],
                            'quantity': result.get('quantity', 0),
                            'price': result.get('price', 0),
                            'pnl': result.get('pnl', 0),
                            'status': result['status']
                        },
                        'success'
                    )
                elif result['status'] == 'rejected':
                    activity_manager.log_activity(
                        'trade',
                        f"Trade rejected: {result.get('reason', 'Unknown reason')}",
                        {
                            'symbol': self.symbol,
                            'action': signal['prediction'],
                            'reason': result.get('reason', 'Unknown reason'),
                            'status': result['status']
                        },
                        'warning'
                    )
                else:
                    activity_manager.log_activity(
                        'trade',
                        f"Trade status: {result['status']}",
                        {
                            'symbol': self.symbol,
                            'action': signal['prediction'],
                            'status': result['status']
                        },
                        'info'
                    )
                
                # 7. Send notification and record trade
                if result['status'] in ['filled', 'closed', 'rejected']:
                    # Notify backend for real-time WebSocket broadcast
                    await notify_backend_api('trade', result)
                    
                    if self.telegram_bot:
                        try:
                            await self.telegram_bot.notify_trade(result)
                        except Exception as e:
                            logger.warning(f"Telegram trade notification failed: {e}")
                    if result['status'] == 'filled':
                        self.health_check.record_trade(result)
                        # Report to diagnostic service
                        await self.diagnostic_reporter.report_trade_execution(result)
                        
                        # PHASE 3.3: Track cumulative transaction costs
                        if result.get('transaction_cost'):
                            self.total_transaction_costs += result['transaction_cost']
                            self.health_check.status['total_transaction_costs'] = self.total_transaction_costs
                        
                        # PHASE 6.2: Reset consecutive skips after successful trade
                        self.consecutive_skips = 0
                
                # 8. Record trade for circuit breaker tracking
                if result['status'] == 'filled':
                    self.trading_engine.circuit_breaker.record_trade(
                        pnl=0,  # Will be updated when position closes
                        timestamp=get_current_time_utc()
                    )
                
                # PHASE 1.3: Duplicate circuit breaker check removed (already done at line 286-287)
                
                # 8. Save daily metrics (PHASE 2.2 - date-based trigger, not time-based)
                today = now.date()
                if self.last_daily_save_date != today:
                    logger.info("Saving daily metrics")
                    self.trading_engine.portfolio.save_daily_metrics()
                    
                    # Send daily report
                    if self.telegram_bot:
                        try:
                            status = self.trading_engine.get_status()
                            await self.telegram_bot.send_daily_report(status['portfolio'])
                        except Exception as e:
                            logger.warning(f"Daily report failed: {e}")
                    
                    self.last_daily_save_date = today
                
                # 9. Log status (PHASE 5.1: Optimized - direct access instead of get_status())
                logger.info(
                    "Trading iteration complete",
                    balance=self.trading_engine.portfolio.balance,
                    equity=self.trading_engine.portfolio.equity,
                    positions=len(positions),
                    time=time_display
                )
                
                # 10. Sleep until next iteration
                await asyncio.sleep(entry_interval)
                
            except Exception as e:
                logger.error("Error in trading loop", error=str(e), exc_info=True)
                self.health_check.record_error(str(e))
                
                # Log error activity
                activity_manager.log_activity(
                    'error',
                    f"Trading loop error: {str(e)}",
                    {
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'location': 'trading_loop'
                    },
                    'error'
                )
                
                # Report error to diagnostic service
                try:
                    await self.diagnostic_reporter.report_error(str(e), {"location": "trading_loop"})
                except Exception as report_error:
                    logger.warning(f"Failed to report error to diagnostic service: {report_error}")
                
                # Improved error recovery - don't exit on single error
                retry_delay = 300  # 5 minutes to match update interval
                logger.warning(f"Error in trading loop, retrying in {retry_delay} seconds")
                await asyncio.sleep(retry_delay)
                continue  # Continue loop instead of exiting
    
    async def heartbeat_task(self):
        """Send heartbeat every 60 seconds with health monitoring."""
        logger.info("Heartbeat task started (60-second interval)")
        consecutive_failures = 0
        
        while self.is_running:
            try:
                self.health_check.heartbeat()
                shared_state.heartbeat()
                logger.debug("Heartbeat sent")
                consecutive_failures = 0  # Reset on success
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"Heartbeat task error (failure {consecutive_failures}): {e}")
                
                # If too many failures, log critical warning
                if consecutive_failures >= 5:
                    logger.critical(f"Heartbeat failing repeatedly ({consecutive_failures} times) - system may be unstable")
            
            await asyncio.sleep(60)
        
        logger.info("Heartbeat task stopped")

    async def start(self) -> None:
        """Start the trading agent."""
        try:
            # Initialize components
            await self.initialize()
            
            self.is_running = True
            time_info = get_time_display()
            self.logger.info(
                "system_start",
                "Kubera Pokisham Trading Agent started!",
                {
                    "utc_time": time_info['utc'],
                    "local_time": time_info['local'],
                    "session_id": self.logger.get_session_id()
                }
            )
            
            # Start heartbeat task (60-second interval)
            heartbeat_task = asyncio.create_task(self.heartbeat_task())
            self.logger.info("heartbeat_start", "Heartbeat task started (60-second interval)")
            
            # Start appropriate position monitoring loop
            if self.model_coordinator is not None:
                # Intelligent system - model-driven exits every 5 minutes
                monitoring_task = asyncio.create_task(self.intelligent_position_monitor())
                self.logger.info("monitoring_start", "Intelligent position monitoring task started (5-minute interval)")
            else:
                # Legacy system - fixed SL/TP checks every 5 minutes
                monitoring_task = asyncio.create_task(self.position_monitoring_loop())
                self.logger.info("monitoring_start", "Position monitoring task started (5-minute interval)")
            
            # Run main trading loop (4-hour signal generation)
            try:
                await self.trading_loop()
            finally:
                # Ensure tasks are cancelled on shutdown
                self.logger.info("shutdown_start", "Shutting down background tasks...")
                heartbeat_task.cancel()
                monitoring_task.cancel()
                
                # Wait for tasks to complete cleanup with timeout
                try:
                    await asyncio.wait_for(
                        asyncio.gather(heartbeat_task, monitoring_task, return_exceptions=True),
                        timeout=10.0  # 10 second timeout for cleanup
                    )
                    self.logger.info("shutdown_complete", "Background tasks shut down successfully")
                except asyncio.TimeoutError:
                    self.logger.warning("shutdown_timeout", "Timeout waiting for background tasks to shutdown")
                except Exception as e:
                    self.logger.error("shutdown_error", "Error during task cleanup", error=e)
            
        except KeyboardInterrupt:
            self.logger.info("shutdown_signal", "Received shutdown signal")
            await self.stop()
        except Exception as e:
            self.logger.error("fatal_error", "Fatal error in trading agent", error=e)
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the trading agent."""
        self.logger.info("system_stop", "Stopping trading agent...")
        self.is_running = False
        
        # Save final metrics
        self.trading_engine.portfolio.save_daily_metrics()
        
        # Stop data synchronization services
        self.data_sync.stop_sync()
        self.logger.info("data_sync_stop", "Data synchronization service stopped")
        
        if self.multi_tf_sync is not None:
            self.multi_tf_sync.stop()
            self.logger.info("multi_tf_sync_stop", "Multi-timeframe sync service stopped")
        
        # Stop Telegram bot
        if self.telegram_bot:
            await self.telegram_bot.notifications.send_shutdown_message()
            await self.telegram_bot.stop()
            self.telegram_bot.cleanup()
        
        # Close diagnostic reporter
        await self.diagnostic_reporter.close()
        
        # Close database
        if self.db is not None:
            self.db.close()
            self.db = None
        
        self.logger.info("system_stop", "Trading agent stopped")


async def main():
    """Main entry point with proper signal handling."""
    agent = TradingAgent()
    shutdown_event = asyncio.Event()
    
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, initiating graceful shutdown...")
        shutdown_event.set()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize and start agent
        await agent.initialize()
        
        # Start background tasks
        tasks = []
        if hasattr(agent, 'trading_loop'):
            tasks.append(asyncio.create_task(agent.trading_loop()))
        if hasattr(agent, 'position_monitoring_loop'):
            tasks.append(asyncio.create_task(agent.position_monitoring_loop()))
        if hasattr(agent, 'data_sync') and hasattr(agent.data_sync, 'start_sync'):
            tasks.append(asyncio.create_task(agent.data_sync.start_sync()))
        
        # Wait for shutdown signal
        await shutdown_event.wait()
        
        logger.info("Shutdown signal received, stopping tasks...")
        
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down...")
    finally:
        # Cancel all tasks
        for task in tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Stop agent gracefully
        await agent.stop()
        
        logger.info("Trading agent shutdown complete")


if __name__ == "__main__":
    from src.core.singleton import SingletonLock
    
    # Acquire singleton lock to prevent multiple instances
    lock = SingletonLock()
    
    try:
        lock.acquire()
        # Add timeout to prevent hanging
        asyncio.run(asyncio.wait_for(main(), timeout=None))
    except KeyboardInterrupt:
        logger.info("Agent interrupted by user")
    except asyncio.TimeoutError:
        logger.error("Main loop timed out")
    except Exception as e:
        logger.error("Fatal error", error=str(e), exc_info=True)
        sys.exit(1)
    finally:
        lock.release()
        logger.info("Trading agent process ended")

