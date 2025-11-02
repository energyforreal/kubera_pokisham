"""Hyperparameter optimization using Optuna for production trading."""

import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler
import numpy as np
from typing import Dict, Callable
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import logger


class HyperparameterOptimizer:
    """Optimize model hyperparameters using Optuna."""
    
    def __init__(
        self,
        objective_metric: str = 'sharpe_ratio',  # Changed from 'accuracy'
        n_trials: int = 200,
        timeout: int = 3600,  # 1 hour max
        n_jobs: int = 1
    ):
        """
        Initialize optimizer.
        
        Args:
            objective_metric: Metric to optimize ('sharpe_ratio', 'sortino_ratio', 'profit_factor')
            n_trials: Number of trials to run
            timeout: Max time in seconds
            n_jobs: Parallel jobs (1 = sequential)
        """
        self.objective_metric = objective_metric
        self.n_trials = n_trials
        self.timeout = timeout
        self.n_jobs = n_jobs
        
        # Setup Optuna
        self.sampler = TPESampler(seed=42)
        self.pruner = MedianPruner(n_startup_trials=20, n_warmup_steps=10)
    
    def optimize_xgboost(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        backtest_fn: Callable = None
    ) -> Dict:
        """
        Optimize XGBoost hyperparameters for TRADING (not just accuracy).
        
        Args:
            X_train, y_train: Training data
            X_val, y_val: Validation data
            backtest_fn: Function to calculate trading metrics (Sharpe, etc.)
        
        Returns:
            Best parameters
        """
        logger.info("Starting XGBoost hyperparameter optimization", 
                   metric=self.objective_metric, trials=self.n_trials)
        
        def objective(trial):
            # Suggest hyperparameters
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 100, 500, step=50),
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'gamma': trial.suggest_float('gamma', 0, 5),
                'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
                'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
                'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True),
                'objective': 'multi:softprob',
                'num_class': 3,
                'random_state': 42,
                'n_jobs': -1
            }
            
            # Train model
            from xgboost import XGBClassifier
            model = XGBClassifier(**params)
            model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
            
            # Get predictions
            val_pred = model.predict(X_val)
            val_proba = model.predict_proba(X_val)
            
            # If backtest function provided, calculate trading metrics
            if backtest_fn:
                metric_value = backtest_fn(val_pred, val_proba, y_val)
            else:
                # Fallback to accuracy (not recommended for live trading)
                metric_value = (val_pred == y_val).mean()
                logger.warning("Using accuracy as metric - NOT recommended for live trading!")
            
            return metric_value
        
        # Create study
        study = optuna.create_study(
            direction='maximize',
            sampler=self.sampler,
            pruner=self.pruner
        )
        
        # Optimize
        study.optimize(
            objective,
            n_trials=self.n_trials,
            timeout=self.timeout,
            n_jobs=self.n_jobs,
            show_progress_bar=True
        )
        
        logger.info("Optimization complete",
                   best_value=study.best_value,
                   best_params=study.best_params)
        
        return study.best_params
    
    def optimize_lightgbm(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        backtest_fn: Callable = None
    ) -> Dict:
        """Optimize LightGBM hyperparameters."""
        
        def objective(trial):
            params = {
                'objective': 'multiclass',
                'num_class': 3,
                'metric': 'multi_logloss',
                'boosting_type': trial.suggest_categorical('boosting_type', ['gbdt', 'dart']),
                'num_leaves': trial.suggest_int('num_leaves', 20, 100),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'feature_fraction': trial.suggest_float('feature_fraction', 0.6, 1.0),
                'bagging_fraction': trial.suggest_float('bagging_fraction', 0.6, 1.0),
                'bagging_freq': trial.suggest_int('bagging_freq', 1, 10),
                'min_child_samples': trial.suggest_int('min_child_samples', 5, 100),
                'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
                'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True),
                'verbose': -1
            }
            
            import lightgbm as lgb
            train_data = lgb.Dataset(X_train, label=y_train)
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            
            model = lgb.train(
                params,
                train_data,
                num_boost_round=1000,
                valid_sets=[val_data],
                callbacks=[lgb.early_stopping(50)]
            )
            
            val_pred = np.argmax(model.predict(X_val), axis=1)
            val_proba = model.predict(X_val)
            
            if backtest_fn:
                return backtest_fn(val_pred, val_proba, y_val)
            else:
                return (val_pred == y_val).mean()
        
        study = optuna.create_study(direction='maximize', sampler=self.sampler, pruner=self.pruner)
        study.optimize(objective, n_trials=self.n_trials, timeout=self.timeout, show_progress_bar=True)
        
        return study.best_params
    
    def optimize_deep_learning(
        self,
        input_dim: int,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        model_type: str = 'lstm',
        backtest_fn: Callable = None
    ) -> Dict:
        """Optimize deep learning model hyperparameters."""
        
        def objective(trial):
            params = {
                'hidden_dim': trial.suggest_categorical('hidden_dim', [64, 128, 256]),
                'num_layers': trial.suggest_int('num_layers', 1, 3),
                'dropout': trial.suggest_float('dropout', 0.1, 0.5),
                'learning_rate': trial.suggest_float('learning_rate', 1e-4, 1e-2, log=True),
                'batch_size': trial.suggest_categorical('batch_size', [16, 32, 64]),
            }
            
            # Import appropriate model
            if model_type == 'lstm':
                from ml_pipeline.models.deep_learning.lstm_attention import LSTMAttentionTrader
                model = LSTMAttentionTrader(
                    input_dim=input_dim,
                    hidden_dim=params['hidden_dim'],
                    num_layers=params['num_layers'],
                    dropout=params['dropout'],
                    device='cuda' if torch.cuda.is_available() else 'cpu'
                )
            else:
                from ml_pipeline.models.deep_learning.transformer import TransformerTrader
                model = TransformerTrader(input_dim=input_dim, device='cuda' if torch.cuda.is_available() else 'cpu')
            
            # Train with early stopping
            model.train(
                X_train, y_train, X_val, y_val,
                epochs=20,  # Reduced for tuning speed
                batch_size=params['batch_size'],
                learning_rate=params['learning_rate']
            )
            
            # Evaluate
            val_pred, val_conf = model.predict(X_val)
            
            if backtest_fn:
                return backtest_fn(val_pred, val_conf, y_val)
            else:
                return (val_pred == y_val).mean()
        
        study = optuna.create_study(direction='maximize', sampler=self.sampler, pruner=self.pruner)
        study.optimize(objective, n_trials=min(50, self.n_trials), timeout=self.timeout, show_progress_bar=True)
        
        return study.best_params


def calculate_trading_metric(predictions, probabilities, actuals, prices=None, metric='sharpe_ratio'):
    """
    Calculate trading-specific metric (CRITICAL for live trading).
    
    Args:
        predictions: Model predictions
        probabilities: Prediction probabilities
        actuals: Actual values
        prices: Price data (if available)
        metric: 'sharpe_ratio', 'sortino_ratio', 'profit_factor'
    
    Returns:
        Metric value (higher is better)
    """
    # Simulate trading returns based on predictions
    # Map predictions: 0=SELL(-1), 1=HOLD(0), 2=BUY(+1)
    positions = np.array([p - 1 for p in predictions])  # Convert to -1, 0, 1
    
    # Calculate returns based on actual price movements
    # If actuals = future direction: 0=down, 1=flat, 2=up
    actual_returns = (actuals - 1) * 0.01  # Simulate 1% move per signal
    
    # Strategy returns = position * actual_return
    strategy_returns = positions * actual_returns
    
    # Apply transaction costs
    position_changes = np.diff(positions, prepend=0)
    costs = np.abs(position_changes) * 0.002  # 0.2% per trade (realistic)
    strategy_returns = strategy_returns - costs
    
    # Calculate metric
    if metric == 'sharpe_ratio':
        if strategy_returns.std() == 0:
            return 0
        sharpe = (strategy_returns.mean() / strategy_returns.std()) * np.sqrt(252)
        return sharpe
    
    elif metric == 'sortino_ratio':
        downside = strategy_returns[strategy_returns < 0]
        if len(downside) == 0 or downside.std() == 0:
            return 0
        sortino = (strategy_returns.mean() / downside.std()) * np.sqrt(252)
        return sortino
    
    elif metric == 'profit_factor':
        wins = strategy_returns[strategy_returns > 0].sum()
        losses = abs(strategy_returns[strategy_returns < 0].sum())
        if losses == 0:
            return wins if wins > 0 else 0
        return wins / losses
    
    else:
        # Default to simple accuracy (not recommended)
        return (predictions == actuals).mean()

