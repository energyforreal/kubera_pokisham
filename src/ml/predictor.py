"""Prediction service for generating trading signals."""

from datetime import datetime, timezone
from typing import Dict, Optional

import pandas as pd

from src.core.config import settings, trading_config
from src.core.logger import logger, get_component_logger
from src.data.delta_client import DeltaExchangeClient
from src.data.feature_engineer import FeatureEngineer
from src.data.data_validator import DataValidator
from src.ml.xgboost_model import XGBoostTradingModel


class TradingPredictor:
    """Generate trading predictions from market data."""
    
    def __init__(self, model_path: Optional[str] = None):
        # Initialize component logger
        self.logger = get_component_logger("ml_predictor")
        
        self.model = XGBoostTradingModel()
        self.delta_client = DeltaExchangeClient()
        self.feature_engineer = FeatureEngineer()
        self.validator = DataValidator()
        
        # Load model - prioritize config.yaml model path over .env
        if model_path is None:
            model_path = trading_config.model.get('path', settings.model_path)
        
        try:
            self.model.load(model_path)
            self.logger.info("model_loaded", "Prediction model loaded successfully", {"path": model_path})
        except FileNotFoundError:
            self.logger.warning("model_loading", "Model not found, needs training first", {"path": model_path})
    
    def get_latest_signal(self, symbol: str, timeframe: str = '15m') -> Dict:
        """Get latest trading signal for a symbol.
        
        Args:
            symbol: Trading symbol
            timeframe: Candle timeframe
            
        Returns:
            Signal dictionary with prediction, confidence, and metadata
        """
        import time
        start_time = time.time()
        
        self.logger.info("signal_generation", f"Generating signal for {symbol}", {"symbol": symbol, "timeframe": timeframe})
        
        try:
            # Fetch latest data (need enough for indicators)
            df = self.delta_client.get_ohlc_candles(
                symbol=symbol,
                resolution=timeframe,
                limit=300  # Enough for all indicators
            )
            
            if df.empty:
                return self._empty_signal("No data available")
            
            # Validate data
            df, quality_metrics = self.validator.validate_and_clean(df)
            
            if df.empty:
                return self._empty_signal("Data validation failed")
            
            # Create features
            df = self.feature_engineer.create_features(df)
            
            if df.empty:
                return self._empty_signal("Feature engineering failed")
            
            # Get latest row for prediction
            latest_features = df.tail(1)
            
            # Make prediction
            prediction, confidence, probabilities = self.model.predict_single(latest_features)
            
            # Get latest price info
            latest_candle = df.iloc[-1]
            
            signal = {
                'timestamp': datetime.now(timezone.utc),
                'symbol': symbol,
                'timeframe': timeframe,
                'prediction': prediction,
                'confidence': confidence,
                'probabilities': probabilities,
                'current_price': float(latest_candle['close']),
                'atr': float(latest_candle.get('atr', 0)),
                'rsi': float(latest_candle.get('rsi', 50)),
                'macd': float(latest_candle.get('macd', 0)),
                'volume_ratio': float(latest_candle.get('volume_ratio', 1)),
                'quality_score': quality_metrics.get('quality_score', 100),
                'candle_timestamp': latest_candle['timestamp']
            }
            
            # Determine if signal is actionable
            min_confidence = trading_config.signal_filters.get('min_confidence', 0.65)
            signal['is_actionable'] = confidence >= min_confidence and prediction != 'HOLD'
            
            duration_ms = (time.time() - start_time) * 1000
            self.logger.info(
                "signal_generated",
                "Signal generated successfully",
                {
                    "symbol": symbol,
                    "prediction": prediction,
                    "confidence": confidence,
                    "actionable": signal['is_actionable'],
                    "timeframe": timeframe
                },
                duration_ms=duration_ms
            )
            
            return signal
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error("signal_generation", "Signal generation failed", {"symbol": symbol, "error": str(e)}, duration_ms=duration_ms, error=e)
            return self._empty_signal(f"Error: {str(e)}")
    
    def get_multi_timeframe_signal(self, symbol: str) -> Dict:
        """Get signals from multiple timeframes and combine.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Combined signal from multiple timeframes
        """
        timeframes = trading_config.get_timeframes()
        signals = {}
        
        for tf in timeframes:
            signals[tf] = self.get_latest_signal(symbol, tf)
        
        # Combine signals (simple majority voting)
        predictions = [s['prediction'] for s in signals.values() if s['prediction'] != 'HOLD']
        confidences = [s['confidence'] for s in signals.values()]
        
        if not predictions:
            combined_prediction = 'HOLD'
            combined_confidence = 0.0
        else:
            # Most common prediction
            from collections import Counter
            prediction_counts = Counter(predictions)
            combined_prediction = prediction_counts.most_common(1)[0][0]
            
            # Average confidence of matching predictions
            matching_confidences = [
                signals[tf]['confidence']
                for tf in timeframes
                if signals[tf]['prediction'] == combined_prediction
            ]
            combined_confidence = sum(matching_confidences) / len(matching_confidences)
        
        combined_signal = {
            'timestamp': datetime.now(timezone.utc),
            'symbol': symbol,
            'prediction': combined_prediction,
            'confidence': combined_confidence,
            'timeframe_signals': signals,
            'is_actionable': combined_confidence >= trading_config.signal_filters.get('min_confidence', 0.65)
        }
        
        logger.info(
            "Multi-timeframe signal",
            symbol=symbol,
            prediction=combined_prediction,
            confidence=combined_confidence,
            timeframes=len(timeframes)
        )
        
        return combined_signal
    
    def _empty_signal(self, reason: str) -> Dict:
        """Create empty signal response.
        
        Args:
            reason: Reason for empty signal
            
        Returns:
            Empty signal dictionary
        """
        return {
            'timestamp': datetime.now(timezone.utc),
            'prediction': 'HOLD',
            'confidence': 0.0,
            'is_actionable': False,
            'reason': reason
        }

