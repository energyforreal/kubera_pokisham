"""Weighted blending ensemble."""

import numpy as np
from typing import List, Tuple, Dict
import joblib
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import logger


class WeightedBlendingEnsemble:
    """Weighted blending of multiple models with adaptive weights."""
    
    def __init__(self, base_models: List = None):
        self.base_models = base_models or []
        self.weights = None
        self.performance_history = []
    
    def add_base_model(self, model, name: str, weight: float = 1.0):
        """Add a base model with weight."""
        self.base_models.append({
            'model': model,
            'name': name,
            'weight': weight,
            'recent_accuracy': []
        })
    
    def optimize_weights(self, X_val: np.ndarray, y_val: np.ndarray):
        """Optimize weights based on validation performance."""
        from scipy.optimize import minimize
        
        # Get predictions from all models
        all_preds = []
        for model_info in self.base_models:
            preds, _ = model_info['model'].predict(X_val)
            all_preds.append(preds)
        
        all_preds = np.array(all_preds)
        
        # Objective: maximize accuracy
        def objective(weights):
            weighted_pred = np.average(all_preds, axis=0, weights=weights)
            pred_classes = np.round(weighted_pred).astype(int)
            pred_classes = np.clip(pred_classes, 0, 2)  # Ensure 0-2 range
            accuracy = np.mean(pred_classes == y_val)
            return -accuracy  # Minimize negative accuracy
        
        # Constraints: weights sum to 1, all non-negative
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        bounds = [(0, 1) for _ in range(len(self.base_models))]
        
        # Initial weights (uniform)
        x0 = np.ones(len(self.base_models)) / len(self.base_models)
        
        # Optimize
        result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
        
        if result.success:
            self.weights = result.x
            logger.info("Optimized weights", weights={
                self.base_models[i]['name']: f"{w:.3f}"
                for i, w in enumerate(self.weights)
            })
        else:
            logger.warning("Weight optimization failed, using uniform weights")
            self.weights = x0
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Make predictions using weighted blending."""
        if self.weights is None:
            # Use equal weights
            self.weights = np.ones(len(self.base_models)) / len(self.base_models)
        
        # Get predictions from all models
        all_preds = []
        all_confs = []
        
        for model_info in self.base_models:
            try:
                preds, confs = model_info['model'].predict(X)
                all_preds.append(preds)
                all_confs.append(confs)
            except Exception as e:
                logger.warning(f"Model prediction failed", model=model_info['name'], error=str(e))
                all_preds.append(np.ones(len(X)))
                all_confs.append(np.zeros(len(X)))
        
        # Weighted average
        all_preds = np.array(all_preds)
        all_confs = np.array(all_confs)
        
        weighted_preds = np.average(all_preds, axis=0, weights=self.weights)
        weighted_confs = np.average(all_confs, axis=0, weights=self.weights)
        
        # Round to get class predictions
        predictions = np.round(weighted_preds).astype(int)
        predictions = np.clip(predictions, 0, 2)
        
        return predictions, weighted_confs
    
    def update_weights_online(self, recent_performance: Dict[str, float]):
        """Adaptively update weights based on recent performance."""
        for i, model_info in enumerate(self.base_models):
            if model_info['name'] in recent_performance:
                model_info['recent_accuracy'].append(recent_performance[model_info['name']])
                
                # Keep only last 100 predictions
                if len(model_info['recent_accuracy']) > 100:
                    model_info['recent_accuracy'].pop(0)
        
        # Recalculate weights based on recent accuracy
        if all(len(m['recent_accuracy']) > 0 for m in self.base_models):
            accuracies = [np.mean(m['recent_accuracy']) for m in self.base_models]
            # Softmax to convert to weights
            exp_acc = np.exp(np.array(accuracies) * 5)  # Temperature = 5
            self.weights = exp_acc / np.sum(exp_acc)
    
    def save(self, path: str):
        joblib.dump({
            'weights': self.weights,
            'base_model_names': [m['name'] for m in self.base_models]
        }, path)
    
    def load(self, path: str):
        data = joblib.load(path)
        self.weights = data['weights']


