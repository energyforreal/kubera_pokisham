"""Main trading loop for Kubera Pokisham AI Trading Agent."""

import asyncio
import signal
import sys
from pathlib import Path
from datetime import datetime, time as dt_time, timezone
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import settings, trading_config
from src.core.database import SessionLocal, init_db
from src.core.logger import logger
from src.data.delta_client import DeltaExchangeClient
from src.ml.predictor import TradingPredictor
from src.ml.multi_model_predictor import MultiModelPredictor
from src.trading.paper_engine import PaperTradingEngine
from src.telegram.bot import TradingBot, set_bot
from src.monitoring.health_check import get_health_check


class TradingAgent:
    """Main trading agent orchestrator."""
    
    def __init__(self):
        self.is_running = False
        self.delta_client = DeltaExchangeClient()
        self.db = SessionLocal()
        self.health_check = get_health_check()
        
        # Initialize components
        # Check if multi-model is enabled
        multi_model_config = trading_config.model.get('multi_model', {})
        multi_model_enabled = multi_model_config.get('enabled', False)
        
        if multi_model_enabled:
            strategy = multi_model_config.get('strategy', 'confirmation')
            self.predictor = MultiModelPredictor(strategy=strategy)
            self.health_check.update_models_loaded(len(self.predictor.models))
            logger.info(f"Using multi-model predictor", strategy=strategy, models=len(self.predictor.models))
        else:
            self.predictor = TradingPredictor()
            self.health_check.update_models_loaded(1)
            logger.info("Using single model predictor")
        
        self.trading_engine = PaperTradingEngine(self.db, settings.initial_balance)
        self.telegram_bot: Optional[TradingBot] = None
        
        # Config
        self.symbol = trading_config.trading.get('symbol', 'BTCUSDT')
        self.update_interval = trading_config.trading.get('update_interval', 900)  # 15 minutes
        self.timeframe = '15m'  # Primary timeframe
        
        logger.info(
            "Trading agent initialized",
            symbol=self.symbol,
            interval=self.update_interval,
            initial_balance=settings.initial_balance
        )
    
    async def initialize(self):
        """Initialize all components."""
        # Initialize database
        init_db()
        logger.info("Database initialized")
        
        # Initialize Telegram bot
        self.telegram_bot = TradingBot(self.trading_engine, self.predictor)
        set_bot(self.telegram_bot)
        await self.telegram_bot.initialize()
        await self.telegram_bot.start()
        
        logger.info("All components initialized")
    
    async def trading_loop(self):
        """Main trading loop."""
        logger.info("Trading loop started")
        
        while self.is_running:
            try:
                # Record heartbeat for health monitoring
                self.health_check.heartbeat()
                
                # Get current time
                now = datetime.now(timezone.utc)
                
                # Check if trading is paused
                if self.telegram_bot and self.telegram_bot.trading_paused:
                    logger.debug("Trading paused, skipping iteration")
                    await asyncio.sleep(60)  # Check every minute
                    continue
                
                # 1. Get latest market data
                logger.info("Fetching market data", symbol=self.symbol)
                ticker = self.delta_client.get_ticker(self.symbol)
                
                if not ticker:
                    logger.warning("Failed to fetch ticker data")
                    await asyncio.sleep(60)
                    continue
                
                current_price = float(ticker.get('close', 0))
                
                if current_price == 0:
                    logger.warning("Invalid price data")
                    await asyncio.sleep(60)
                    continue
                
                # 2. Check stop loss / take profit for existing positions
                positions = self.trading_engine.portfolio.get_positions()
                for position in positions:
                    result = self.trading_engine.check_stop_loss_take_profit(
                        position.symbol,
                        current_price
                    )
                    if result and self.telegram_bot:
                        await self.telegram_bot.notify_trade(result)
                
                # 3. Update position unrealized PnL
                self.trading_engine.portfolio.update_equity({self.symbol: current_price})
                
                # 4. Check circuit breaker BEFORE getting signal (prevent unnecessary API calls)
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
                    if self.telegram_bot:
                        await self.telegram_bot.notify_risk_alert({
                            'type': 'circuit_breaker',
                            'reason': circuit_status['reason'],
                            'details': str(circuit_status)
                        })
                    await asyncio.sleep(self.update_interval)
                    continue
                
                # 5. Get AI trading signal
                logger.info("Getting trading signal")
                signal = self.predictor.get_latest_signal(self.symbol, self.timeframe)
                
                # Record signal generation
                if signal:
                    self.health_check.record_signal(signal)
                
                if not signal or not signal.get('is_actionable'):
                    logger.debug("No actionable signal", signal=signal.get('prediction') if signal else None)
                    await asyncio.sleep(self.update_interval)
                    continue
                
                # 6. Execute trade based on signal
                logger.info(
                    "Actionable signal received",
                    prediction=signal['prediction'],
                    confidence=signal['confidence']
                )
                
                result = self.trading_engine.execute_signal(
                    symbol=self.symbol,
                    signal=signal['prediction'],
                    confidence=signal['confidence'],
                    current_price=current_price,
                    atr=signal.get('atr', current_price * 0.02),  # Default 2% ATR
                    metadata=signal
                )
                
                # 7. Send notification and record trade
                if result['status'] in ['filled', 'closed', 'rejected']:
                    if self.telegram_bot:
                        await self.telegram_bot.notify_trade(result)
                    if result['status'] == 'filled':
                        self.health_check.record_trade(result)
                
                # 8. Record trade for circuit breaker tracking
                if result['status'] == 'filled':
                    self.trading_engine.circuit_breaker.record_trade(
                        pnl=0,  # Will be updated when position closes
                        timestamp=datetime.now(timezone.utc)
                    )
                
                # Update circuit breaker status in health check
                circuit_check = self.trading_engine.circuit_breaker.check_all_breakers(
                    self.trading_engine.portfolio.balance,
                    self.trading_engine.portfolio.initial_balance
                )
                self.health_check.update_circuit_breaker(circuit_check['triggered'])
                
                # 8. Save daily metrics (once per day at midnight)
                if now.hour == 0 and now.minute < 15:  # Around midnight
                    self.trading_engine.portfolio.save_daily_metrics()
                    
                    # Send daily report
                    if self.telegram_bot:
                        status = self.trading_engine.get_status()
                        await self.telegram_bot.send_daily_report(status['portfolio'])
                
                # 9. Log status
                status = self.trading_engine.get_status()
                logger.info(
                    "Trading iteration complete",
                    balance=status['portfolio']['balance'],
                    equity=status['portfolio']['equity'],
                    positions=status['portfolio']['num_positions']
                )
                
                # 10. Sleep until next iteration
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error("Error in trading loop", error=str(e), exc_info=True)
                self.health_check.record_error(str(e))
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    async def start(self):
        """Start the trading agent."""
        try:
            # Initialize components
            await self.initialize()
            
            self.is_running = True
            logger.info("🚀 Kubera Pokisham Trading Agent started!")
            
            # Run trading loop
            await self.trading_loop()
            
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            await self.stop()
        except Exception as e:
            logger.error("Fatal error in trading agent", error=str(e), exc_info=True)
            await self.stop()
    
    async def stop(self):
        """Stop the trading agent."""
        logger.info("Stopping trading agent...")
        self.is_running = False
        
        # Save final metrics
        self.trading_engine.portfolio.save_daily_metrics()
        
        # Stop Telegram bot
        if self.telegram_bot:
            await self.telegram_bot.notifications.send_shutdown_message()
            await self.telegram_bot.stop()
        
        # Close database
        self.db.close()
        
        logger.info("Trading agent stopped")


async def main():
    """Main entry point."""
    agent = TradingAgent()
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("Received interrupt signal")
        asyncio.create_task(agent.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start agent
    await agent.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Agent interrupted by user")
    except Exception as e:
        logger.error("Fatal error", error=str(e), exc_info=True)
        sys.exit(1)

