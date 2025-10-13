"""Multi-model predictor for ensemble trading signals."""

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from src.core.config import settings, trading_config
from src.core.logger import logger
from src.data.delta_client import DeltaExchangeClient
from src.data.feature_engineer import FeatureEngineer
from src.data.data_validator import DataValidator
from src.ml.xgboost_model import XGBoostTradingModel


class MultiModelPredictor:
    """Generate trading predictions using multiple models."""
    
    def __init__(self, strategy: str = 'confirmation'):
        """Initialize multi-model predictor.
        
        Args:
            strategy: Ensemble strategy - 'confirmation', 'weighted', or 'voting'
        """
        self.strategy = strategy
        self.models = []
        self.delta_client = DeltaExchangeClient()
        self.feature_engineer = FeatureEngineer()
        self.validator = DataValidator()
        
        # Load configuration
        multi_config = trading_config.model.get('multi_model', {})
        self.enabled = multi_config.get('enabled', False)
        self.require_all_agree = multi_config.get('require_all_agree', True)
        self.min_combined_confidence = multi_config.get('min_combined_confidence', 0.70)
        
        # Load models
        self._load_models()
        
    def _load_models(self):
        """Load all configured models."""
        multi_config = trading_config.model.get('multi_model', {})
        model_configs = multi_config.get('models', [])
        
        if not model_configs:
            # Fallback to default models
            model_configs = [
                {'path': 'models/xgboost_BTCUSD_15m.pkl', 'weight': 0.7, 'timeframe': '15m'},
                {'path': 'models/xgboost_BTCUSD_1h.pkl', 'weight': 0.3, 'timeframe': '1h'}
            ]
        
        for config in model_configs:
            model = XGBoostTradingModel()
            try:
                model.load(config['path'])
                self.models.append({
                    'model': model,
                    'weight': config.get('weight', 1.0 / len(model_configs)),
                    'timeframe': config.get('timeframe', '15m'),
                    'path': config['path']
                })
                logger.info(f"Loaded model", path=config['path'], timeframe=config.get('timeframe'))
            except FileNotFoundError:
                logger.warning(f"Model not found", path=config['path'])
    
    def get_latest_signal(self, symbol: str, timeframe: str = '15m') -> Dict:
        """Get combined trading signal from all models.
        
        Args:
            symbol: Trading symbol
            timeframe: Primary timeframe (used for data fetching)
            
        Returns:
            Combined signal dictionary with predictions from all models
        """
        start_time = time.time()
        
        if not self.models:
            logger.error("No models loaded")
            return self._empty_signal()
        
        try:
            # Fetch market data
            df = self.delta_client.get_ohlc_candles(
                symbol=symbol,
                resolution=timeframe,
                limit=300
            )
            
            if df.empty:
                logger.warning("No market data available")
                return self._empty_signal()
            
            # Validate data
            df, metrics = self.validator.validate_and_clean(df)
            
            # Create features ONCE (optimization - reuse for all models)
            df = self.feature_engineer.create_features(df)
            
            if df.empty:
                logger.error("Feature engineering failed", symbol=symbol, rows=len(df))
                return self._empty_signal()
            
            # Prepare features ONCE for all models (performance optimization)
            X, _, feature_names = self.feature_engineer.prepare_for_model(df)
            logger.debug(f"Features prepared", features=len(feature_names), samples=len(X))
            
            # Get predictions from all models (reusing same features)
            predictions = []
            for model_info in self.models:
                try:
                    pred, conf = model_info['model'].predict(X)
                    
                    # Get latest prediction
                    latest_pred = pred[-1] if len(pred) > 0 else 1  # Default to HOLD
                    latest_conf = conf[-1] if len(conf) > 0 else 0.0
                    signal_str = self._map_prediction(latest_pred)
                    
                    predictions.append({
                        'timeframe': model_info['timeframe'],
                        'prediction': latest_pred,
                        'confidence': latest_conf,
                        'weight': model_info['weight'],
                        'signal': signal_str
                    })
                    
                    # Log individual model prediction
                    logger.info(
                        f"Model prediction",
                        timeframe=model_info['timeframe'],
                        signal=signal_str,
                        confidence=f"{latest_conf:.2%}",
                        raw_prediction=latest_pred
                    )
                except Exception as model_error:
                    logger.error(
                        f"Model prediction failed",
                        timeframe=model_info['timeframe'],
                        error=str(model_error)
                    )
                    # Skip this model and continue with others
                    continue
            
            # Combine predictions based on strategy
            combined_signal = self._combine_predictions(predictions)
            
            # Add metadata
            combined_signal.update({
                'symbol': symbol,
                'timestamp': datetime.now(timezone.utc),
                'strategy': self.strategy,
                'individual_predictions': predictions,
                'data_quality': metrics.get('quality_score', 0)
            })
            
            # Calculate total duration
            duration = time.time() - start_time
            
            # Detailed logging
            if combined_signal.get('models_agree'):
                logger.info(
                    "Multi-model signal - AGREEMENT",
                    strategy=self.strategy,
                    signal=combined_signal.get('prediction'),
                    confidence=f"{combined_signal.get('confidence', 0):.2%}",
                    agreement_level=f"{combined_signal.get('agreement_level', 0):.0%}",
                    actionable=combined_signal.get('actionable'),
                    duration_ms=f"{duration*1000:.0f}"
                )
            else:
                logger.warning(
                    "Multi-model signal - DISAGREEMENT",
                    strategy=self.strategy,
                    final_signal=combined_signal.get('prediction'),
                    confidence=f"{combined_signal.get('confidence', 0):.2%}",
                    agreement_level=f"{combined_signal.get('agreement_level', 0):.0%}",
                    individual_signals=[f"{p['timeframe']}:{p['signal']}" for p in predictions],
                    reason="Models disagree - returning HOLD",
                    duration_ms=f"{duration*1000:.0f}"
                )
            
            # Log performance warning if too slow
            if duration > 3.0:
                logger.warning(
                    "Signal generation took too long",
                    duration_seconds=f"{duration:.2f}",
                    threshold="3s",
                    recommendation="Consider optimizing feature engineering or reducing data points"
                )
            
            return combined_signal
            
        except Exception as e:
            logger.error(
                f"Multi-model signal generation failed",
                error=str(e),
                symbol=symbol,
                timeframe=timeframe,
                num_models=len(self.models),
                exc_info=True
            )
            return self._empty_signal()
    
    def _combine_predictions(self, predictions: List[Dict]) -> Dict:
        """Combine predictions from multiple models based on strategy.
        
        Args:
            predictions: List of prediction dictionaries from each model
            
        Returns:
            Combined prediction dictionary
        """
        if self.strategy == 'confirmation':
            return self._confirmation_strategy(predictions)
        elif self.strategy == 'weighted':
            return self._weighted_strategy(predictions)
        elif self.strategy == 'voting':
            return self._voting_strategy(predictions)
        else:
            logger.warning(f"Unknown strategy: {self.strategy}, using confirmation")
            return self._confirmation_strategy(predictions)
    
    def _confirmation_strategy(self, predictions: List[Dict]) -> Dict:
        """Require all models to agree on the same signal.
        
        Args:
            predictions: List of predictions
            
        Returns:
            Combined signal (HOLD if models disagree)
        """
        # Check if all models agree
        signals = [p['signal'] for p in predictions]
        predictions_raw = [p['prediction'] for p in predictions]
        confidences = [p['confidence'] for p in predictions]
        
        # All must agree and not be HOLD
        all_agree = len(set(predictions_raw)) == 1 and predictions_raw[0] != 1
        
        if all_agree:
            # Use minimum confidence (most conservative)
            min_confidence = min(confidences)
            
            return {
                'prediction': signals[0],
                'confidence': min_confidence,
                'models_agree': True,
                'agreement_level': 1.0,
                'actionable': min_confidence >= self.min_combined_confidence
            }
        else:
            # Models disagree - return HOLD
            return {
                'prediction': 'HOLD',
                'confidence': 0.0,
                'models_agree': False,
                'agreement_level': 0.0,
                'actionable': False
            }
    
    def _weighted_strategy(self, predictions: List[Dict]) -> Dict:
        """Use weighted average of predictions.
        
        Args:
            predictions: List of predictions with weights
            
        Returns:
            Weighted combined signal
        """
        # Calculate weighted average of raw predictions (0=SELL, 1=HOLD, 2=BUY)
        weighted_sum = sum(p['prediction'] * p['weight'] for p in predictions)
        total_weight = sum(p['weight'] for p in predictions)
        weighted_avg = weighted_sum / total_weight if total_weight > 0 else 1
        
        # Calculate weighted confidence
        weighted_conf = sum(p['confidence'] * p['weight'] for p in predictions) / total_weight if total_weight > 0 else 0
        
        # Map to signal
        if weighted_avg > 1.5:  # Closer to 2 (BUY)
            final_signal = 'BUY'
        elif weighted_avg < 0.5:  # Closer to 0 (SELL)
            final_signal = 'SELL'
        else:  # Around 1 (HOLD)
            final_signal = 'HOLD'
        
        # Calculate agreement level
        signals = [p['signal'] for p in predictions]
        agreement = signals.count(final_signal) / len(signals) if signals else 0
        
        return {
            'prediction': final_signal,
            'confidence': weighted_conf,
            'models_agree': agreement >= 0.7,
            'agreement_level': agreement,
            'actionable': weighted_conf >= self.min_combined_confidence and final_signal != 'HOLD'
        }
    
    def _voting_strategy(self, predictions: List[Dict]) -> Dict:
        """Use majority voting with averaged confidence.
        
        Args:
            predictions: List of predictions
            
        Returns:
            Majority vote signal
        """
        signals = [p['signal'] for p in predictions]
        confidences = [p['confidence'] for p in predictions]
        
        # Count votes
        vote_counts = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        for signal in signals:
            vote_counts[signal] += 1
        
        # Get majority
        majority_signal = max(vote_counts, key=vote_counts.get)
        majority_count = vote_counts[majority_signal]
        
        # Average confidence from models that voted for majority
        majority_confidences = [
            p['confidence'] for p in predictions 
            if p['signal'] == majority_signal
        ]
        avg_confidence = np.mean(majority_confidences) if majority_confidences else 0
        
        # Agreement level
        agreement = majority_count / len(predictions) if predictions else 0
        
        return {
            'prediction': majority_signal,
            'confidence': avg_confidence,
            'models_agree': agreement >= 0.7,
            'agreement_level': agreement,
            'actionable': avg_confidence >= self.min_combined_confidence and majority_signal != 'HOLD'
        }
    
    def _map_prediction(self, prediction: int) -> str:
        """Map numeric prediction to signal string.
        
        Args:
            prediction: 0 (SELL), 1 (HOLD), 2 (BUY)
            
        Returns:
            Signal string
        """
        mapping = {0: 'SELL', 1: 'HOLD', 2: 'BUY'}
        return mapping.get(prediction, 'HOLD')
    
    def _empty_signal(self) -> Dict:
        """Return empty/default signal."""
        return {
            'prediction': 'HOLD',
            'confidence': 0.0,
            'models_agree': False,
            'agreement_level': 0.0,
            'actionable': False,
            'symbol': '',
            'timestamp': datetime.utcnow(),
            'strategy': self.strategy,
            'individual_predictions': [],
            'data_quality': 0
        }

