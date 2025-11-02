"""Generic model wrapper for loading different types of ML models."""

import pickle
import joblib
from pathlib import Path
from typing import Any, Tuple
import numpy as np

from src.core.logger import logger


class GenericTradingModel:
    """Generic wrapper for loading and using different types of models."""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.model_type = None
    
    def load(self, filepath: str):
        """Load a model from file - supports multiple formats.
        
        Args:
            filepath: Path to the saved model
        """
        if not Path(filepath).exists():
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        logger.info(f"Loading model from {filepath}")
        
        try:
            # Try loading as wrapped model (with metadata)
            model_data = joblib.load(filepath)
            
            if isinstance(model_data, dict):
                # It's a wrapped model with metadata
                self.model = model_data.get('model')
                self.scaler = model_data.get('scaler', None)
                self.feature_names = model_data.get('feature_names', None)
                
                logger.info(
                    "Loaded wrapped model",
                    filepath=filepath,
                    type=type(self.model).__name__,
                    features=len(self.feature_names) if self.feature_names else 'unknown'
                )
            else:
                # It's a raw model
                self.model = model_data
                self.scaler = None
                self.feature_names = None
                
                logger.info(
                    "Loaded raw model",
                    filepath=filepath,
                    type=type(self.model).__name__
                )
            
            # Detect model type
            self.model_type = type(self.model).__name__
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}", exc_info=True)
            raise
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Make predictions using the loaded model.
        
        Args:
            X: Features array
            
        Returns:
            Tuple of (predictions, confidences)
        """
        if self.model is None:
            raise ValueError("Model not loaded. Call load() first.")
        
        try:
            # Get predictions
            predictions = self.model.predict(X)
            
            # Get confidence scores (probabilities if available)
            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(X)
                
                # For binary/multiclass, take max probability as confidence
                if probabilities.ndim == 2:
                    confidences = np.max(probabilities, axis=1)
                else:
                    confidences = np.abs(probabilities)
            else:
                # No probability method - use default confidence
                confidences = np.ones_like(predictions) * 0.7  # Default 70% confidence
            
            logger.debug(
                f"Prediction made",
                model_type=self.model_type,
                num_predictions=len(predictions),
                avg_confidence=float(np.mean(confidences))
            )
            
            return predictions, confidences
            
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}", exc_info=True)
            raise
    
    def __repr__(self):
        return f"GenericTradingModel(type={self.model_type}, loaded={self.model is not None})"

