"""Random Forest classifier for trading signals."""

from sklearn.ensemble import RandomForestClassifier
import numpy as np
from typing import Tuple
import joblib
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import logger


class RandomForestTrader:
    """Random Forest trading model."""
    
    def __init__(self, params: dict = None):
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
            **(params or {})
        )
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray = None, y_val: np.ndarray = None):
        """Train Random Forest model."""
        self.model.fit(X_train, y_train)
        logger.info("Random Forest model trained")
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict trading signals."""
        probs = self.model.predict_proba(X)
        predictions = np.argmax(probs, axis=1)
        confidences = np.max(probs, axis=1)
        return predictions, confidences
    
    def save(self, path: str):
        joblib.dump(self.model, path)
    
    def load(self, path: str):
        self.model = joblib.load(path)


