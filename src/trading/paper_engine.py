"""Paper trading engine for simulating trades."""

from datetime import datetime, timezone
from typing import Dict, Optional

from sqlalchemy.orm import Session

from src.core.config import trading_config
from src.core.logger import logger
from src.risk.circuit_breaker import CircuitBreaker
from src.risk.position_sizer import PositionSizer
from src.trading.portfolio import Portfolio


class PaperTradingEngine:
    """Simulate paper trading with realistic execution."""
    
    def __init__(self, db: Session, initial_balance: Optional[float] = None):
        self.db = db
        self.portfolio = Portfolio(db, initial_balance)
        self.position_sizer = PositionSizer()
        self.circuit_breaker = CircuitBreaker(db)
        
        # Execution settings
        exec_config = trading_config.execution
        self.transaction_cost = exec_config.get('transaction_cost', 0.001)  # 0.1%
        self.slippage = exec_config.get('slippage', 0.0005)  # 0.05%
    
    def execute_signal(
        self,
        symbol: str,
        signal: str,
        confidence: float,
        current_price: float,
        atr: float,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Execute trading signal.
        
        Args:
            symbol: Trading symbol
            signal: 'BUY', 'SELL', or 'HOLD'
            confidence: Signal confidence (0-1)
            current_price: Current market price
            atr: Average True Range for stop loss calculation
            metadata: Additional signal metadata
            
        Returns:
            Execution result dictionary
        """
        # Check if signal is actionable
        if signal == 'HOLD':
            return {'status': 'skipped', 'reason': 'HOLD signal'}
        
        # Check circuit breakers
        can_trade, rejection_reason = self.circuit_breaker.validate_trade(
            self.portfolio.balance,
            self.portfolio.initial_balance
        )
        
        if not can_trade:
            logger.warning("Trade rejected by circuit breaker", reason=rejection_reason)
            return {'status': 'rejected', 'reason': rejection_reason}
        
        # Check if we already have a position
        existing_position = self.portfolio.get_position(symbol)
        
        if existing_position:
            # Check if signal suggests closing
            if (existing_position.side == 'buy' and signal == 'SELL') or \
               (existing_position.side == 'sell' and signal == 'BUY'):
                return self._close_position(symbol, current_price, 'signal')
            else:
                return {'status': 'skipped', 'reason': 'Position already open in same direction'}
        
        # Open new position
        if signal == 'BUY':
            return self._open_position(symbol, 'buy', confidence, current_price, atr, metadata)
        elif signal == 'SELL':
            return self._open_position(symbol, 'sell', confidence, current_price, atr, metadata)
        
        return {'status': 'skipped', 'reason': 'Unknown signal'}
    
    def _open_position(
        self,
        symbol: str,
        side: str,
        confidence: float,
        current_price: float,
        atr: float,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Open a new position.
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            confidence: Signal confidence
            current_price: Current price
            atr: Average True Range
            metadata: Additional metadata
            
        Returns:
            Execution result
        """
        # Calculate position size
        position_size = self.position_sizer.calculate_position_size(
            balance=self.portfolio.balance,
            confidence=confidence,
            volatility=atr / current_price if current_price > 0 else None
        )
        
        # Simulate realistic execution price
        executed_price = self._simulate_execution(current_price, side)
        
        # Calculate stop loss and take profit
        stop_loss = self._calculate_stop_loss(executed_price, side, atr)
        take_profit = self._calculate_take_profit(executed_price, side, stop_loss)
        
        # Calculate costs
        trade_value = position_size
        transaction_cost = trade_value * self.transaction_cost
        
        # Check if we have enough balance
        total_cost = trade_value + transaction_cost
        if total_cost > self.portfolio.balance:
            logger.warning(
                "Insufficient balance",
                balance=self.portfolio.balance,
                required=total_cost
            )
            return {'status': 'rejected', 'reason': 'Insufficient balance'}
        
        # Update balance
        self.portfolio.balance -= total_cost
        
        # Create position
        position = self.portfolio.add_position(
            symbol=symbol,
            side=side,
            entry_price=executed_price,
            size=position_size / executed_price,  # Convert to base currency
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        # Update circuit breaker
        self.circuit_breaker.update_last_trade_time()
        
        result = {
            'status': 'filled',
            'symbol': symbol,
            'side': side,
            'entry_price': executed_price,
            'size': position.size,
            'position_value': position_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'transaction_cost': transaction_cost,
            'confidence': confidence,
            'timestamp': datetime.now(timezone.utc),
            'balance': self.portfolio.balance
        }
        
        logger.info("Position opened", **result)
        
        return result
    
    def _close_position(
        self,
        symbol: str,
        current_price: float,
        reason: str = 'signal'
    ) -> Dict:
        """Close an existing position.
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            reason: Close reason
            
        Returns:
            Execution result
        """
        position = self.portfolio.get_position(symbol)
        
        if not position:
            return {'status': 'failed', 'reason': 'No position to close'}
        
        # Simulate execution price
        executed_price = self._simulate_execution(current_price, 'sell' if position.side == 'buy' else 'buy')
        
        # Close position and create trade record
        trade = self.portfolio.close_position(symbol, executed_price, reason)
        
        if not trade:
            return {'status': 'failed', 'reason': 'Failed to close position'}
        
        # Calculate transaction cost
        trade_value = position.size * executed_price
        transaction_cost = trade_value * self.transaction_cost
        
        # Return proceeds minus costs
        proceeds = trade_value - transaction_cost
        self.portfolio.balance += proceeds
        
        result = {
            'status': 'closed',
            'symbol': symbol,
            'side': position.side,
            'entry_price': position.entry_price,
            'exit_price': executed_price,
            'size': position.size,
            'pnl': trade.pnl,
            'pnl_percent': trade.pnl_percent,
            'holding_period': trade.holding_period,
            'close_reason': reason,
            'transaction_cost': transaction_cost,
            'timestamp': datetime.now(timezone.utc),
            'balance': self.portfolio.balance
        }
        
        logger.info("Position closed", **result)
        
        return result
    
    def _simulate_execution(self, price: float, side: str) -> float:
        """Simulate realistic execution with slippage.
        
        Args:
            price: Current market price
            side: 'buy' or 'sell'
            
        Returns:
            Executed price
        """
        slippage_amount = price * self.slippage
        
        # Buying: pay slippage, Selling: lose slippage
        if side == 'buy':
            return price + slippage_amount
        else:
            return price - slippage_amount
    
    def _calculate_stop_loss(self, entry_price: float, side: str, atr: float) -> float:
        """Calculate stop loss price based on ATR.
        
        Args:
            entry_price: Entry price
            side: 'buy' or 'sell'
            atr: Average True Range
            
        Returns:
            Stop loss price
        """
        atr_multiplier = trading_config.risk_management.get('stop_loss_atr_multiplier', 2.0)
        stop_distance = atr * atr_multiplier
        
        if side == 'buy':
            return entry_price - stop_distance
        else:  # sell
            return entry_price + stop_distance
    
    def _calculate_take_profit(self, entry_price: float, side: str, stop_loss: float) -> float:
        """Calculate take profit based on risk-reward ratio.
        
        Args:
            entry_price: Entry price
            side: 'buy' or 'sell'
            stop_loss: Stop loss price
            
        Returns:
            Take profit price
        """
        risk_reward = trading_config.risk_management.get('take_profit_risk_reward', 2.0)
        risk = abs(entry_price - stop_loss)
        
        if side == 'buy':
            return entry_price + (risk * risk_reward)
        else:  # sell
            return entry_price - (risk * risk_reward)
    
    def check_stop_loss_take_profit(self, symbol: str, current_price: float) -> Optional[Dict]:
        """Check if stop loss or take profit is hit.
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            
        Returns:
            Execution result if position closed, None otherwise
        """
        position = self.portfolio.get_position(symbol)
        
        if not position:
            return None
        
        # Check stop loss
        if position.stop_loss:
            if (position.side == 'buy' and current_price <= position.stop_loss) or \
               (position.side == 'sell' and current_price >= position.stop_loss):
                logger.info("Stop loss hit", symbol=symbol, price=current_price, sl=position.stop_loss)
                return self._close_position(symbol, current_price, 'stop_loss')
        
        # Check take profit
        if position.take_profit:
            if (position.side == 'buy' and current_price >= position.take_profit) or \
               (position.side == 'sell' and current_price <= position.take_profit):
                logger.info("Take profit hit", symbol=symbol, price=current_price, tp=position.take_profit)
                return self._close_position(symbol, current_price, 'take_profit')
        
        return None
    
    def get_status(self) -> Dict:
        """Get trading engine status.
        
        Returns:
            Status dictionary
        """
        portfolio_status = self.portfolio.get_status()
        circuit_status = self.circuit_breaker.check_all_breakers(
            self.portfolio.balance,
            self.portfolio.initial_balance
        )
        
        return {
            'portfolio': portfolio_status,
            'circuit_breaker': circuit_status,
            'is_active': not circuit_status['triggered']
        }
