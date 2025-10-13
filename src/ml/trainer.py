"""Model training pipeline with walk-forward validation."""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from src.core.logger import logger
from src.data.delta_client import DeltaExchangeClient
from src.data.feature_engineer import FeatureEngineer
from src.data.data_validator import DataValidator
from src.ml.xgboost_model import XGBoostTradingModel


class ModelTrainer:
    """Train and validate trading models."""
    
    def __init__(self):
        self.delta_client = DeltaExchangeClient()
        self.feature_engineer = FeatureEngineer()
        self.validator = DataValidator()
    
    def prepare_training_data(
        self,
        symbol: str,
        timeframe: str,
        days: int = 365
    ) -> pd.DataFrame:
        """Fetch and prepare data for training.
        
        Args:
            symbol: Trading symbol
            timeframe: Candle timeframe
            days: Number of days of historical data
            
        Returns:
            DataFrame with features and target
        """
        logger.info("Preparing training data", symbol=symbol, timeframe=timeframe, days=days)
        
        # Fetch historical data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        df = self.delta_client.get_ohlc_candles(
            symbol=symbol,
            resolution=timeframe,
            start=start_date,
            end=end_date,
            limit=days * 100  # Approximate candles
        )
        
        if df.empty:
            raise ValueError("No data fetched from Delta Exchange")
        
        # Validate and clean data
        df, quality_metrics = self.validator.validate_and_clean(df)
        logger.info("Data quality check complete", metrics=quality_metrics)
        
        # Create features
        df = self.feature_engineer.create_features(df)
        
        # Create target variable
        df = self._create_target(df)
        
        logger.info("Training data prepared", rows=len(df), features=len(df.columns))
        
        return df
    
    def _create_target(self, df: pd.DataFrame, forward_periods: int = 3) -> pd.DataFrame:
        """Create target variable based on future returns.
        
        Args:
            df: DataFrame with features
            forward_periods: Number of periods to look ahead
            
        Returns:
            DataFrame with target column added
        """
        # Calculate forward returns
        df['future_return'] = df['close'].shift(-forward_periods) / df['close'] - 1
        
        # Define thresholds for classification
        buy_threshold = 0.01   # 1% gain
        sell_threshold = -0.01  # 1% loss
        
        # Create target: 0=SELL, 1=HOLD, 2=BUY
        df['target'] = 1  # Default to HOLD
        df.loc[df['future_return'] > buy_threshold, 'target'] = 2  # BUY
        df.loc[df['future_return'] < sell_threshold, 'target'] = 0  # SELL
        
        # Drop last few rows (no future data)
        df = df.iloc[:-forward_periods]
        
        # Log target distribution
        target_dist = df['target'].value_counts().to_dict()
        logger.info("Target distribution", distribution=target_dist)
        
        return df
    
    def split_data(
        self,
        df: pd.DataFrame,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Split data into train, validation, and test sets.
        
        Args:
            df: Full dataset
            train_ratio: Proportion for training
            val_ratio: Proportion for validation
            test_ratio: Proportion for testing
            
        Returns:
            Tuple of (train_df, val_df, test_df)
        """
        total = len(df)
        train_end = int(total * train_ratio)
        val_end = int(total * (train_ratio + val_ratio))
        
        train_df = df.iloc[:train_end]
        val_df = df.iloc[train_end:val_end]
        test_df = df.iloc[val_end:]
        
        logger.info(
            "Data split complete",
            train=len(train_df),
            val=len(val_df),
            test=len(test_df)
        )
        
        return train_df, val_df, test_df
    
    def train_model(
        self,
        df: pd.DataFrame,
        save_path: Optional[str] = None
    ) -> XGBoostTradingModel:
        """Train XGBoost model with validation.
        
        Args:
            df: DataFrame with features and target
            save_path: Path to save trained model
            
        Returns:
            Trained model instance
        """
        # Split data
        train_df, val_df, test_df = self.split_data(df)
        
        # Prepare features and target
        X_train, y_train, feature_names = self.feature_engineer.prepare_for_model(train_df, 'target')
        X_val, y_val, _ = self.feature_engineer.prepare_for_model(val_df, 'target')
        X_test, y_test, _ = self.feature_engineer.prepare_for_model(test_df, 'target')
        
        # Create and train model
        model = XGBoostTradingModel()
        
        train_metrics = model.train(X_train, y_train, X_val, y_val)
        
        # Evaluate on test set
        test_pred, test_conf = model.predict(X_test)
        test_accuracy = (test_pred == y_test).mean()
        
        logger.info(
            "Model training complete",
            train_acc=train_metrics['train_accuracy'],
            val_acc=train_metrics.get('val_accuracy'),
            test_acc=test_accuracy
        )
        
        # Log feature importance
        feature_importance = model.get_feature_importance(top_n=10)
        logger.info("Top features", importance=feature_importance.to_dict('records'))
        
        # Save model
        if save_path:
            model.save(save_path)
        
        return model
    
    def walk_forward_validation(
        self,
        df: pd.DataFrame,
        n_splits: int = 5
    ) -> List[dict]:
        """Perform walk-forward validation.
        
        Args:
            df: DataFrame with features and target
            n_splits: Number of train/test splits
            
        Returns:
            List of validation results for each split
        """
        logger.info("Starting walk-forward validation", splits=n_splits)
        
        tscv = TimeSeriesSplit(n_splits=n_splits)
        results = []
        
        X, y, feature_names = self.feature_engineer.prepare_for_model(df, 'target')
        
        for i, (train_idx, test_idx) in enumerate(tscv.split(X)):
            logger.info(f"Fold {i+1}/{n_splits}", train_size=len(train_idx), test_size=len(test_idx))
            
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            # Train model
            model = XGBoostTradingModel()
            model.train(X_train, y_train)
            
            # Evaluate
            test_pred, test_conf = model.predict(X_test)
            accuracy = (test_pred == y_test).mean()
            
            # Calculate per-class metrics
            class_metrics = {}
            for class_label in [0, 1, 2]:  # SELL, HOLD, BUY
                mask = y_test == class_label
                if mask.sum() > 0:
                    class_acc = (test_pred[mask] == y_test[mask]).mean()
                    class_metrics[f'class_{class_label}_accuracy'] = class_acc
            
            results.append({
                'fold': i + 1,
                'accuracy': accuracy,
                'avg_confidence': test_conf.mean(),
                **class_metrics
            })
            
            logger.info(f"Fold {i+1} results", accuracy=accuracy, avg_confidence=test_conf.mean())
        
        # Calculate average metrics
        avg_accuracy = np.mean([r['accuracy'] for r in results])
        logger.info("Walk-forward validation complete", avg_accuracy=avg_accuracy, results=results)
        
        return results

