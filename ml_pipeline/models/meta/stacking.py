"""Stacking ensemble for combining multiple models."""

import numpy as np
from typing import List, Tuple, Dict
from sklearn.linear_model import LogisticRegression
import joblib
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import logger


class StackingEnsemble:
    """Stacking ensemble that combines base model predictions."""
    
    def __init__(self, base_models: List = None, meta_model = None):
        """
        Initialize stacking ensemble.
        
        Args:
            base_models: List of base models (must have predict method)
            meta_model: Meta learner (default: LogisticRegression)
        """
        self.base_models = base_models or []
        self.meta_model = meta_model or LogisticRegression(
            multi_class='multinomial',
            max_iter=1000,
            random_state=42
        )
        self.trained = False
    
    def add_base_model(self, model, name: str = None):
        """Add a base model to the ensemble."""
        self.base_models.append({
            'model': model,
            'name': name or f'model_{len(self.base_models)}'
        })
    
    def _get_base_predictions(self, X: np.ndarray) -> np.ndarray:
        """Get predictions from all base models."""
        base_preds = []
        
        for model_info in self.base_models:
            model = model_info['model']
            try:
                # Get predictions and confidences
                preds, confs = model.predict(X)
                
                # Stack predictions and confidences as features
                base_preds.append(preds)
                base_preds.append(confs)
            except Exception as e:
                logger.warning(f"Base model prediction failed", model=model_info['name'], error=str(e))
                # Add zeros as fallback
                base_preds.append(np.ones(len(X)))
                base_preds.append(np.zeros(len(X)))
        
        # Convert to feature matrix
        if base_preds:
            return np.column_stack(base_preds)
        else:
            return np.zeros((len(X), 1))
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray = None, y_val: np.ndarray = None):
        """Train the stacking ensemble."""
        if not self.base_models:
            raise ValueError("No base models added to ensemble")
        
        logger.info(f"Training stacking ensemble with {len(self.base_models)} base models")
        
        # Get base model predictions on training data
        train_base_preds = self._get_base_predictions(X_train)
        
        # Train meta model on base predictions
        self.meta_model.fit(train_base_preds, y_train)
        
        self.trained = True
        
        # Validate if validation set provided
        if X_val is not None and y_val is not None:
            val_base_preds = self._get_base_predictions(X_val)
            val_accuracy = self.meta_model.score(val_base_preds, y_val)
            logger.info(f"Stacking ensemble validation accuracy", accuracy=f"{val_accuracy:.4f}")
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Make predictions using stacking ensemble."""
        if not self.trained:
            raise ValueError("Ensemble not trained yet")
        
        # Get base model predictions
        base_preds = self._get_base_predictions(X)
        
        # Meta model prediction
        predictions = self.meta_model.predict(base_preds)
        
        # Get confidence from meta model probabilities
        probs = self.meta_model.predict_proba(base_preds)
        confidences = np.max(probs, axis=1)
        
        return predictions, confidences
    
    def save(self, path: str):
        """Save ensemble model."""
        joblib.dump({
            'meta_model': self.meta_model,
            'base_models': [m['name'] for m in self.base_models],
            'trained': self.trained
        }, path)
        logger.info(f"Stacking ensemble saved", path=path)
    
    def load(self, path: str):
        """Load ensemble model (base models must be loaded separately)."""
        data = joblib.load(path)
        self.meta_model = data['meta_model']
        self.trained = data['trained']
        logger.info(f"Stacking ensemble loaded", path=path)


