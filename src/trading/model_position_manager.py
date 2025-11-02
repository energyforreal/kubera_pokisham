"""Model-Driven Position Manager - Replaces fixed SL/TP with continuous model evaluation."""

from typing import Dict, List, Optional
from collections import deque
from datetime import datetime, timezone

from src.core.config import trading_config
from src.core.logger import logger
from src.utils.timestamp import get_current_time_utc, format_timestamp


class PositionConfidenceTracker:
    """Tracks position confidence score over time."""
    
    def __init__(self, max_history: int = 10):
        self.history = deque(maxlen=max_history)
        self.max_history = max_history
    
    def add(self, pcs: float, timestamp: datetime):
        """Add new PCS reading."""
        self.history.append({
            'pcs': pcs,
            'timestamp': timestamp
        })
    
    def get_recent(self, n: int = 3) -> List[float]:
        """Get N most recent PCS values."""
        if len(self.history) < n:
            return [h['pcs'] for h in self.history]
        return [h['pcs'] for h in list(self.history)[-n:]]
    
    def is_declining(self, threshold: int = 3) -> bool:
        """Check if PCS has been declining for N consecutive checks."""
        recent = self.get_recent(threshold)
        if len(recent) < threshold:
            return False
        
        # Check if each value is less than the previous
        for i in range(1, len(recent)):
            if recent[i] >= recent[i-1]:
                return False
        
        return True
    
    def get_trend(self) -> str:
        """Get overall trend: 'improving', 'declining', 'stable'."""
        if len(self.history) < 3:
            return 'unknown'
        
        recent = self.get_recent(3)
        
        # Calculate simple trend
        if recent[-1] > recent[0] + 0.05:
            return 'improving'
        elif recent[-1] < recent[0] - 0.05:
            return 'declining'
        else:
            return 'stable'


class ModelPositionManager:
    """Manages open positions using continuous model evaluation."""
    
    def __init__(self):
        """Initialize the position manager."""
        # Get configuration
        try:
            # Try to get model_driven_exits from trading_config
            if hasattr(trading_config, 'model_driven_exits'):
                self.config = trading_config.model_driven_exits
            elif hasattr(trading_config, '__getitem__'):
                self.config = trading_config.get('model_driven_exits', {})
            else:
                # Fallback to dict-like access
                self.config = getattr(trading_config, '_config', {}).get('model_driven_exits', {})
        except Exception as e:
            logger.warning("Failed to load model exits config", error=str(e))
            # Fallback to default values
            self.config = {}
        
        # Thresholds
        self.min_position_confidence = self.config.get('min_position_confidence', 0.40)
        self.profit_protection_confidence = self.config.get('profit_protection_confidence', 0.55)
        self.high_confidence_threshold = self.config.get('high_confidence_threshold', 0.80)
        
        # Exit triggers
        self.confidence_decline_threshold = self.config.get('confidence_decline_threshold', 3)
        self.reversal_timeframes = self.config.get('reversal_timeframes', ['15m', '1h'])
        
        # Emergency stops
        self.emergency_stop_enabled = self.config.get('emergency_stop_enabled', True)
        self.emergency_stop_multiplier = self.config.get('emergency_stop_loss_multiplier', 5.0)
        
        # Profit extension
        self.min_profit_multiple = self.config.get('min_profit_multiple', 1.5)
        self.trailing_confidence_threshold = self.config.get('trailing_confidence_threshold', 0.75)
        
        # Position tracking
        self.position_trackers: Dict[str, PositionConfidenceTracker] = {}
        
        logger.info(
            "ModelPositionManager initialized",
            min_pcs=self.min_position_confidence,
            profit_protection=self.profit_protection_confidence
        )
    
    def evaluate_position(
        self,
        position: object,
        predictions: Dict,
        current_price: float
    ) -> Dict:
        """Evaluate if position should be held or exited based on model predictions.
        
        Args:
            position: Position object with side, entry_price, size, etc.
            predictions: Output from ModelCoordinator.get_all_predictions()
            current_price: Current market price
            
        Returns:
            Evaluation result with action ('hold' or 'exit') and detailed reasoning
        """
        symbol = position.symbol
        
        # Initialize tracker if needed
        if symbol not in self.position_trackers:
            self.position_trackers[symbol] = PositionConfidenceTracker()
        
        tracker = self.position_trackers[symbol]
        
        # Calculate Position Confidence Score
        pcs = self._calculate_position_confidence_score(position, predictions)
        
        # Record PCS
        timestamp = get_current_time_utc()
        tracker.add(pcs, timestamp)
        
        # Calculate unrealized P&L
        if position.side == 'buy':
            unrealized_pnl = (current_price - position.entry_price) * position.size
        else:  # sell
            unrealized_pnl = (position.entry_price - current_price) * position.size
        
        # Calculate R-multiple (risk-adjusted profit)
        risk = abs(position.entry_price - position.stop_loss) if position.stop_loss else position.entry_price * 0.02
        r_multiple = unrealized_pnl / (risk * position.size) if risk > 0 else 0
        
        is_profitable = unrealized_pnl > 0
        
        # Evaluate exit conditions
        exit_evaluation = self._evaluate_exit_conditions(
            position=position,
            pcs=pcs,
            tracker=tracker,
            predictions=predictions,
            r_multiple=r_multiple,
            is_profitable=is_profitable
        )
        
        # Check emergency stop
        if self.emergency_stop_enabled and position.stop_loss:
            emergency_triggered = self._check_emergency_stop(position, current_price)
            if emergency_triggered:
                exit_evaluation['action'] = 'exit'
                exit_evaluation['reason'] = 'emergency_stop_loss'
                exit_evaluation['priority'] = 'critical'
        
        # Build result
        result = {
            'action': exit_evaluation['action'],
            'reason': exit_evaluation['reason'],
            'priority': exit_evaluation.get('priority', 'normal'),
            
            # Metrics
            'pcs': pcs,
            'pcs_trend': tracker.get_trend(),
            'recent_pcs': tracker.get_recent(3),
            'r_multiple': r_multiple,
            'unrealized_pnl': unrealized_pnl,
            'is_profitable': is_profitable,
            
            # Details
            'exit_evaluation': exit_evaluation,
            'timestamp': timestamp,
            'timestamp_display': format_timestamp(timestamp)
        }
        
        # Log decision
        if result['action'] == 'exit':
            logger.info(
                f"EXIT signal for {symbol}",
                reason=result['reason'],
                pcs=f"{pcs:.2%}",
                r_multiple=f"{r_multiple:.2f}R",
                pnl=f"${unrealized_pnl:.2f}",
                priority=result['priority']
            )
        else:
            logger.debug(
                f"HOLD position {symbol}",
                pcs=f"{pcs:.2%}",
                trend=tracker.get_trend(),
                r_multiple=f"{r_multiple:.2f}R"
            )
        
        return result
    
    def _calculate_position_confidence_score(
        self,
        position: object,
        predictions: Dict
    ) -> float:
        """Calculate Position Confidence Score (PCS).
        
        For LONG positions: High score if models predict BUY/HOLD
        For SHORT positions: High score if models predict SELL/HOLD
        
        Returns:
            PCS value between 0 and 1
        """
        timeframes_data = predictions.get('timeframes', {})
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for timeframe, tf_data in timeframes_data.items():
            if tf_data.get('status') != 'success':
                continue
            
            for model_pred in tf_data.get('models', []):
                signal = model_pred['prediction']
                confidence = model_pred['confidence']
                weight = model_pred['weight']
                
                # Score based on alignment with position direction
                if position.side == 'buy':
                    # Long position: BUY=1.0, HOLD=0.5, SELL=0.0
                    if signal == 'BUY':
                        alignment_score = 1.0
                    elif signal == 'HOLD':
                        alignment_score = 0.5
                    else:  # SELL
                        alignment_score = 0.0
                else:  # short position
                    # Short position: SELL=1.0, HOLD=0.5, BUY=0.0
                    if signal == 'SELL':
                        alignment_score = 1.0
                    elif signal == 'HOLD':
                        alignment_score = 0.5
                    else:  # BUY
                        alignment_score = 0.0
                
                # Combine alignment with confidence
                model_score = alignment_score * confidence
                
                # Weight the score
                total_weighted_score += model_score * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0.5  # Neutral if no predictions
        
        pcs = total_weighted_score / total_weight
        
        return pcs
    
    def _evaluate_exit_conditions(
        self,
        position: object,
        pcs: float,
        tracker: PositionConfidenceTracker,
        predictions: Dict,
        r_multiple: float,
        is_profitable: bool
    ) -> Dict:
        """Evaluate all exit conditions and return decision.
        
        Exit Triggers:
        1. Immediate Exit: PCS < min_position_confidence
        2. Reversal Exit: Key timeframes flip direction
        3. Confidence Erosion: PCS declining for N checks
        4. Profit Protection: PCS < threshold while in profit
        """
        # Check 1: Immediate exit on low confidence
        if pcs < self.min_position_confidence:
            return {
                'action': 'exit',
                'reason': 'low_confidence',
                'details': f'PCS {pcs:.2%} < minimum {self.min_position_confidence:.2%}',
                'priority': 'high'
            }
        
        # Check 2: Reversal exit
        reversal_check = self._check_reversal(position, predictions)
        if reversal_check['is_reversal']:
            return {
                'action': 'exit',
                'reason': 'reversal_detected',
                'details': reversal_check['details'],
                'priority': 'high'
            }
        
        # Check 3: Confidence erosion
        if tracker.is_declining(self.confidence_decline_threshold):
            return {
                'action': 'exit',
                'reason': 'confidence_erosion',
                'details': f'PCS declining for {self.confidence_decline_threshold} consecutive checks',
                'priority': 'medium'
            }
        
        # Check 4: Profit protection
        if is_profitable and r_multiple >= self.min_profit_multiple:
            # In profit - use tighter threshold
            if pcs < self.profit_protection_confidence:
                return {
                    'action': 'exit',
                    'reason': 'profit_protection',
                    'details': f'Locking in {r_multiple:.2f}R profit, PCS {pcs:.2%} < protection threshold',
                    'priority': 'medium'
                }
        
        # No exit conditions met
        hold_reason = 'models_support_position'
        if pcs > self.high_confidence_threshold:
            hold_reason = 'high_confidence_continuation'
        
        return {
            'action': 'hold',
            'reason': hold_reason,
            'details': f'PCS {pcs:.2%}, trend: {tracker.get_trend()}',
            'priority': 'normal'
        }
    
    def _check_reversal(self, position: object, predictions: Dict) -> Dict:
        """Check if key timeframes have reversed direction."""
        timeframes_data = predictions.get('timeframes', {})
        
        reversals = []
        
        for timeframe in self.reversal_timeframes:
            tf_data = timeframes_data.get(timeframe, {})
            
            if tf_data.get('status') != 'success':
                continue
            
            # Get dominant signal for this timeframe
            models = tf_data.get('models', [])
            if not models:
                continue
            
            signals = [m['prediction'] for m in models]
            from collections import Counter
            most_common = Counter(signals).most_common(1)[0][0]
            
            # Check if it contradicts position
            if position.side == 'buy' and most_common == 'SELL':
                reversals.append(f"{timeframe}: {most_common}")
            elif position.side == 'sell' and most_common == 'BUY':
                reversals.append(f"{timeframe}: {most_common}")
        
        # Reversal if at least one key timeframe flipped
        is_reversal = len(reversals) > 0
        
        return {
            'is_reversal': is_reversal,
            'details': ', '.join(reversals) if reversals else 'No reversals',
            'reversed_timeframes': reversals
        }
    
    def _check_emergency_stop(self, position: object, current_price: float) -> bool:
        """Check if emergency stop loss hit (catastrophic move protection)."""
        if not position.stop_loss:
            return False
        
        if position.side == 'buy':
            return current_price <= position.stop_loss
        else:  # sell
            return current_price >= position.stop_loss
    
    def cleanup_position(self, symbol: str):
        """Clean up tracker when position is closed."""
        if symbol in self.position_trackers:
            del self.position_trackers[symbol]
            logger.debug(f"Cleaned up tracker for {symbol}")
    
    def get_tracker_stats(self) -> Dict:
        """Get statistics on all position trackers."""
        stats = {
            'total_tracked': len(self.position_trackers),
            'positions': []
        }
        
        for symbol, tracker in self.position_trackers.items():
            recent_pcs = tracker.get_recent(5)
            stats['positions'].append({
                'symbol': symbol,
                'current_pcs': recent_pcs[-1] if recent_pcs else 0,
                'trend': tracker.get_trend(),
                'history_length': len(tracker.history)
            })
        
        return stats

