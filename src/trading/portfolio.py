"""Portfolio management and tracking."""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import Position, Trade, PerformanceMetrics
from src.core.logger import logger


class Portfolio:
    """Manage portfolio state, positions, and performance."""
    
    def __init__(self, db: Session, initial_balance: Optional[float] = None):
        self.db = db
        self.initial_balance = initial_balance or settings.initial_balance
        self.balance = self.initial_balance
        self.equity = self.initial_balance
        self._load_state()
    
    def _load_state(self):
        """Load portfolio state from database."""
        # Get latest performance metrics
        latest_perf = self.db.query(PerformanceMetrics).order_by(
            PerformanceMetrics.date.desc()
        ).first()
        
        if latest_perf:
            self.balance = latest_perf.balance
            self.equity = latest_perf.equity
        
        logger.info(
            "Portfolio state loaded",
            balance=self.balance,
            equity=self.equity
        )
    
    def get_positions(self) -> List[Position]:
        """Get all open positions.
        
        Returns:
            List of Position objects
        """
        positions = self.db.query(Position).all()
        return positions
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a specific symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position object or None
        """
        position = self.db.query(Position).filter(
            Position.symbol == symbol
        ).first()
        return position
    
    def has_position(self, symbol: str) -> bool:
        """Check if position exists for symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            True if position exists
        """
        return self.get_position(symbol) is not None
    
    def add_position(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        size: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Position:
        """Add new position to portfolio.
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            entry_price: Entry price
            size: Position size
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            Created Position object
        """
        position = Position(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            size=size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            entry_timestamp=datetime.now(timezone.utc)
        )
        
        self.db.add(position)
        self.db.commit()
        
        logger.info(
            "Position added",
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            size=size
        )
        
        return position
    
    def update_position(
        self,
        symbol: str,
        current_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ):
        """Update existing position.
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            stop_loss: New stop loss price
            take_profit: New take profit price
        """
        position = self.get_position(symbol)
        
        if not position:
            logger.warning("Position not found for update", symbol=symbol)
            return
        
        # Calculate unrealized PnL
        if position.side == 'buy':
            position.unrealized_pnl = (current_price - position.entry_price) * position.size
        else:  # sell
            position.unrealized_pnl = (position.entry_price - current_price) * position.size
        
        # Update stop loss and take profit if provided
        if stop_loss is not None:
            position.stop_loss = stop_loss
        if take_profit is not None:
            position.take_profit = take_profit
        
        self.db.commit()
    
    def close_position(
        self,
        symbol: str,
        exit_price: float,
        reason: str = 'signal'
    ) -> Optional[Trade]:
        """Close position and create trade record.
        
        Args:
            symbol: Trading symbol
            exit_price: Exit price
            reason: Close reason ('stop_loss', 'take_profit', 'signal', 'manual')
            
        Returns:
            Created Trade object or None
        """
        position = self.get_position(symbol)
        
        if not position:
            logger.warning("Position not found for closing", symbol=symbol)
            return None
        
        # Calculate PnL
        if position.side == 'buy':
            pnl = (exit_price - position.entry_price) * position.size
        else:  # sell
            pnl = (position.entry_price - exit_price) * position.size
        
        pnl_percent = (pnl / (position.entry_price * position.size)) * 100
        
        # Calculate holding period
        holding_period = (datetime.now(timezone.utc) - position.entry_timestamp).total_seconds()
        
        # Create trade record
        trade = Trade(
            timestamp=position.entry_timestamp,
            symbol=symbol,
            side=position.side,
            entry_price=position.entry_price,
            exit_price=exit_price,
            size=position.size,
            stop_loss=position.stop_loss,
            take_profit=position.take_profit,
            pnl=pnl,
            pnl_percent=pnl_percent,
            holding_period=int(holding_period),
            is_closed=True,
            close_reason=reason,
            closed_at=datetime.now(timezone.utc)
        )
        
        self.db.add(trade)
        
        # Update balance
        self.balance += pnl
        
        # Delete position
        self.db.delete(position)
        self.db.commit()
        
        logger.info(
            "Position closed",
            symbol=symbol,
            exit_price=exit_price,
            pnl=pnl,
            pnl_percent=pnl_percent,
            reason=reason
        )
        
        return trade
    
    def update_equity(self, current_prices: Dict[str, float]):
        """Update portfolio equity based on current prices.
        
        Args:
            current_prices: Dict of symbol: price
        """
        positions = self.get_positions()
        
        total_unrealized = 0.0
        
        for position in positions:
            if position.symbol in current_prices:
                current_price = current_prices[position.symbol]
                
                if position.side == 'buy':
                    unrealized = (current_price - position.entry_price) * position.size
                else:
                    unrealized = (position.entry_price - current_price) * position.size
                
                position.unrealized_pnl = unrealized
                total_unrealized += unrealized
        
        self.db.commit()
        
        # Update equity
        self.equity = self.balance + total_unrealized
    
    def get_status(self) -> Dict:
        """Get current portfolio status.
        
        Returns:
            Dict with portfolio metrics
        """
        positions = self.get_positions()
        
        total_unrealized = sum(p.unrealized_pnl for p in positions)
        
        # Get total PnL from closed trades
        closed_trades = self.db.query(Trade).filter(Trade.is_closed == True).all()
        total_realized = sum(t.pnl for t in closed_trades) if closed_trades else 0
        
        # Calculate returns
        total_return = (self.equity - self.initial_balance) / self.initial_balance
        
        status = {
            'balance': self.balance,
            'equity': self.equity,
            'initial_balance': self.initial_balance,
            'total_pnl': total_realized + total_unrealized,
            'total_pnl_pct': total_return * 100,
            'realized_pnl': total_realized,
            'unrealized_pnl': total_unrealized,
            'num_positions': len(positions),
            'num_trades': len(closed_trades),
            'positions': [
                {
                    'symbol': p.symbol,
                    'side': p.side,
                    'entry_price': p.entry_price,
                    'size': p.size,
                    'unrealized_pnl': p.unrealized_pnl,
                    'stop_loss': p.stop_loss,
                    'take_profit': p.take_profit
                }
                for p in positions
            ]
        }
        
        return status
    
    def save_daily_metrics(self):
        """Save daily performance metrics."""
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Check if already saved for today
        existing = self.db.query(PerformanceMetrics).filter(
            PerformanceMetrics.date == today
        ).first()
        
        # Get today's trades
        today_trades = self.db.query(Trade).filter(
            Trade.timestamp >= today,
            Trade.is_closed == True
        ).all()
        
        daily_pnl = sum(t.pnl for t in today_trades) if today_trades else 0
        winning_trades = sum(1 for t in today_trades if t.pnl > 0)
        losing_trades = sum(1 for t in today_trades if t.pnl < 0)
        win_rate = winning_trades / len(today_trades) if today_trades else 0
        
        # Get consecutive losses
        recent_trades = self.db.query(Trade).filter(
            Trade.is_closed == True
        ).order_by(Trade.timestamp.desc()).limit(10).all()
        
        consecutive_losses = 0
        for trade in recent_trades:
            if trade.pnl < 0:
                consecutive_losses += 1
            else:
                break
        
        # Calculate total metrics
        all_trades = self.db.query(Trade).filter(Trade.is_closed == True).all()
        total_pnl = sum(t.pnl for t in all_trades) if all_trades else 0
        total_pnl_pct = (total_pnl / self.initial_balance) * 100
        
        if existing:
            # Update existing
            existing.balance = self.balance
            existing.equity = self.equity
            existing.daily_pnl = daily_pnl
            existing.daily_pnl_percent = (daily_pnl / self.initial_balance) * 100
            existing.total_pnl = total_pnl
            existing.total_pnl_percent = total_pnl_pct
            existing.total_trades = len(today_trades)
            existing.winning_trades = winning_trades
            existing.losing_trades = losing_trades
            existing.win_rate = win_rate
            existing.consecutive_losses = consecutive_losses
        else:
            # Create new
            metrics = PerformanceMetrics(
                date=today,
                balance=self.balance,
                equity=self.equity,
                daily_pnl=daily_pnl,
                daily_pnl_percent=(daily_pnl / self.initial_balance) * 100,
                total_pnl=total_pnl,
                total_pnl_percent=total_pnl_pct,
                total_trades=len(today_trades),
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                consecutive_losses=consecutive_losses
            )
            self.db.add(metrics)
        
        self.db.commit()
        
        logger.info(
            "Daily metrics saved",
            date=today,
            daily_pnl=daily_pnl,
            balance=self.balance
        )

