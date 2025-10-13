"""Notification service for sending alerts via Telegram."""

import asyncio
import sys
from datetime import datetime, timezone
from typing import Dict, Optional

# Fix import conflict between local 'telegram' package and python-telegram-bot
_original_path = sys.path.copy()
sys.path = [p for p in sys.path if 'Trading Agent' not in p or 'site-packages' in p]
try:
    from telegram import Bot
    from telegram.error import TelegramError
finally:
    sys.path = _original_path

from src.core.logger import logger


class NotificationService:
    """Send notifications via Telegram."""
    
    def __init__(self, token: str, chat_id: str):
        self.bot = Bot(token=token)
        self.chat_id = chat_id
    
    async def send_message(self, message: str, parse_mode: str = 'Markdown'):
        """Send a message to Telegram.
        
        Args:
            message: Message text
            parse_mode: Parse mode ('Markdown' or 'HTML')
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            logger.debug("Telegram message sent")
        except TelegramError as e:
            logger.error("Failed to send Telegram message", error=str(e))
    
    async def send_trade_notification(self, trade: Dict):
        """Send trade execution notification.
        
        Args:
            trade: Trade execution result dictionary
        """
        status = trade.get('status')
        
        if status == 'filled':
            # New position opened
            side_emoji = "🟢" if trade['side'] == 'buy' else "🔴"
            
            message = f"""
{side_emoji} **TRADE EXECUTED**

**{trade['side'].upper()}** {trade['symbol']}
💰 Entry Price: ${trade['entry_price']:.2f}
📦 Size: {trade['size']:.4f}
💵 Position Value: ${trade['position_value']:.2f}

📍 Stop Loss: ${trade['stop_loss']:.2f}
🎯 Take Profit: ${trade['take_profit']:.2f}

📊 Confidence: {trade.get('confidence', 0):.1%}
💳 Balance: ${trade['balance']:.2f}

⏰ {trade['timestamp'].strftime('%H:%M:%S')}
            """
        
        elif status == 'closed':
            # Position closed
            pnl_emoji = "📈" if trade['pnl'] >= 0 else "📉"
            result_emoji = "✅" if trade['pnl'] >= 0 else "❌"
            
            message = f"""
{result_emoji} **POSITION CLOSED**

{trade['symbol']} - {trade['side'].upper()}
📍 Entry: ${trade['entry_price']:.2f}
📍 Exit: ${trade['exit_price']:.2f}

{pnl_emoji} **PnL: ${trade['pnl']:.2f} ({trade['pnl_percent']:+.2f}%)**

⏱️ Holding Time: {trade.get('holding_period', 0) // 60} minutes
📋 Reason: {trade['close_reason']}
💳 Balance: ${trade['balance']:.2f}

⏰ {trade['timestamp'].strftime('%H:%M:%S')}
            """
        
        elif status == 'rejected':
            message = f"""
⚠️ **TRADE REJECTED**

{trade.get('symbol', 'Unknown')}
Reason: {trade.get('reason', 'Unknown')}

⏰ {datetime.now(timezone.utc).strftime('%H:%M:%S')}
            """
        
        else:
            return  # Don't send notification for other statuses
        
        await self.send_message(message)
    
    async def send_risk_alert(self, alert: Dict):
        """Send risk management alert.
        
        Args:
            alert: Risk alert details
        """
        alert_type = alert.get('type', 'unknown')
        
        if alert_type == 'circuit_breaker':
            message = f"""
🔴 **CIRCUIT BREAKER TRIGGERED**

⚠️ Trading has been halted!

**Reason:** {alert.get('reason', 'Unknown')}

**Details:**
{alert.get('details', 'No additional details')}

Trading will resume automatically after cooldown period or use /resume command.

⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}
            """
        
        elif alert_type == 'drawdown':
            message = f"""
⚠️ **DRAWDOWN ALERT**

Current Drawdown: {alert.get('drawdown_pct', 0):.2f}%
Peak Balance: ${alert.get('peak_balance', 0):.2f}
Current Balance: ${alert.get('current_balance', 0):.2f}

Please review your strategy!

⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}
            """
        
        elif alert_type == 'daily_loss':
            message = f"""
⚠️ **DAILY LOSS LIMIT WARNING**

Daily Loss: {alert.get('loss_pct', 0):.2f}%
Limit: {alert.get('limit_pct', 0):.2f}%

Consider reducing position sizes or pausing trading.

⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}
            """
        
        else:
            message = f"""
⚠️ **RISK ALERT**

{alert.get('message', 'Risk threshold exceeded')}

⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}
            """
        
        await self.send_message(message)
    
    async def send_daily_report(self, report: Dict):
        """Send daily performance report.
        
        Args:
            report: Daily report data
        """
        message = f"""
📊 **DAILY PERFORMANCE REPORT**
📅 {datetime.now(timezone.utc).strftime('%Y-%m-%d')}

**Trading Activity**
• Trades: {report.get('total_trades', 0)}
• Wins: {report.get('winning_trades', 0)} 🟢
• Losses: {report.get('losing_trades', 0)} 🔴
• Win Rate: {report.get('win_rate', 0):.1f}%

**Financial Performance**
• Daily PnL: ${report.get('daily_pnl', 0):.2f} ({report.get('daily_pnl_pct', 0):+.2f}%)
• Total PnL: ${report.get('total_pnl', 0):.2f} ({report.get('total_pnl_pct', 0):+.2f}%)

**Current Status**
• Balance: ${report.get('balance', 0):.2f}
• Equity: ${report.get('equity', 0):.2f}
• Open Positions: {report.get('num_positions', 0)}

**Risk Metrics**
• Max Drawdown: {report.get('max_drawdown', 0):.2f}%
• Sharpe Ratio: {report.get('sharpe_ratio', 0):.2f}

{'🎉 Great day!' if report.get('daily_pnl', 0) > 0 else '💪 Tomorrow is another day!'}
        """
        
        await self.send_message(message)
    
    async def send_startup_message(self):
        """Send bot startup notification."""
        message = """
🚀 **KUBERA POKISHAM STARTED**

AI Trading Agent is now active!

• Paper Trading Mode
• All systems operational
• Risk management active

Use /help to see available commands

Good luck! 📈
        """
        await self.send_message(message)
    
    async def send_shutdown_message(self):
        """Send bot shutdown notification."""
        message = """
🛑 **KUBERA POKISHAM STOPPED**

Trading agent has been shut down.

All positions remain as they were.
No new trades will be executed.

⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}
        """
        await self.send_message(message)

