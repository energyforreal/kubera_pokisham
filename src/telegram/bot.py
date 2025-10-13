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
from src.core.logger import logger
from src.telegram.handlers import TelegramHandlers
from src.telegram.notifications import NotificationService


class TradingBot:
    """Telegram bot for trading agent."""
    
    def __init__(self, trading_engine=None, predictor=None):
        self.token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.application: Optional[Application] = None
        self.is_running = False
        self.trading_paused = False
        
        # Services
        self.trading_engine = trading_engine
        self.predictor = predictor
        self.db: Session = SessionLocal()
        
        # Handlers and notifications
        self.handlers = TelegramHandlers(self.db, trading_engine, predictor)
        self.notifications = NotificationService(self.token, self.chat_id)
    
    async def initialize(self):
        """Initialize the bot application."""
        self.application = Application.builder().token(self.token).build()
        
        # Register command handlers
        self.application.add_handler(CommandHandler("start", self.handlers.start_command))
        self.application.add_handler(CommandHandler("status", self.handlers.status_command))
        self.application.add_handler(CommandHandler("positions", self.handlers.positions_command))
        self.application.add_handler(CommandHandler("signals", self.handlers.signals_command))
        self.application.add_handler(CommandHandler("pause", self.handlers.pause_command))
        self.application.add_handler(CommandHandler("resume", self.handlers.resume_command))
        self.application.add_handler(CommandHandler("emergency_stop", self.handlers.emergency_stop_command))
        self.application.add_handler(CommandHandler("daily", self.handlers.daily_report_command))
        self.application.add_handler(CommandHandler("help", self.handlers.help_command))
        
        logger.info("Telegram bot initialized")
    
    async def start(self):
        """Start the bot."""
        if not self.application:
            await self.initialize()
        
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        self.is_running = True
        logger.info("Telegram bot started")
        
        # Send startup message
        await self.notifications.send_message("🚀 Kubera Pokisham trading agent started!")
    
    async def stop(self):
        """Stop the bot."""
        if self.application and self.is_running:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            
            self.is_running = False
            logger.info("Telegram bot stopped")
    
    def pause_trading(self):
        """Pause trading."""
        self.trading_paused = True
        self.handlers.trading_paused = True
        logger.info("Trading paused via Telegram")
    
    def resume_trading(self):
        """Resume trading."""
        self.trading_paused = False
        self.handlers.trading_paused = False
        logger.info("Trading resumed via Telegram")
    
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


# Global bot instance
bot_instance: Optional[TradingBot] = None


def get_bot() -> Optional[TradingBot]:
    """Get the global bot instance."""
    return bot_instance


def set_bot(bot: TradingBot):
    """Set the global bot instance."""
    global bot_instance
    bot_instance = bot

