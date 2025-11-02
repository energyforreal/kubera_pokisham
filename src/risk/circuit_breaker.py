"""Circuit breaker system to halt trading under adverse conditions."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from src.core.config import trading_config
from src.core.database import Trade, PerformanceMetrics
from src.core.logger import logger


class CircuitBreaker:
    """Monitor conditions and trigger circuit breakers to stop trading."""
    
    def __init__(self, db: Session):
        self.db = db
        self.config = trading_config.risk_management
        self.is_triggered = False
        self.trigger_reason: Optional[str] = None
        self.trigger_time: Optional[datetime] = None
        self.last_trade_time: Optional[datetime] = None
    
    def check_all_breakers(self, current_balance: float, initial_balance: float) -> Dict:
        """Check all circuit breaker conditions.
        
        Args:
            current_balance: Current account balance
            initial_balance: Initial/starting balance
            
        Returns:
            Dict with breaker status and details
        """
        if self.is_triggered:
            return {
                'triggered': True,
                'reason': self.trigger_reason,
                'trigger_time': self.trigger_time,
                'can_resume': self._can_resume()
            }
        
        # Check each breaker
        breakers = [
            self._check_daily_loss(current_balance, initial_balance),
            self._check_max_drawdown(current_balance, initial_balance),
            self._check_consecutive_losses(),
            self._check_time_between_trades()
        ]
        
        # Find if any breaker is triggered
        triggered_breakers = [b for b in breakers if b['triggered']]
        
        if triggered_breakers:
            self.is_triggered = True
            self.trigger_reason = triggered_breakers[0]['reason']
            self.trigger_time = datetime.now(timezone.utc)
            
            logger.warning(
                "Circuit breaker triggered",
                reason=self.trigger_reason,
                details=triggered_breakers[0]
            )
        
        return {
            'triggered': self.is_triggered,
            'reason': self.trigger_reason,
            'trigger_time': self.trigger_time,
            'breakers': breakers
        }
    
    def _check_daily_loss(self, current_balance: float, initial_balance: float) -> Dict:
        """Check if daily loss limit exceeded.
        
        Args:
            current_balance: Current balance
            initial_balance: Balance at start of day
            
        Returns:
            Dict with breaker status
        """
        max_daily_loss = self.config.get('max_daily_loss_percent', 5) / 100
        
        # Get today's trades
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        today_trades = self.db.query(Trade).filter(
            Trade.timestamp >= today_start,
            Trade.is_closed.is_(True)
        ).all()
        
        daily_pnl = sum(t.pnl for t in today_trades) if today_trades else 0
        daily_loss_pct = daily_pnl / initial_balance if initial_balance > 0 else 0
        
        triggered = daily_loss_pct <= -max_daily_loss
        
        return {
            'name': 'daily_loss',
            'triggered': triggered,
            'reason': f'Daily loss limit exceeded: {daily_loss_pct*100:.2f}% (limit: {max_daily_loss*100}%)',
            'current_loss_pct': daily_loss_pct * 100,
            'limit_pct': max_daily_loss * 100,
            'daily_pnl': daily_pnl
        }
    
    def _check_max_drawdown(self, current_balance: float, initial_balance: float) -> Dict:
        """Check if maximum drawdown exceeded.
        
        Args:
            current_balance: Current balance
            initial_balance: Initial balance
            
        Returns:
            Dict with breaker status
        """
        max_drawdown = self.config.get('max_drawdown_percent', 15) / 100
        
        # Get peak balance
        all_perf = self.db.query(PerformanceMetrics).order_by(
            PerformanceMetrics.balance.desc()
        ).first()
        
        peak_balance = all_perf.balance if all_perf else initial_balance
        
        # Calculate current drawdown
        drawdown = (peak_balance - current_balance) / peak_balance if peak_balance > 0 else 0
        
        triggered = drawdown >= max_drawdown
        
        return {
            'name': 'max_drawdown',
            'triggered': triggered,
            'reason': f'Maximum drawdown exceeded: {drawdown*100:.2f}% (limit: {max_drawdown*100}%)',
            'current_drawdown_pct': drawdown * 100,
            'limit_pct': max_drawdown * 100,
            'peak_balance': peak_balance,
            'current_balance': current_balance
        }
    
    def _check_consecutive_losses(self) -> Dict:
        """Check if consecutive loss limit exceeded.
        
        Returns:
            Dict with breaker status
        """
        max_consecutive = self.config.get('max_consecutive_losses', 5)
        
        # Get recent trades
        recent_trades = self.db.query(Trade).filter(
            Trade.is_closed.is_(True)
        ).order_by(Trade.timestamp.desc()).limit(max_consecutive + 5).all()
        
        # Count consecutive losses
        consecutive_losses = 0
        for trade in recent_trades:
            if trade.pnl < 0:
                consecutive_losses += 1
            else:
                break
        
        triggered = consecutive_losses >= max_consecutive
        
        return {
            'name': 'consecutive_losses',
            'triggered': triggered,
            'reason': f'Consecutive loss limit exceeded: {consecutive_losses} losses (limit: {max_consecutive})',
            'consecutive_losses': consecutive_losses,
            'limit': max_consecutive
        }
    
    def _check_time_between_trades(self) -> Dict:
        """Check if minimum time between trades is respected.
        
        Returns:
            Dict with breaker status
        """
        min_time_seconds = self.config.get('min_time_between_trades', 300)
        
        if self.last_trade_time is None:
            return {
                'name': 'time_between_trades',
                'triggered': False,
                'reason': 'No previous trade',
                'time_since_last': None
            }
        
        time_since_last = (datetime.now(timezone.utc) - self.last_trade_time).total_seconds()
        triggered = time_since_last < min_time_seconds
        
        return {
            'name': 'time_between_trades',
            'triggered': triggered,
            'reason': f'Trading too quickly: {time_since_last:.0f}s since last trade (minimum: {min_time_seconds}s)',
            'time_since_last': time_since_last,
            'minimum_seconds': min_time_seconds
        }
    
    def update_last_trade_time(self, timestamp: Optional[datetime] = None):
        """Update the last trade timestamp.
        
        Args:
            timestamp: Trade timestamp (default: now)
        """
        self.last_trade_time = timestamp or datetime.now(timezone.utc)
    
    def record_trade(self, pnl: float, timestamp: datetime):
        """Record a trade for circuit breaker tracking.
        
        Args:
            pnl: Trade profit/loss
            timestamp: Trade timestamp
        """
        self.update_last_trade_time(timestamp)
        
        # Log trade for tracking
        logger.debug(
            "Trade recorded for circuit breaker",
            pnl=pnl,
            timestamp=timestamp
        )
    
    def reset(self):
        """Reset circuit breaker (manual override)."""
        self.is_triggered = False
        self.trigger_reason = None
        self.trigger_time = None
        
        logger.info("Circuit breaker reset")
    
    def _can_resume(self) -> bool:
        """Check if trading can be resumed after trigger.
        
        Returns:
            True if can resume, False otherwise
        """
        if not self.is_triggered or self.trigger_time is None:
            return True
        
        # Allow resume after 1 hour cooldown
        cooldown_minutes = 60
        time_since_trigger = (datetime.now(timezone.utc) - self.trigger_time).total_seconds() / 60
        
        can_resume = time_since_trigger >= cooldown_minutes
        
        if can_resume:
            logger.info(
                "Circuit breaker cooldown complete, can resume",
                cooldown_minutes=cooldown_minutes,
                time_since_trigger=time_since_trigger
            )
        
        return can_resume
    
    def validate_trade(
        self,
        current_balance: float,
        initial_balance: float
    ) -> Tuple[bool, Optional[str]]:
        """Validate if a trade can be executed.
        
        Args:
            current_balance: Current account balance
            initial_balance: Initial balance
            
        Returns:
            Tuple of (can_trade, rejection_reason)
        """
        status = self.check_all_breakers(current_balance, initial_balance)
        
        if status['triggered']:
            if status.get('can_resume'):
                self.reset()
                return True, None
            else:
                return False, status['reason']
        
        return True, None

