"""Telegram command handlers."""

import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

# Fix import conflict between local 'telegram' package and python-telegram-bot
_original_path = sys.path.copy()
sys.path = [p for p in sys.path if 'Trading Agent' not in p or 'site-packages' in p]
try:
    from telegram import Update
    from telegram.ext import ContextTypes
finally:
    sys.path = _original_path

from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.logger import logger


class TelegramHandlers:
    """Handle Telegram bot commands."""
    
    def __init__(self, db: Session, trading_engine=None, predictor=None):
        self.db = db
        self.trading_engine = trading_engine
        self.predictor = predictor
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = """
🚀 **Welcome to Kubera Pokisham Trading Agent!**

I'm your AI-powered monitoring assistant for Delta Exchange.

**📊 Monitoring Commands:**
/status - Portfolio status and PnL
/positions - View open positions
/signals - Latest AI trading signals
/daily - Daily performance report
/help - Show this help message

**ℹ️ Note:** This bot is for monitoring only. All trading decisions are made automatically by the AI agent.

Ready to monitor your trading! 📈
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        logger.info("Bot started by user", user_id=update.effective_user.id)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        if not self.trading_engine:
            await update.message.reply_text("❌ Trading engine not initialized")
            return
        
        try:
            status = self.trading_engine.get_status()
            portfolio = status['portfolio']
            
            message = f"""
📊 **Portfolio Status**

💰 **Balance:** ${portfolio['balance']:.2f}
💎 **Equity:** ${portfolio['equity']:.2f}
📈 **Total PnL:** ${portfolio['total_pnl']:.2f} ({portfolio['total_pnl_pct']:.2f}%)

📉 **Realized PnL:** ${portfolio['realized_pnl']:.2f}
📊 **Unrealized PnL:** ${portfolio['unrealized_pnl']:.2f}

📍 **Open Positions:** {portfolio['num_positions']}
📝 **Total Trades:** {portfolio['num_trades']}

⚡ **Circuit Breaker:** {'🔴 TRIGGERED' if status['circuit_breaker']['triggered'] else '🟢 OK'}
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error("Status command failed", error=str(e))
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def positions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /positions command."""
        if not self.trading_engine:
            await update.message.reply_text("❌ Trading engine not initialized")
            return
        
        try:
            status = self.trading_engine.get_status()
            positions = status['portfolio']['positions']
            
            if not positions:
                await update.message.reply_text("📭 No open positions")
                return
            
            message = "📍 **Open Positions**\n\n"
            
            for i, pos in enumerate(positions, 1):
                side_emoji = "🟢" if pos['side'] == 'buy' else "🔴"
                pnl_emoji = "📈" if pos['unrealized_pnl'] >= 0 else "📉"
                
                message += f"""
{side_emoji} **Position {i}: {pos['symbol']}**
• Side: {pos['side'].upper()}
• Entry: ${pos['entry_price']:.2f}
• Size: {pos['size']:.4f}
• Stop Loss: ${pos['stop_loss']:.2f}
• Take Profit: ${pos['take_profit']:.2f}
{pnl_emoji} Unrealized PnL: ${pos['unrealized_pnl']:.2f}

                """
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error("Positions command failed", error=str(e))
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signals command."""
        if not self.predictor:
            await update.message.reply_text("❌ Predictor not initialized")
            return
        
        try:
            symbol = settings.trading_symbol
            signal = self.predictor.get_latest_signal(symbol)
            
            if not signal or 'error' in signal:
                await update.message.reply_text("❌ Failed to get signal")
                return
            
            # Determine emoji based on prediction
            signal_emoji = {
                'BUY': '🟢',
                'SELL': '🔴',
                'HOLD': '⚪'
            }.get(signal['prediction'], '❓')
            
            confidence_bar = '█' * int(signal['confidence'] * 10)
            
            # Check if multi-model
            individual_preds = signal.get('individual_predictions', [])
            strategy = signal.get('strategy', 'single')
            
            if individual_preds:
                # Multi-model signal
                message = f"""
🤖 MULTI-MODEL AI Signal

{signal_emoji} Combined: {signal['prediction']}
📊 Confidence: {signal['confidence']:.1%}
{confidence_bar}

Strategy: {strategy.upper()}
Models Agree: {'✅ Yes' if signal.get('models_agree') else '❌ No'}
Agreement: {signal.get('agreement_level', 0):.0%}

Individual Models:
"""
                for pred in individual_preds:
                    emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '⚪'}.get(pred['signal'], '❓')
                    message += f"  {emoji} {pred['timeframe']}: {pred['signal']} ({pred['confidence']:.1%})\n"
                
                message += f"""
✅ Actionable: {'Yes' if signal.get('is_actionable') else 'No'}
📊 Data Quality: {signal.get('data_quality', 0):.1f}%
⏰ Time: {signal['timestamp'].strftime('%H:%M:%S')}
"""
            else:
                # Single model signal
                message = f"""
🤖 AI Trading Signal

{signal_emoji} Prediction: {signal['prediction']}
📊 Confidence: {signal['confidence']:.1%}
{confidence_bar}

Market Data:
• Symbol: {signal.get('symbol', 'N/A')}
• Price: ${signal.get('current_price', 0):.2f}
• RSI: {signal.get('rsi', 0):.1f}
• MACD: {signal.get('macd', 0):.4f}
• ATR: ${signal.get('atr', 0):.2f}

✅ Actionable: {'Yes' if signal.get('is_actionable') else 'No'}
⏰ Timestamp: {signal['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error("Signals command failed", error=str(e))
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    
    async def daily_report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /daily command."""
        if not self.trading_engine:
            await update.message.reply_text("❌ Trading engine not initialized")
            return
        
        try:
            from src.core.database import Trade, PerformanceMetrics
            
            # Get today's trades
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            today_trades = self.db.query(Trade).filter(
                Trade.timestamp >= today_start,
                Trade.is_closed.is_(True)
            ).all()
            
            # Calculate metrics
            total_trades = len(today_trades)
            winning_trades = sum(1 for t in today_trades if t.pnl > 0)
            losing_trades = sum(1 for t in today_trades if t.pnl < 0)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            daily_pnl = sum(t.pnl for t in today_trades)
            
            # Get current status
            status = self.trading_engine.get_status()
            portfolio = status['portfolio']
            
            message = f"""
📊 **Daily Performance Report**
📅 {datetime.now(timezone.utc).strftime('%Y-%m-%d')}

**Trading Summary**
• Total Trades: {total_trades}
• Winning: {winning_trades} 🟢
• Losing: {losing_trades} 🔴
• Win Rate: {win_rate:.1f}%

**Financial Performance**
• Daily PnL: ${daily_pnl:.2f}
• Current Balance: ${portfolio['balance']:.2f}
• Current Equity: ${portfolio['equity']:.2f}
• Total PnL: ${portfolio['total_pnl']:.2f} ({portfolio['total_pnl_pct']:.2f}%)

**Position Status**
• Open Positions: {portfolio['num_positions']}
• Unrealized PnL: ${portfolio['unrealized_pnl']:.2f}

📈 Keep up the good work!
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error("Daily report failed", error=str(e))
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = """📚 Kubera Pokisham - Monitoring Commands

📊 **Available Commands:**
/status - Portfolio status and PnL
/positions - View open positions details
/signals - Latest AI trading signals
/daily - Daily performance report
/help - This help message

ℹ️ **Note:** This bot is for monitoring only. All trading decisions are made automatically by the AI agent.

💡 **Tips:**
• Check /signals to see AI predictions
• Review /daily report regularly
• Monitor /positions for active trades
• Use /status for quick overview

📈 Happy monitoring!"""
        
        try:
            await update.message.reply_text(help_message)
        except Exception as e:
            # Fallback without special formatting if parse error occurs
            logger.error("Help command formatting error", error=str(e))
            simple_message = (
                "Kubera Pokisham Commands:\n\n"
                "Monitoring: /status /positions /signals /daily\n"
                "Control: /pause /resume /emergency_stop\n"
                "Info: /start /help"
            )
            await update.message.reply_text(simple_message)

