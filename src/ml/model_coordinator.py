"""Model Coordinator - Central hub for managing all trading models across timeframes."""

import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import numpy as np

from src.core.config import trading_config
from src.core.logger import logger, get_component_logger
from src.ml.generic_model import GenericTradingModel
from src.data.delta_client import DeltaExchangeClient
from src.data.feature_engineer import FeatureEngineer
from src.data.data_validator import DataValidator
from src.utils.timestamp import get_current_time_utc, format_timestamp


class ModelInfo:
    """Container for model metadata and tracking."""
    
    def __init__(self, model: GenericTradingModel, config: Dict):
        self.model = model
        self.path = config['path']
        self.weight = config.get('weight', 0.2)
        self.timeframe = config.get('timeframe', '15m')
        self.role = config.get('role', 'general')
        self.algorithm = self._detect_algorithm(config['path'])
        
        # Performance tracking
        self.total_predictions = 0
        self.last_prediction_time = None
        self.recent_confidences = []
        self.is_healthy = True
        self.error_count = 0
        
    def _detect_algorithm(self, path: str) -> str:
        """Detect algorithm type from filename."""
        path_lower = path.lower()
        if 'randomforest' in path_lower or 'rf' in path_lower:
            return 'RandomForest'
        elif 'xgboost' in path_lower or 'xgb' in path_lower:
            return 'XGBoost'
        elif 'lightgbm' in path_lower or 'lgbm' in path_lower:
            return 'LightGBM'
        else:
            return 'Unknown'
    
    def record_prediction(self, confidence: float):
        """Record a prediction for tracking."""
        self.total_predictions += 1
        self.last_prediction_time = get_current_time_utc()
        self.recent_confidences.append(confidence)
        if len(self.recent_confidences) > 20:
            self.recent_confidences.pop(0)
    
    def record_error(self):
        """Record a prediction error."""
        self.error_count += 1
        if self.error_count >= 5:
            self.is_healthy = False
            logger.warning(f"Model {self.path} marked unhealthy after {self.error_count} errors")
    
    def get_avg_confidence(self) -> float:
        """Get average recent confidence."""
        if not self.recent_confidences:
            return 0.0
        return float(np.mean(self.recent_confidences))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for logging/reporting."""
        return {
            'path': self.path,
            'timeframe': self.timeframe,
            'algorithm': self.algorithm,
            'role': self.role,
            'weight': self.weight,
            'total_predictions': self.total_predictions,
            'avg_confidence': self.get_avg_confidence(),
            'is_healthy': self.is_healthy,
            'error_count': self.error_count
        }


class ModelCoordinator:
    """Coordinates all trading models across multiple timeframes."""
    
    def __init__(self):
        """Initialize the model coordinator."""
        # Initialize component logger
        self.logger = get_component_logger("ml_coordinator")
        
        self.models_by_timeframe: Dict[str, List[ModelInfo]] = {
            '15m': [],
            '1h': [],
            '4h': []
        }
        self.all_models: List[ModelInfo] = []
        
        # Data fetching
        self.delta_client = DeltaExchangeClient()
        self.feature_engineer = FeatureEngineer()
        self.validator = DataValidator()
        
        # Data cache with timestamps
        self.data_cache: Dict[str, Dict] = {}  # {timeframe: {data, timestamp}}
        self.cache_ttl = {
            '15m': 300,   # 5 minutes (matches signal interval)
            '1h': 600,    # 10 minutes
            '4h': 1800    # 30 minutes
        }
        
        # Load models from config
        self._load_models()
        
        self.logger.info(
            "initialization",
            "ModelCoordinator initialized",
            {
                "total_models": len(self.all_models),
                "models_15m": len(self.models_by_timeframe['15m']),
                "models_1h": len(self.models_by_timeframe['1h']),
                "models_4h": len(self.models_by_timeframe['4h'])
            }
        )
    
    def _load_models(self):
        """Load all models from configuration."""
        multi_config = trading_config.model.get('multi_model', {})
        model_configs = multi_config.get('models', [])
        
        if not model_configs:
            self.logger.error("model_loading", "No models configured in multi_model section!")
            return
        
        for config in model_configs:
            try:
                model = GenericTradingModel()
                model.load(config['path'])
                
                model_info = ModelInfo(model, config)
                timeframe = model_info.timeframe
                
                if timeframe in self.models_by_timeframe:
                    self.models_by_timeframe[timeframe].append(model_info)
                else:
                    self.logger.warning("model_loading", f"Unknown timeframe {timeframe} for model {config['path']}")
                    continue
                
                self.all_models.append(model_info)
                
                self.logger.info(
                    "model_loaded",
                    "Model loaded successfully",
                    {
                        "path": config['path'],
                        "timeframe": timeframe,
                        "algorithm": model_info.algorithm,
                        "role": model_info.role,
                        "weight": model_info.weight
                    }
                )
                
            except FileNotFoundError:
                self.logger.error("model_loading", f"Model file not found: {config['path']}")
            except Exception as e:
                self.logger.error("model_loading", f"Failed to load model {config['path']}", error=e)
        
        # Validate that we have models
        if len(self.all_models) == 0:
            raise RuntimeError("No models loaded! Cannot operate without models.")
    
    def _get_cached_data(self, symbol: str, timeframe: str) -> Optional[Tuple[object, Dict]]:
        """Get cached data if still fresh."""
        cache_key = f"{symbol}_{timeframe}"
        
        if cache_key not in self.data_cache:
            return None
        
        cached = self.data_cache[cache_key]
        cache_age = (get_current_time_utc() - cached['timestamp']).total_seconds()
        ttl = self.cache_ttl.get(timeframe, 300)
        
        if cache_age < ttl:
            logger.debug(f"Using cached data for {cache_key} (age: {cache_age:.0f}s)")
            return cached['df'], cached['metrics']
        else:
            logger.debug(f"Cache expired for {cache_key} (age: {cache_age:.0f}s, ttl: {ttl}s)")
            return None
    
    def _cache_data(self, symbol: str, timeframe: str, df, metrics: Dict):
        """Cache data with timestamp."""
        cache_key = f"{symbol}_{timeframe}"
        self.data_cache[cache_key] = {
            'df': df,
            'metrics': metrics,
            'timestamp': get_current_time_utc()
        }
    
    def _fetch_and_prepare_data(self, symbol: str, timeframe: str, use_cache: bool = True):
        """Fetch and prepare data for predictions."""
        # Check cache first
        if use_cache:
            cached = self._get_cached_data(symbol, timeframe)
            if cached is not None:
                return cached
        
        # Fetch fresh data
        try:
            df = self.delta_client.get_ohlc_candles(
                symbol=symbol,
                resolution=timeframe,
                limit=500
            )
            
            if df.empty:
                logger.warning(f"No data fetched for {symbol} {timeframe}")
                return None, {}
            
            # Validate
            df, metrics = self.validator.validate_and_clean(df)
            
            # Create features
            df = self.feature_engineer.create_features(df)
            
            if df.empty:
                logger.warning(f"Feature engineering failed for {symbol} {timeframe}")
                return None, {}
            
            # Cache the data
            self._cache_data(symbol, timeframe, df, metrics)
            
            logger.debug(
                f"Data fetched and prepared",
                symbol=symbol,
                timeframe=timeframe,
                rows=len(df),
                quality=metrics.get('quality_score', 0)
            )
            
            return df, metrics
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol} {timeframe}: {e}")
            return None, {}
    
    def get_all_predictions(self, symbol: str, use_cache: bool = True) -> Dict:
        """Get predictions from all models across all timeframes.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSD')
            use_cache: Whether to use cached data
            
        Returns:
            Dictionary with predictions organized by timeframe and model
        """
        start_time = time.time()
        self.logger.info("prediction_start", f"Starting predictions for {symbol}", {"symbol": symbol, "use_cache": use_cache})
        
        predictions = {
            'timestamp': get_current_time_utc(),
            'symbol': symbol,
            'timeframes': {},
            'all_healthy': True
        }
        
        for timeframe, models in self.models_by_timeframe.items():
            if not models:
                continue
            
            # Get data for this timeframe
            df, metrics = self._fetch_and_prepare_data(symbol, timeframe, use_cache)
            
            if df is None or df.empty:
                self.logger.warning("prediction_data", f"No data available for {timeframe}", {"timeframe": timeframe})
                predictions['timeframes'][timeframe] = {
                    'status': 'no_data',
                    'models': []
                }
                continue
            
            # Prepare features once for all models in this timeframe
            X, _, feature_names = self.feature_engineer.prepare_for_model(df)
            
            timeframe_predictions = []
            
            for model_info in models:
                try:
                    # Get prediction
                    pred, conf = model_info.model.predict(X)
                    
                    # Get latest
                    latest_pred = int(pred[-1]) if len(pred) > 0 else 1
                    latest_conf = float(conf[-1]) if len(conf) > 0 else 0.0
                    
                    # Map to signal
                    signal = self._map_prediction(latest_pred)
                    
                    # Record prediction
                    model_info.record_prediction(latest_conf)
                    
                    timeframe_predictions.append({
                        'model': model_info.algorithm,
                        'path': model_info.path,
                        'prediction': signal,
                        'prediction_raw': latest_pred,
                        'confidence': latest_conf,
                        'weight': model_info.weight,
                        'role': model_info.role,
                        'is_healthy': model_info.is_healthy
                    })
                    
                except Exception as e:
                    logger.error(
                        f"Prediction failed for {model_info.path}",
                        error=str(e)
                    )
                    model_info.record_error()
                    predictions['all_healthy'] = False
            
            predictions['timeframes'][timeframe] = {
                'status': 'success',
                'models': timeframe_predictions,
                'data_quality': metrics.get('quality_score', 0),
                'num_candles': len(df)
            }
        
        duration = time.time() - start_time
        predictions['duration_ms'] = int(duration * 1000)
        
        self.logger.info(
            "prediction_complete",
            "All predictions generated successfully",
            {
                "symbol": symbol,
                "duration_ms": predictions['duration_ms'],
                "timeframes": list(predictions['timeframes'].keys()),
                "all_healthy": predictions['all_healthy']
            },
            duration_ms=duration * 1000
        )
        
        return predictions
    
    def get_model_agreement_score(self, predictions: Dict, timeframe: Optional[str] = None) -> float:
        """Calculate agreement score among models.
        
        Args:
            predictions: Predictions dictionary from get_all_predictions
            timeframe: Specific timeframe to check, or None for all
            
        Returns:
            Agreement score (0-1)
        """
        all_signals = []
        
        if timeframe:
            # Single timeframe
            tf_data = predictions['timeframes'].get(timeframe, {})
            models = tf_data.get('models', [])
            all_signals = [m['prediction'] for m in models]
        else:
            # All timeframes
            for tf_data in predictions['timeframes'].values():
                models = tf_data.get('models', [])
                all_signals.extend([m['prediction'] for m in models])
        
        if not all_signals:
            return 0.0
        
        # Count most common signal
        from collections import Counter
        counts = Counter(all_signals)
        most_common_count = counts.most_common(1)[0][1]
        
        # Agreement = fraction that agree with majority
        agreement = most_common_count / len(all_signals)
        
        return agreement
    
    def validate_model_health(self) -> Dict:
        """Validate health of all models.
        
        Returns:
            Health status dictionary
        """
        health = {
            'timestamp': get_current_time_utc(),
            'total_models': len(self.all_models),
            'healthy_models': 0,
            'unhealthy_models': 0,
            'models': []
        }
        
        for model_info in self.all_models:
            if model_info.is_healthy:
                health['healthy_models'] += 1
            else:
                health['unhealthy_models'] += 1
            
            health['models'].append(model_info.to_dict())
        
        health['all_healthy'] = health['unhealthy_models'] == 0
        
        return health
    
    def _map_prediction(self, prediction: int) -> str:
        """Map numeric prediction to signal string."""
        mapping = {0: 'SELL', 1: 'HOLD', 2: 'BUY'}
        return mapping.get(prediction, 'HOLD')
    
    def clear_cache(self):
        """Clear all cached data."""
        self.data_cache.clear()
        logger.info("Data cache cleared")
    
    def get_stats(self) -> Dict:
        """Get coordinator statistics."""
        return {
            'total_models': len(self.all_models),
            'models_by_timeframe': {
                tf: len(models) for tf, models in self.models_by_timeframe.items()
            },
            'cache_size': len(self.data_cache),
            'model_health': self.validate_model_health()
        }
    
    def get_latest_signal(self, symbol: str, timeframe: str = '15m') -> Dict:
        """Get latest signal for API compatibility.
        
        This method provides backward compatibility with the old predictor interface.
        It aggregates predictions from the requested timeframe.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSD')
            timeframe: Requested timeframe (default: '15m')
            
        Returns:
            Signal dictionary compatible with API expectations
        """
        from src.ml.cross_timeframe_aggregator import CrossTimeframeAggregator
        
        try:
            # Get predictions from all timeframes
            predictions = self.get_all_predictions(symbol)
            
            # Aggregate using cross-timeframe logic
            aggregator = CrossTimeframeAggregator()
            
            # Get current price for aggregation
            ticker = self.delta_client.get_ticker(symbol)
            current_price = float(ticker.get('close', 0)) if ticker else 0
            
            # Calculate ATR (use 2% default if not available)
            atr = current_price * 0.02
            
            # Aggregate signals
            composite_signal = aggregator.aggregate_signals(
                predictions_by_timeframe=predictions,
                current_price=current_price,
                atr=atr
            )
            
            # Build individual predictions list for API
            individual_predictions = []
            for tf, tf_data in predictions.get('timeframes', {}).items():
                if tf_data.get('status') == 'success':
                    for model in tf_data.get('models', []):
                        individual_predictions.append({
                            'model': f"{model['model']}_{tf}",
                            'prediction': model['prediction'],
                            'confidence': model['confidence'],
                            'timeframe': tf,
                            'weight': model['weight']
                        })
            
            # Return signal in expected format
            return {
                'timestamp': composite_signal['timestamp'],
                'symbol': symbol,
                'timeframe': 'multi',  # Indicate multi-timeframe
                'prediction': composite_signal['signal'],
                'confidence': composite_signal['confidence'],
                'is_actionable': composite_signal['is_actionable'],
                'atr': atr,
                'current_price': current_price,
                'data_quality': composite_signal.get('quality_score', 0.5),
                'individual_predictions': individual_predictions,
                'num_models': composite_signal.get('num_models', 0),
                'timeframe_alignment': composite_signal.get('timeframe_alignment', {}),
                'entry_quality': composite_signal.get('entry_quality', {})
            }
            
        except Exception as e:
            logger.error(f"Failed to generate signal for {symbol}: {e}", exc_info=True)
            return {
                'error': str(e),
                'timestamp': get_current_time_utc(),
                'symbol': symbol,
                'timeframe': timeframe,
                'prediction': 'HOLD',
                'confidence': 0.0,
                'is_actionable': False,
                'data_quality': 0.0
            }

