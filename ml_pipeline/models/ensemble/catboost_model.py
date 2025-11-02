"""CatBoost classifier for trading signals."""

from catboost import CatBoostClassifier
import numpy as np
from typing import Tuple
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import logger


class CatBoostTrader:
    """CatBoost trading model."""
    
    def __init__(self, params: dict = None):
        self.model = CatBoostClassifier(
            iterations=1000,
            learning_rate=0.05,
            depth=6,
            loss_function='MultiClass',
            classes_count=3,
            eval_metric='MultiClass',
            early_stopping_rounds=50,
            verbose=50,
            **(params or {})
        )
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray = None, y_val: np.ndarray = None):
        """Train CatBoost model."""
        if X_val is not None:
            self.model.fit(
                X_train, y_train,
                eval_set=(X_val, y_val),
                verbose=50
            )
        else:
            self.model.fit(X_train, y_train)
        
        logger.info("CatBoost model trained")
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict trading signals."""
        probs = self.model.predict_proba(X)
        predictions = np.argmax(probs, axis=1)
        confidences = np.max(probs, axis=1)
        return predictions, confidences
    
    def save(self, path: str):
        self.model.save_model(path)
    
    def load(self, path: str):
        self.model.load_model(path)


