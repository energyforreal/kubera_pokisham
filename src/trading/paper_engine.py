"""Paper trading engine for simulating trades."""

from datetime import datetime, timezone
from typing import Dict, Optional

from sqlalchemy.orm import Session

from src.core.config import trading_config
from src.core.logger import logger, get_component_logger
from src.risk.circuit_breaker import CircuitBreaker
from src.risk.position_sizer import PositionSizer
from src.trading.portfolio import Portfolio
from src.utils.timestamp import get_current_time_utc, format_timestamp


class PaperTradingEngine:
    """Simulate paper trading with realistic execution."""
    
    def __init__(self, db: Session, initial_balance: Optional[float] = None):
        # Initialize component logger
        self.logger = get_component_logger("trading_engine")
        
        self.db = db
        self.portfolio = Portfolio(db, initial_balance)
        self.position_sizer = PositionSizer()
        self.circuit_breaker = CircuitBreaker(db)
        
        # Execution settings
        exec_config = trading_config.execution
        self.transaction_cost = exec_config.get('transaction_cost', 0.001)  # 0.1%
        self.slippage = exec_config.get('slippage', 0.0005)  # 0.05%
        
        self.logger.info("initialization", "Paper trading engine initialized", {
            "initial_balance": initial_balance,
            "transaction_cost": self.transaction_cost,
            "slippage": self.slippage
        })
    
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
        import time
        start_time = time.time()
        
        self.logger.info("signal_execution", f"Executing {signal} signal for {symbol}", {
            "symbol": symbol,
            "signal": signal,
            "confidence": confidence,
            "current_price": current_price,
            "atr": atr,
            "metadata": metadata or {}
        })
        
        # Check if signal is actionable
        if signal == 'HOLD':
            duration_ms = (time.time() - start_time) * 1000
            self.logger.info("signal_execution", "HOLD signal skipped", {
                "symbol": symbol,
                "duration_ms": duration_ms
            })
            return {'status': 'skipped', 'reason': 'HOLD signal'}
        
        # Check circuit breakers
        can_trade, rejection_reason = self.circuit_breaker.validate_trade(
            self.portfolio.balance,
            self.portfolio.initial_balance
        )
        
        if not can_trade:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.warning("signal_execution", "Trade rejected by circuit breaker", {
                "symbol": symbol,
                "signal": signal,
                "reason": rejection_reason,
                "duration_ms": duration_ms
            })
            return {'status': 'rejected', 'reason': rejection_reason}
        
        # Check if we already have a position
        existing_position = self.portfolio.get_position(symbol)
        
        if existing_position:
            # Check if signal suggests closing
            if (existing_position.side == 'buy' and signal == 'SELL') or \
               (existing_position.side == 'sell' and signal == 'BUY'):
                result = self._close_position(symbol, current_price, 'signal')
                duration_ms = (time.time() - start_time) * 1000
                self.logger.info("signal_execution", "Position closed due to signal reversal", {
                    "symbol": symbol,
                    "signal": signal,
                    "existing_side": existing_position.side,
                    "duration_ms": duration_ms
                })
                return result
            else:
                duration_ms = (time.time() - start_time) * 1000
                self.logger.info("signal_execution", "Position already open in same direction", {
                    "symbol": symbol,
                    "signal": signal,
                    "existing_side": existing_position.side,
                    "duration_ms": duration_ms
                })
                return {'status': 'skipped', 'reason': 'Position already open in same direction'}
        
        # Open new position
        if signal == 'BUY':
            result = self._open_position(symbol, 'buy', confidence, current_price, atr, metadata)
            duration_ms = (time.time() - start_time) * 1000
            self.logger.info("signal_execution", "BUY position opened", {
                "symbol": symbol,
                "confidence": confidence,
                "price": current_price,
                "success": result.get('success', False),
                "duration_ms": duration_ms
            })
            return result
        elif signal == 'SELL':
            result = self._open_position(symbol, 'sell', confidence, current_price, atr, metadata)
            duration_ms = (time.time() - start_time) * 1000
            self.logger.info("signal_execution", "SELL position opened", {
                "symbol": symbol,
                "confidence": confidence,
                "price": current_price,
                "success": result.get('success', False),
                "duration_ms": duration_ms
            })
            return result
        
        duration_ms = (time.time() - start_time) * 1000
        self.logger.warning("signal_execution", "Unknown signal type", {
            "symbol": symbol,
            "signal": signal,
            "duration_ms": duration_ms
        })
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
        
        # Check if model-driven exits are enabled
        try:
            if hasattr(trading_config, 'model_driven_exits'):
                model_exits_config = trading_config.model_driven_exits
            else:
                model_exits_config = {}
        except Exception as e:
            logger.warning("Failed to get model exits config", error=str(e))
            model_exits_config = {}
        
        use_model_exits = model_exits_config.get('enabled', False)
        use_fixed_sl_tp = model_exits_config.get('use_fixed_sl_tp', True)
        
        if use_model_exits and not use_fixed_sl_tp:
            # Use emergency-only stops (wide stops as safety net)
            emergency_multiplier = model_exits_config.get('emergency_stop_loss_multiplier', 5.0)
            stop_loss = self._calculate_emergency_stop_loss(executed_price, side, atr, emergency_multiplier)
            take_profit = None  # No fixed TP with model exits
            logger.info(
                "Model-driven exits enabled - using emergency stops only",
                emergency_sl=stop_loss,
                multiplier=emergency_multiplier
            )
        else:
            # Traditional fixed SL/TP
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
        
        timestamp = get_current_time_utc()
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
            'timestamp': timestamp,
            'timestamp_display': format_timestamp(timestamp),
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
        
        # Update circuit breaker
        self.circuit_breaker.update_last_trade_time()
        
        timestamp = get_current_time_utc()
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
            'timestamp': timestamp,
            'timestamp_display': format_timestamp(timestamp),
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
    
    def _calculate_emergency_stop_loss(
        self, 
        entry_price: float, 
        side: str, 
        atr: float,
        multiplier: float
    ) -> float:
        """Calculate wide emergency stop loss (for model-driven exits).
        
        Args:
            entry_price: Entry price
            side: 'buy' or 'sell'
            atr: Average True Range
            multiplier: ATR multiplier for emergency stop
            
        Returns:
            Emergency stop loss price
        """
        stop_distance = atr * multiplier
        
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
