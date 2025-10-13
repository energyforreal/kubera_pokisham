"""XGBoost model for trading signal prediction."""

from pathlib import Path
from typing import Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from src.core.config import trading_config
from src.core.logger import logger


class XGBoostTradingModel:
    """XGBoost classifier for predicting trading signals."""
    
    def __init__(self):
        self.model: Optional[XGBClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: Optional[list] = None
        self.model_config = trading_config.model
        
    def create_model(self) -> XGBClassifier:
        """Create and configure XGBoost model.
        
        Returns:
            Configured XGBoost classifier
        """
        params = {
            'n_estimators': self.model_config.get('n_estimators', 200),
            'max_depth': self.model_config.get('max_depth', 6),
            'learning_rate': self.model_config.get('learning_rate', 0.1),
            'objective': 'multi:softprob',
            'num_class': 3,  # BUY, SELL, HOLD
            'eval_metric': 'mlogloss',
            'use_label_encoder': False,
            'random_state': 42,
            'n_jobs': -1
        }
        
        model = XGBClassifier(**params)
        logger.info("XGBoost model created", params=params)
        
        return model
    
    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None
    ) -> dict:
        """Train the XGBoost model.
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features (optional)
            y_val: Validation labels (optional)
            
        Returns:
            Training metrics dictionary
        """
        # Store feature names
        self.feature_names = list(X_train.columns)
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Create model
        self.model = self.create_model()
        
        # Prepare validation set
        eval_set = None
        if X_val is not None and y_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
            eval_set = [(X_train_scaled, y_train), (X_val_scaled, y_val)]
        
        # Train model
        logger.info("Training XGBoost model", samples=len(X_train), features=len(self.feature_names))
        
        self.model.fit(
            X_train_scaled,
            y_train,
            eval_set=eval_set,
            verbose=False
        )
        
        # Calculate training metrics
        train_pred = self.model.predict(X_train_scaled)
        train_accuracy = (train_pred == y_train).mean()
        
        metrics = {
            'train_accuracy': train_accuracy,
            'num_features': len(self.feature_names),
            'num_samples': len(X_train)
        }
        
        if X_val is not None and y_val is not None:
            val_pred = self.model.predict(X_val_scaled)
            val_accuracy = (val_pred == y_val).mean()
            metrics['val_accuracy'] = val_accuracy
        
        logger.info("Model training complete", metrics=metrics)
        
        return metrics
    
    def predict(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Make predictions with confidence scores.
        
        Args:
            X: Features DataFrame
            
        Returns:
            Tuple of (predictions, confidence scores)
        """
        if self.model is None or self.scaler is None:
            raise ValueError("Model not trained. Call train() or load() first.")
        
        # Ensure features are in correct order
        if self.feature_names:
            X = X[self.feature_names]
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Get predictions and probabilities
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)
        
        # Confidence is the max probability
        confidence = probabilities.max(axis=1)
        
        return predictions, confidence
    
    def predict_single(self, features: pd.DataFrame) -> Tuple[int, float, dict]:
        """Predict for a single sample with detailed output.
        
        Args:
            features: Single row DataFrame with features
            
        Returns:
            Tuple of (prediction, confidence, probabilities dict)
        """
        predictions, confidence = self.predict(features)
        
        # Get class probabilities
        X_scaled = self.scaler.transform(features[self.feature_names])
        probs = self.model.predict_proba(X_scaled)[0]
        
        prob_dict = {
            'SELL': float(probs[0]),
            'HOLD': float(probs[1]),
            'BUY': float(probs[2])
        }
        
        # Map prediction to label
        label_map = {0: 'SELL', 1: 'HOLD', 2: 'BUY'}
        prediction_label = label_map[predictions[0]]
        
        return prediction_label, float(confidence[0]), prob_dict
    
    def get_feature_importance(self, top_n: int = 20) -> pd.DataFrame:
        """Get feature importance scores.
        
        Args:
            top_n: Number of top features to return
            
        Returns:
            DataFrame with feature names and importance scores
        """
        if self.model is None:
            raise ValueError("Model not trained")
        
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        })
        
        importance_df = importance_df.sort_values('importance', ascending=False).head(top_n)
        
        return importance_df
    
    def save(self, filepath: str):
        """Save model, scaler, and feature names.
        
        Args:
            filepath: Path to save the model
        """
        if self.model is None:
            raise ValueError("No model to save")
        
        # Create directory if it doesn't exist
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names
        }
        
        joblib.dump(model_data, filepath)
        logger.info("Model saved", filepath=filepath)
    
    def load(self, filepath: str):
        """Load model, scaler, and feature names.
        
        Args:
            filepath: Path to the saved model
        """
        if not Path(filepath).exists():
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        
        logger.info("Model loaded", filepath=filepath, features=len(self.feature_names))

