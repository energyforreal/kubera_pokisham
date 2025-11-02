"""Telegram bot for trading agent control and monitoring."""

import asyncio
import sys
from datetime import datetime
from typing import Optional

# Fix import conflict between local 'telegram' package and python-telegram-bot
# Temporarily remove local path to import the actual telegram package
_original_path = sys.path.copy()
sys.path = [p for p in sys.path if 'Trading Agent' not in p or 'site-packages' in p]
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes
finally:
    sys.path = _original_path

from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import SessionLocal
from src.core.logger import logger, get_component_logger
from src.telegram.handlers import TelegramHandlers
from src.telegram.notifications import NotificationService


class TradingBot:
    """Telegram bot for trading agent."""
    
    def __init__(self, trading_engine=None, predictor=None):
        # Initialize component logger
        self.logger = get_component_logger("telegram_bot")
        
        self.token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.application: Optional[Application] = None
        self.is_running = False
        
        # Services
        self.trading_engine = trading_engine
        self.predictor = predictor
        self.db: Session = SessionLocal()
        
        # Handlers and notifications
        self.handlers = TelegramHandlers(self.db, trading_engine, predictor)
        self.notifications = NotificationService(self.token, self.chat_id)
        
        self.logger.info("initialization", "Telegram bot initialized", {
            "chat_id": self.chat_id,
            "has_trading_engine": trading_engine is not None,
            "has_predictor": predictor is not None
        })
    
    async def initialize(self):
        """Initialize the bot application."""
        self.logger.info("bot_initialization", "Initializing Telegram bot application")
        
        self.application = Application.builder().token(self.token).build()
        
        # Register monitoring command handlers only
        self.application.add_handler(CommandHandler("start", self.handlers.start_command))
        self.application.add_handler(CommandHandler("status", self.handlers.status_command))
        self.application.add_handler(CommandHandler("positions", self.handlers.positions_command))
        self.application.add_handler(CommandHandler("signals", self.handlers.signals_command))
        self.application.add_handler(CommandHandler("daily", self.handlers.daily_report_command))
        self.application.add_handler(CommandHandler("help", self.handlers.help_command))
        
        self.logger.info("bot_initialization", "Telegram bot application initialized successfully")
    
    async def start(self):
        """Start the bot."""
        self.logger.info("bot_start", "Starting Telegram bot")
        
        if not self.application:
            await self.initialize()
        
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        self.is_running = True
        self.logger.info("bot_start", "Telegram bot started successfully")
    
    async def stop(self):
        """Stop the bot with proper error handling."""
        if self.application and self.is_running:
            try:
                logger.info("Stopping Telegram bot...")
                
                if self.application.updater and self.application.updater.running:
                    await self.application.updater.stop()
                    logger.info("Telegram updater stopped")
                
                await self.application.stop()
                logger.info("Telegram application stopped")
                
                await self.application.shutdown()
                logger.info("Telegram application shutdown complete")
                
            except Exception as e:
                logger.error(f"Error stopping Telegram bot: {e}", exc_info=True)
                # Continue with cleanup even if errors occur
            finally:
                self.is_running = False
                self.cleanup()  # Ensure database session is closed
                logger.info("Telegram bot stopped")
    
    
    async def notify_signal(self, signal: dict):
        """Send signal generation notification.
        
        Args:
            signal: Signal data
        """
        await self.notifications.send_signal_notification(signal)
    
    async def notify_trade(self, trade_result: dict):
        """Send trade notification.
        
        Args:
            trade_result: Trade execution result
        """
        await self.notifications.send_trade_notification(trade_result)
    
    async def notify_risk_alert(self, alert: dict):
        """Send risk alert notification.
        
        Args:
            alert: Risk alert details
        """
        await self.notifications.send_risk_alert(alert)
    
    async def send_daily_report(self, report: dict):
        """Send daily performance report.
        
        Args:
            report: Daily report data
        """
        await self.notifications.send_daily_report(report)
    
    def cleanup(self):
        """Cleanup resources."""
        if hasattr(self, 'db') and self.db:
            try:
                self.db.close()
                logger.debug("Telegram bot database session closed")
            except Exception as e:
                logger.warning(f"Error closing Telegram bot database session: {e}")


# Global bot instance
bot_instance: Optional[TradingBot] = None


def get_bot() -> Optional[TradingBot]:
    """Get the global bot instance."""
    return bot_instance


def set_bot(bot: TradingBot):
    """Set the global bot instance."""
    global bot_instance
    bot_instance = bot

