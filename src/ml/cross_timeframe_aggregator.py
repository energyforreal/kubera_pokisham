"""Cross-Timeframe Signal Aggregator - Intelligent signal combination across timeframes."""

from typing import Dict, List, Optional
from collections import Counter
import numpy as np

from src.core.config import trading_config
from src.core.logger import logger
from src.utils.timestamp import get_current_time_utc, format_timestamp


class CrossTimeframeAggregator:
    """Aggregates predictions from multiple models across different timeframes."""
    
    def __init__(self):
        """Initialize the aggregator."""
        # Get configuration
        self.config = trading_config.model.get('multi_model', {})
        self.min_combined_confidence = self.config.get('min_combined_confidence', 0.60)
        
        # Signal mapping
        self.signal_to_value = {'SELL': 0, 'HOLD': 1, 'BUY': 2}
        self.value_to_signal = {0: 'SELL', 1: 'HOLD', 2: 'BUY'}
        
        logger.info("CrossTimeframeAggregator initialized")
    
    def aggregate_signals(
        self,
        predictions_by_timeframe: Dict,
        current_price: float = 0,
        atr: float = 0
    ) -> Dict:
        """Aggregate signals from all timeframes into composite decision.
        
        Args:
            predictions_by_timeframe: Output from ModelCoordinator.get_all_predictions()
            current_price: Current market price (for volatility adjustment)
            atr: Average True Range (for volatility adjustment)
            
        Returns:
            Composite signal with detailed breakdown
        """
        timestamp = get_current_time_utc()
        
        # Extract timeframe data
        timeframes_data = predictions_by_timeframe.get('timeframes', {})
        
        # Collect all predictions with metadata
        all_predictions = []
        for timeframe, tf_data in timeframes_data.items():
            if tf_data.get('status') != 'success':
                continue
            
            for model_pred in tf_data.get('models', []):
                all_predictions.append({
                    'timeframe': timeframe,
                    'signal': model_pred['prediction'],
                    'confidence': model_pred['confidence'],
                    'weight': model_pred['weight'],
                    'role': model_pred['role'],
                    'model': model_pred['model']
                })
        
        if not all_predictions:
            logger.warning("No predictions available for aggregation")
            return self._empty_signal()
        
        # Calculate weighted consensus
        weighted_signal = self._calculate_weighted_consensus(all_predictions)
        
        # Check cross-timeframe alignment
        alignment = self._check_timeframe_alignment(timeframes_data)
        
        # Check for entry quality
        entry_quality = self._assess_entry_quality(all_predictions, timeframes_data)
        
        # Apply volatility adjustment
        if current_price > 0 and atr > 0:
            volatility_pct = (atr / current_price) * 100
            adjusted_threshold = self._adjust_for_volatility(volatility_pct)
        else:
            volatility_pct = 0
            adjusted_threshold = self.min_combined_confidence
        
        # Determine if signal is actionable
        is_actionable = (
            weighted_signal['confidence'] >= adjusted_threshold and
            weighted_signal['signal'] != 'HOLD' and
            alignment['is_aligned'] and
            entry_quality['meets_requirements']
        )
        
        # Build composite signal
        composite = {
            'timestamp': timestamp,
            'timestamp_display': format_timestamp(timestamp),
            'signal': weighted_signal['signal'],
            'confidence': weighted_signal['confidence'],
            'is_actionable': is_actionable,
            
            # Breakdown
            'weighted_consensus': weighted_signal,
            'timeframe_alignment': alignment,
            'entry_quality': entry_quality,
            
            # Thresholds
            'min_confidence_threshold': adjusted_threshold,
            'volatility_pct': volatility_pct,
            
            # All predictions for transparency
            'all_predictions': all_predictions,
            'num_models': len(all_predictions)
        }
        
        # Log decision
        if is_actionable:
            logger.info(
                "ACTIONABLE signal generated",
                signal=composite['signal'],
                confidence=f"{composite['confidence']:.2%}",
                alignment=f"{alignment['alignment_score']:.2%}",
                entry_quality=entry_quality['quality_score']
            )
        else:
            logger.debug(
                "Non-actionable signal",
                signal=composite['signal'],
                confidence=f"{composite['confidence']:.2%}",
                reasons=self._get_rejection_reasons(composite)
            )
        
        return composite
    
    def _calculate_weighted_consensus(self, predictions: List[Dict]) -> Dict:
        """Calculate weighted consensus across all predictions."""
        # Convert signals to numeric values
        weighted_sum = 0.0
        total_weight = 0.0
        weighted_confidence = 0.0
        
        signal_counts = Counter()
        
        for pred in predictions:
            signal = pred['signal']
            confidence = pred['confidence']
            weight = pred['weight']
            
            # Weighted signal value
            signal_value = self.signal_to_value.get(signal, 1)
            weighted_sum += signal_value * weight
            weighted_confidence += confidence * weight
            total_weight += weight
            
        # Count signals
        signal_counts[signal] += 1
        
        # Log individual model contributions
        logger.debug(
            f"Model contribution: {pred.get('model', 'Unknown')} ({pred['timeframe']}) - "
            f"Signal: {pred['signal']}, Confidence: {pred['confidence']:.2%}, "
            f"Weight: {pred['weight']:.2%}"
        )
        
        if total_weight == 0:
            return {'signal': 'HOLD', 'confidence': 0.0, 'agreement': 0.0}
        
        # Calculate weighted average
        weighted_avg = weighted_sum / total_weight
        avg_confidence = weighted_confidence / total_weight
        
        # Map back to signal
        if weighted_avg > 1.5:  # Closer to BUY (2)
            final_signal = 'BUY'
        elif weighted_avg < 0.5:  # Closer to SELL (0)
            final_signal = 'SELL'
        else:  # Around HOLD (1)
            final_signal = 'HOLD'
        
        # Calculate agreement (how many agree with final signal)
        agreement = signal_counts[final_signal] / len(predictions)
        
        return {
            'signal': final_signal,
            'confidence': avg_confidence,
            'agreement': agreement,
            'weighted_avg': weighted_avg,
            'signal_distribution': dict(signal_counts)
        }
    
    def _check_timeframe_alignment(self, timeframes_data: Dict) -> Dict:
        """Check if timeframes are aligned in their predictions."""
        # Extract dominant signal per timeframe
        timeframe_signals = {}
        
        for timeframe, tf_data in timeframes_data.items():
            if tf_data.get('status') != 'success':
                continue
            
            models = tf_data.get('models', [])
            if not models:
                continue
            
            # Get majority signal for this timeframe
            signals = [m['prediction'] for m in models]
            most_common = Counter(signals).most_common(1)
            if most_common:
                timeframe_signals[timeframe] = most_common[0][0]
        
        if len(timeframe_signals) < 2:
            return {
                'is_aligned': False,
                'alignment_score': 0.0,
                'reason': 'insufficient_timeframes'
            }
        
        # Check alignment
        all_signals = list(timeframe_signals.values())
        signal_counts = Counter(all_signals)
        most_common_signal = signal_counts.most_common(1)[0][0]
        agreement_count = signal_counts[most_common_signal]
        alignment_score = agreement_count / len(all_signals)
        
        # Require at least 2/3 agreement
        is_aligned = alignment_score >= 0.67
        
        return {
            'is_aligned': is_aligned,
            'alignment_score': alignment_score,
            'timeframe_signals': timeframe_signals,
            'dominant_signal': most_common_signal,
            'agreement_count': agreement_count,
            'total_timeframes': len(all_signals)
        }
    
    def _assess_entry_quality(
        self,
        all_predictions: List[Dict],
        timeframes_data: Dict
    ) -> Dict:
        """Assess quality of entry signal based on multiple criteria.
        
        Entry Requirements:
        - 15m model shows BUY/SELL with ≥65% confidence
        - Majority of 4h models agree on direction
        - 1h model not contradicting (allows HOLD)
        """
        # Get predictions by timeframe
        tf_15m = [p for p in all_predictions if p['timeframe'] == '15m']
        tf_1h = [p for p in all_predictions if p['timeframe'] == '1h']
        tf_4h = [p for p in all_predictions if p['timeframe'] == '4h']
        
        quality_checks = {
            '15m_signal_strong': False,
            '4h_majority_agrees': False,
            '1h_not_contradicting': False
        }
        
        reasons = []
        
        # Check 15m signal (entry timing)
        if tf_15m:
            max_conf_15m = max([p['confidence'] for p in tf_15m])
            signals_15m = [p['signal'] for p in tf_15m]
            dominant_15m = Counter(signals_15m).most_common(1)[0][0]
            
            if dominant_15m != 'HOLD' and max_conf_15m >= 0.65:
                quality_checks['15m_signal_strong'] = True
            else:
                reasons.append(f"15m weak: {dominant_15m} @ {max_conf_15m:.2%}")
        else:
            reasons.append("No 15m predictions")
        
        # Check 4h models (trend direction)
        if len(tf_4h) >= 2:
            signals_4h = [p['signal'] for p in tf_4h]
            signal_counts = Counter(signals_4h)
            most_common = signal_counts.most_common(1)[0]
            
            # Majority means more than half
            if most_common[1] > len(tf_4h) / 2:
                quality_checks['4h_majority_agrees'] = True
            else:
                reasons.append(f"4h split: {dict(signal_counts)}")
        else:
            reasons.append("Insufficient 4h models")
        
        # Check 1h not contradicting
        if tf_1h:
            signals_1h = [p['signal'] for p in tf_1h]
            dominant_1h = Counter(signals_1h).most_common(1)[0][0]
            
            # Get dominant signals from other timeframes
            if tf_15m:
                dominant_15m = Counter([p['signal'] for p in tf_15m]).most_common(1)[0][0]
            else:
                dominant_15m = 'HOLD'
            
            if tf_4h:
                dominant_4h = Counter([p['signal'] for p in tf_4h]).most_common(1)[0][0]
            else:
                dominant_4h = 'HOLD'
            
            # 1h can be HOLD or same direction, but not opposite
            is_contradiction = (
                (dominant_15m == 'BUY' and dominant_1h == 'SELL') or
                (dominant_15m == 'SELL' and dominant_1h == 'BUY') or
                (dominant_4h == 'BUY' and dominant_1h == 'SELL') or
                (dominant_4h == 'SELL' and dominant_1h == 'BUY')
            )
            
            if not is_contradiction:
                quality_checks['1h_not_contradicting'] = True
            else:
                reasons.append(f"1h contradicts: {dominant_1h}")
        else:
            # No 1h data means no contradiction
            quality_checks['1h_not_contradicting'] = True
        
        # Overall quality
        checks_passed = sum(quality_checks.values())
        quality_score = checks_passed / len(quality_checks)
        meets_requirements = all(quality_checks.values())
        
        return {
            'meets_requirements': meets_requirements,
            'quality_score': quality_score,
            'checks': quality_checks,
            'checks_passed': checks_passed,
            'total_checks': len(quality_checks),
            'rejection_reasons': reasons if not meets_requirements else []
        }
    
    def _adjust_for_volatility(self, volatility_pct: float) -> float:
        """Adjust confidence threshold based on market volatility."""
        base_threshold = self.min_combined_confidence
        
        # Get volatility config
        risk_config = trading_config.risk_management
        high_vol_threshold = risk_config.get('high_volatility_threshold', 5.0)
        high_vol_min_conf = risk_config.get('high_volatility_min_confidence', 0.70)
        
        if volatility_pct > high_vol_threshold:
            # Require higher confidence in volatile markets
            adjusted = high_vol_min_conf
            logger.info(
                f"High volatility detected",
                volatility_pct=f"{volatility_pct:.2f}%",
                adjusted_threshold=f"{adjusted:.2%}"
            )
            return adjusted
        
        return base_threshold
    
    def _get_rejection_reasons(self, composite: Dict) -> List[str]:
        """Get reasons why signal was not actionable."""
        reasons = []
        
        if composite['signal'] == 'HOLD':
            reasons.append("Signal is HOLD")
        
        if composite['confidence'] < composite['min_confidence_threshold']:
            reasons.append(
                f"Confidence {composite['confidence']:.2%} < "
                f"threshold {composite['min_confidence_threshold']:.2%}"
            )
        
        if not composite['timeframe_alignment']['is_aligned']:
            reasons.append("Timeframes not aligned")
        
        if not composite['entry_quality']['meets_requirements']:
            reasons.extend(composite['entry_quality']['rejection_reasons'])
        
        return reasons
    
    def _empty_signal(self) -> Dict:
        """Return empty/default signal."""
        return {
            'timestamp': get_current_time_utc(),
            'signal': 'HOLD',
            'confidence': 0.0,
            'is_actionable': False,
            'reason': 'no_predictions_available'
        }

