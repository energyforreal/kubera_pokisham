"""LightGBM classifier for trading signals."""

import lightgbm as lgb
import numpy as np
from typing import Tuple
import joblib
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import logger


class LightGBMTrader:
    """LightGBM trading model."""
    
    def __init__(self, params: dict = None):
        self.params = params or {
            'objective': 'multiclass',
            'num_class': 3,
            'metric': 'multi_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1
        }
        self.model = None
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray = None, y_val: np.ndarray = None):
        """Train LightGBM model."""
        train_data = lgb.Dataset(X_train, label=y_train)
        
        if X_val is not None:
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            self.model = lgb.train(
                self.params,
                train_data,
                num_boost_round=1000,
                valid_sets=[train_data, val_data],
                callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(50)]
            )
        else:
            self.model = lgb.train(self.params, train_data, num_boost_round=1000)
        
        logger.info("LightGBM model trained")
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict trading signals."""
        # LightGBM Booster.predict() returns raw predictions
        # For multiclass, we need to ensure we get probabilities
        raw_pred = self.model.predict(X)
        
        # Check if we got probabilities (2D) or predictions (1D)
        if len(raw_pred.shape) == 1:
            # Got 1D array - likely class predictions, not probabilities
            # This happens if predict() returns argmax instead of probabilities
            # Solution: Use the raw predictions as class labels
            n_samples = len(X)
            n_classes = self.params.get('num_class', 3)
            
            # Check if it's flattened probabilities or actual predictions
            if len(raw_pred) == n_samples * n_classes:
                # Flattened probabilities - reshape
                probs = raw_pred.reshape(n_samples, n_classes)
            else:
                # These are class predictions - create one-hot style probabilities
                predictions = raw_pred.astype(int)
                # Create confidence scores (use 0.6 for predicted class, distribute rest)
                probs = np.ones((n_samples, n_classes)) * 0.2  # Base probability
                for i, pred in enumerate(predictions):
                    if 0 <= pred < n_classes:
                        probs[i, pred] = 0.6  # Higher confidence for predicted class
        else:
            # Got 2D array - these are probabilities
            probs = raw_pred
        
        predictions = np.argmax(probs, axis=1)
        confidences = np.max(probs, axis=1)
        return predictions, confidences
    
    def save(self, path: str):
        self.model.save_model(path)
    
    def load(self, path: str):
        self.model = lgb.Booster(model_file=path)


