"""Position sizing strategies for risk management."""

from typing import Dict, Optional

import numpy as np

from src.core.config import trading_config
from src.core.logger import logger


class PositionSizer:
    """Calculate position sizes based on risk management strategies."""
    
    def __init__(self):
        self.config = trading_config.position_sizing
        self.method = self.config.get('method', 'fixed_fractional')
    
    def calculate_position_size(
        self,
        balance: float,
        risk_per_trade: Optional[float] = None,
        confidence: float = 1.0,
        volatility: Optional[float] = None,
        entry_price: Optional[float] = None,
        stop_loss: Optional[float] = None
    ) -> float:
        """Calculate position size based on configured strategy.
        
        Args:
            balance: Account balance
            risk_per_trade: Risk percentage per trade (overrides config)
            confidence: Signal confidence (0-1)
            volatility: Current market volatility (optional)
            entry_price: Entry price (for stop-loss based sizing)
            stop_loss: Stop loss price (for stop-loss based sizing)
            
        Returns:
            Position size in quote currency
        """
        # Input validation
        if balance <= 0:
            logger.error("Invalid balance", balance=balance)
            return 0.0
        
        # Validate confidence is in range [0, 1]
        if confidence < 0 or confidence > 1:
            logger.warning(
                "Confidence out of bounds, clamping",
                original=confidence,
                clamped=max(0.0, min(1.0, confidence))
            )
            confidence = max(0.0, min(1.0, confidence))
        
        # Validate risk_per_trade if provided
        if risk_per_trade is not None and (risk_per_trade < 0 or risk_per_trade > 0.1):
            logger.warning(
                "Risk per trade out of safe range, clamping to 0.1",
                original=risk_per_trade
            )
            risk_per_trade = max(0.001, min(0.1, risk_per_trade))
        
        if self.method == 'fixed_fractional':
            size = self._fixed_fractional(balance, risk_per_trade, confidence)
        elif self.method == 'kelly_criterion':
            size = self._kelly_criterion(balance, confidence)
        elif self.method == 'volatility_adjusted':
            size = self._volatility_adjusted(balance, risk_per_trade, volatility)
        elif self.method == 'stop_loss_based':
            size = self._stop_loss_based(balance, risk_per_trade, entry_price, stop_loss)
        else:
            logger.warning(f"Unknown sizing method: {self.method}, using fixed_fractional")
            size = self._fixed_fractional(balance, risk_per_trade, confidence)
        
        # Apply limits
        min_size = self.config.get('min_position_size', 100)
        max_size = self.config.get('max_position_size', balance * 0.25)
        
        # Additional safety check - never risk more than 10% in a single trade
        absolute_max = balance * 0.10
        max_size = min(max_size, absolute_max)
        
        original_size = size
        size = max(min_size, min(size, max_size))
        
        if size != original_size:
            logger.warning(
                "Position size clamped to limits",
                original=original_size,
                final=size,
                min=min_size,
                max=max_size
            )
        
        logger.info(
            "Position size calculated",
            method=self.method,
            size=size,
            balance=balance,
            confidence=confidence,
            size_pct_of_balance=f"{(size/balance)*100:.2f}%"
        )
        
        return size
    
    def _fixed_fractional(
        self,
        balance: float,
        risk_per_trade: Optional[float] = None,
        confidence: float = 1.0
    ) -> float:
        """Fixed fractional position sizing.
        
        Args:
            balance: Account balance
            risk_per_trade: Risk percentage (default from config)
            confidence: Scale size by confidence
            
        Returns:
            Position size
        """
        risk_pct = risk_per_trade or self.config.get('risk_per_trade', 0.02)
        
        # Scale by confidence (higher confidence = larger position)
        adjusted_risk = risk_pct * confidence
        
        size = balance * adjusted_risk
        
        return size
    
    def _kelly_criterion(self, balance: float, confidence: float = 1.0) -> float:
        """Kelly Criterion position sizing.
        
        Args:
            balance: Account balance
            confidence: Signal confidence (used as proxy for win rate)
            
        Returns:
            Position size
        """
        # Assume average win/loss based on historical data
        # In practice, these should be calculated from actual trade history
        avg_win = 1.5  # 1.5% average win
        avg_loss = 1.0  # 1% average loss
        win_rate = 0.5 + (confidence - 0.5) * 0.3  # Scale win rate with confidence
        
        # Kelly formula: f = (bp - q) / b
        # b = win/loss ratio, p = win probability, q = loss probability
        b = avg_win / avg_loss
        p = win_rate
        q = 1 - p
        
        kelly_pct = (b * p - q) / b
        
        # Use half-Kelly for safety
        kelly_pct = kelly_pct * 0.5
        
        # Ensure positive and reasonable
        kelly_pct = max(0.01, min(kelly_pct, 0.25))
        
        size = balance * kelly_pct
        
        logger.debug(
            "Kelly criterion",
            kelly_pct=kelly_pct,
            win_rate=win_rate,
            size=size
        )
        
        return size
    
    def _volatility_adjusted(
        self,
        balance: float,
        risk_per_trade: Optional[float] = None,
        volatility: Optional[float] = None
    ) -> float:
        """Volatility-adjusted position sizing.
        
        Args:
            balance: Account balance
            risk_per_trade: Base risk percentage
            volatility: Current volatility (as fraction)
            
        Returns:
            Position size
        """
        base_risk = risk_per_trade or self.config.get('risk_per_trade', 0.02)
        
        if volatility is None:
            # Fallback to fixed fractional
            return self._fixed_fractional(balance, base_risk)
        
        # Assume average volatility of 2%
        avg_volatility = 0.02
        
        # Reduce size in high volatility, increase in low volatility
        volatility_ratio = avg_volatility / max(volatility, 0.001)
        
        # Cap adjustment to 2x
        volatility_ratio = min(volatility_ratio, 2.0)
        
        adjusted_risk = base_risk * volatility_ratio
        size = balance * adjusted_risk
        
        logger.debug(
            "Volatility adjustment",
            volatility=volatility,
            ratio=volatility_ratio,
            size=size
        )
        
        return size
    
    def _stop_loss_based(
        self,
        balance: float,
        risk_per_trade: Optional[float] = None,
        entry_price: Optional[float] = None,
        stop_loss: Optional[float] = None
    ) -> float:
        """Calculate position size based on stop loss distance.
        
        Args:
            balance: Account balance
            risk_per_trade: Risk percentage
            entry_price: Entry price
            stop_loss: Stop loss price
            
        Returns:
            Position size
        """
        if entry_price is None or stop_loss is None:
            # Fallback to fixed fractional
            return self._fixed_fractional(balance, risk_per_trade)
        
        risk_pct = risk_per_trade or self.config.get('risk_per_trade', 0.02)
        
        # Calculate risk amount in quote currency
        risk_amount = balance * risk_pct
        
        # Calculate stop loss distance as percentage
        sl_distance = abs(entry_price - stop_loss) / entry_price
        
        # Position size = risk amount / stop loss distance
        # This ensures we only risk risk_amount if stop loss is hit
        size = risk_amount / sl_distance if sl_distance > 0 else balance * risk_pct
        
        logger.debug(
            "Stop loss based sizing",
            entry=entry_price,
            stop_loss=stop_loss,
            sl_distance_pct=sl_distance * 100,
            size=size
        )
        
        return size

