"""Intelligent Entry Engine - Generates high-quality entry signals using multi-model consensus."""

from typing import Dict, Optional
from datetime import datetime, timedelta

from src.core.config import trading_config
from src.core.logger import logger
from src.utils.timestamp import get_current_time_utc, format_timestamp


class IntelligentEntry:
    """Generates selective, high-quality entry signals from multi-timeframe analysis."""
    
    def __init__(self):
        """Initialize the entry engine."""
        # Configuration
        self.config = trading_config.model.get('multi_model', {})
        self.min_combined_confidence = self.config.get('min_combined_confidence', 0.60)
        
        # Entry tracking
        self.last_entry_attempt = {}  # symbol -> timestamp
        self.min_time_between_entries = 300  # 5 minutes minimum
        
        logger.info("IntelligentEntry engine initialized")
    
    def should_attempt_entry(self, symbol: str) -> bool:
        """Check if enough time has passed since last entry attempt.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            True if entry should be attempted
        """
        if symbol not in self.last_entry_attempt:
            return True
        
        last_attempt = self.last_entry_attempt[symbol]
        time_since = (get_current_time_utc() - last_attempt).total_seconds()
        
        return time_since >= self.min_time_between_entries
    
    def generate_entry_signal(
        self,
        composite_signal: Dict,
        current_price: float,
        atr: float,
        has_open_position: bool = False
    ) -> Dict:
        """Generate entry signal from composite multi-timeframe signal.
        
        Entry Requirements:
        - No existing position in symbol
        - Composite signal is actionable
        - Signal confidence meets threshold
        - Cross-timeframe alignment confirmed
        - Entry quality checks passed
        
        Args:
            composite_signal: Output from CrossTimeframeAggregator
            current_price: Current market price
            atr: Average True Range
            has_open_position: Whether position already exists
            
        Returns:
            Entry decision with signal and metadata
        """
        timestamp = get_current_time_utc()
        symbol = composite_signal.get('symbol', 'UNKNOWN')
        
        # Record attempt
        self.last_entry_attempt[symbol] = timestamp
        
        # Check 1: No existing position
        if has_open_position:
            return self._reject_entry(
                symbol=symbol,
                reason='existing_position',
                details='Position already open in this symbol'
            )
        
        # Check 2: Signal must be actionable
        if not composite_signal.get('is_actionable', False):
            return self._reject_entry(
                symbol=symbol,
                reason='not_actionable',
                details='Composite signal not actionable',
                composite=composite_signal
            )
        
        # Check 3: Must be BUY or SELL
        signal = composite_signal.get('signal', 'HOLD')
        if signal == 'HOLD':
            return self._reject_entry(
                symbol=symbol,
                reason='hold_signal',
                details='Signal is HOLD - no directional bias'
            )
        
        # Check 4: Confidence threshold
        confidence = composite_signal.get('confidence', 0.0)
        if confidence < self.min_combined_confidence:
            return self._reject_entry(
                symbol=symbol,
                reason='low_confidence',
                details=f'Confidence {confidence:.2%} < threshold {self.min_combined_confidence:.2%}'
            )
        
        # Check 5: Timeframe alignment
        alignment = composite_signal.get('timeframe_alignment', {})
        if not alignment.get('is_aligned', False):
            return self._reject_entry(
                symbol=symbol,
                reason='timeframes_not_aligned',
                details=f"Alignment score: {alignment.get('alignment_score', 0):.2%}"
            )
        
        # Check 6: Entry quality requirements
        entry_quality = composite_signal.get('entry_quality', {})
        if not entry_quality.get('meets_requirements', False):
            return self._reject_entry(
                symbol=symbol,
                reason='quality_requirements_not_met',
                details=', '.join(entry_quality.get('rejection_reasons', []))
            )
        
        # All checks passed - generate entry signal
        entry_signal = {
            'status': 'approved',
            'symbol': symbol,
            'signal': signal,
            'confidence': confidence,
            'current_price': current_price,
            'atr': atr,
            
            # Composite breakdown
            'composite_signal': composite_signal,
            
            # Entry metadata
            'entry_quality_score': entry_quality.get('quality_score', 0),
            'timeframe_alignment_score': alignment.get('alignment_score', 0),
            'num_models': composite_signal.get('num_models', 0),
            
            # Timestamp
            'timestamp': timestamp,
            'timestamp_display': format_timestamp(timestamp),
            
            # Reasoning
            'entry_rationale': self._build_entry_rationale(composite_signal)
        }
        
        logger.info(
            f"✅ ENTRY APPROVED: {signal}",
            symbol=symbol,
            confidence=f"{confidence:.2%}",
            quality=f"{entry_quality.get('quality_score', 0):.2%}",
            alignment=f"{alignment.get('alignment_score', 0):.2%}",
            price=current_price
        )
        
        return entry_signal
    
    def _reject_entry(
        self,
        symbol: str,
        reason: str,
        details: str,
        composite: Optional[Dict] = None
    ) -> Dict:
        """Create rejection response."""
        result = {
            'status': 'rejected',
            'symbol': symbol,
            'signal': 'HOLD',
            'reason': reason,
            'details': details,
            'timestamp': get_current_time_utc()
        }
        
        if composite:
            result['composite_signal'] = composite
        
        logger.debug(
            f"Entry rejected for {symbol}",
            reason=reason,
            details=details
        )
        
        return result
    
    def _build_entry_rationale(self, composite_signal: Dict) -> str:
        """Build human-readable entry rationale."""
        signal = composite_signal.get('signal', 'HOLD')
        confidence = composite_signal.get('confidence', 0)
        
        # Get breakdown
        weighted = composite_signal.get('weighted_consensus', {})
        agreement = weighted.get('agreement', 0)
        
        alignment = composite_signal.get('timeframe_alignment', {})
        alignment_score = alignment.get('alignment_score', 0)
        
        entry_quality = composite_signal.get('entry_quality', {})
        quality_score = entry_quality.get('quality_score', 0)
        
        # Build rationale
        rationale_parts = [
            f"{signal} signal with {confidence:.1%} confidence",
            f"{agreement:.0%} model agreement",
            f"{alignment_score:.0%} timeframe alignment",
            f"{quality_score:.0%} entry quality"
        ]
        
        # Add specific strengths
        if entry_quality.get('checks', {}).get('15m_signal_strong'):
            rationale_parts.append("strong 15m entry timing")
        
        if entry_quality.get('checks', {}).get('4h_majority_agrees'):
            rationale_parts.append("4h trend support")
        
        return "; ".join(rationale_parts)
    
    def get_stats(self) -> Dict:
        """Get entry engine statistics."""
        return {
            'total_symbols_tracked': len(self.last_entry_attempt),
            'min_time_between_entries': self.min_time_between_entries,
            'last_attempts': {
                symbol: format_timestamp(ts)
                for symbol, ts in self.last_entry_attempt.items()
            }
        }

