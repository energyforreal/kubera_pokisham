"""Walk-forward validation for production trading strategies."""

import numpy as np
import pandas as pd
import time
from typing import Dict, List, Tuple, Callable
from datetime import datetime, timedelta
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import logger
from ml_pipeline.evaluation.backtester import VectorizedBacktester


class WalkForwardValidator:
    """
    Walk-forward validation - ESSENTIAL for live trading.
    
    Validates strategy on truly unseen future data to prevent overfitting.
    """
    
    def __init__(
        self,
        train_window: int = 180,  # 6 months
        test_window: int = 30,    # 1 month
        step_size: int = 7,       # 1 week
        min_train_samples: int = 100,  # Reduced from 1000 for flexibility
        window_unit: str = 'samples'   # 'samples' or 'days'
    ):
        """
        Initialize walk-forward validator.
        
        Args:
            train_window: Training window (in samples or days based on window_unit)
            test_window: Testing window (in samples or days based on window_unit)
            step_size: Step size for rolling window (in samples or days)
            min_train_samples: Minimum samples needed for training
            window_unit: 'samples' (row count) or 'days' (will convert based on data frequency)
        """
        self.train_window = train_window
        self.test_window = test_window
        self.step_size = step_size
        self.min_train_samples = min_train_samples
        self.window_unit = window_unit
        
        logger.info(
            "Walk-forward validator initialized",
            train_window=train_window,
            test_window=test_window,
            step_size=step_size
        )
    
    def create_windows(self, data: pd.DataFrame) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Create rolling train/test windows.
        
        Returns:
            List of (train_data, test_data) tuples
        """
        windows = []
        
        start = 0
        total_window = self.train_window + self.test_window
        
        while start + total_window <= len(data):
            train_end = start + self.train_window
            test_end = train_end + self.test_window
            
            train_data = data.iloc[start:train_end].copy()
            test_data = data.iloc[train_end:test_end].copy()
            
            # Only add if minimum samples met
            if len(train_data) >= self.min_train_samples:
                windows.append((train_data, test_data))
            
            start += self.step_size
        
        logger.info(f"Created {len(windows)} walk-forward windows")
        return windows
    
    def validate_strategy(
        self,
        data: pd.DataFrame,
        train_fn: Callable,
        predict_fn: Callable,
        optimize_params: bool = True
    ) -> Dict:
        """
        Perform walk-forward validation.
        
        Args:
            data: Full dataset with features
            train_fn: Function(train_data, params) -> model
            predict_fn: Function(model, test_data) -> signals
            optimize_params: Whether to optimize params on each window
        
        Returns:
            Validation results with out-of-sample metrics
        """
        windows = self.create_windows(data)
        
        if not windows:
            raise ValueError("Not enough data for walk-forward validation")
        
        results = []
        all_predictions = []
        all_actuals = []
        
        logger.info(f"Starting walk-forward validation", windows=len(windows))
        
        for i, (train_data, test_data) in enumerate(windows):
            window_start = time.time()
            
            # Train model on training window
            model = train_fn(train_data)
            
            # Predict on test window (out-of-sample)
            test_signals = predict_fn(model, test_data)
            
            # Backtest on test window
            backtester = VectorizedBacktester(test_data)
            backtest_results = backtester.run(signals=test_signals)
            
            # Store results
            window_metrics = backtest_results['metrics']
            results.append({
                'window': i + 1,
                'train_start': train_data.index[0],
                'train_end': train_data.index[-1],
                'test_start': test_data.index[0],
                'test_end': test_data.index[-1],
                'train_samples': len(train_data),
                'test_samples': len(test_data),
                'sharpe_ratio': window_metrics['sharpe_ratio'],
                'sortino_ratio': window_metrics['sortino_ratio'],
                'total_return': window_metrics['total_return'],
                'max_drawdown': window_metrics['max_drawdown'],
                'win_rate': window_metrics['win_rate'],
                'profit_factor': window_metrics['profit_factor'],
                'total_trades': window_metrics['total_trades']
            })
            
            # Collect predictions for overall analysis
            all_predictions.extend(test_signals.tolist())
            all_actuals.extend(test_data['target'].tolist() if 'target' in test_data else [])
            
            logger.info(
                f"Window {i+1}/{len(windows)} complete",
                sharpe=window_metrics['sharpe_ratio'],
                return_pct=window_metrics['total_return_percent'],
                trades=window_metrics['total_trades']
            )
        
        # Aggregate results
        results_df = pd.DataFrame(results)
        
        aggregate_metrics = {
            'avg_sharpe': results_df['sharpe_ratio'].mean(),
            'std_sharpe': results_df['sharpe_ratio'].std(),
            'avg_sortino': results_df['sortino_ratio'].mean(),
            'avg_return': results_df['total_return'].mean(),
            'avg_max_drawdown': results_df['max_drawdown'].mean(),
            'avg_win_rate': results_df['win_rate'].mean(),
            'avg_profit_factor': results_df['profit_factor'].mean(),
            'total_windows': len(windows),
            'profitable_windows': (results_df['total_return'] > 0).sum(),
            'profitable_window_rate': (results_df['total_return'] > 0).mean(),
            'consistency_score': 1 - (results_df['sharpe_ratio'].std() / (results_df['sharpe_ratio'].mean() + 1e-10))
        }
        
        logger.info(
            "Walk-forward validation complete",
            avg_sharpe=aggregate_metrics['avg_sharpe'],
            profitable_rate=aggregate_metrics['profitable_window_rate'],
            consistency=aggregate_metrics['consistency_score']
        )
        
        return {
            'aggregate_metrics': aggregate_metrics,
            'window_results': results_df,
            'all_predictions': all_predictions,
            'all_actuals': all_actuals
        }
    
    def plot_walk_forward_results(self, results: Dict, save_path: str = None):
        """Plot walk-forward validation results."""
        import matplotlib.pyplot as plt
        
        window_results = results['window_results']
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Sharpe ratio by window
        axes[0, 0].plot(window_results['window'], window_results['sharpe_ratio'], marker='o')
        axes[0, 0].axhline(y=0, color='r', linestyle='--', alpha=0.5)
        axes[0, 0].axhline(y=1.5, color='g', linestyle='--', alpha=0.5, label='Target')
        axes[0, 0].set_title('Sharpe Ratio by Window', fontweight='bold')
        axes[0, 0].set_xlabel('Window')
        axes[0, 0].set_ylabel('Sharpe Ratio')
        axes[0, 0].legend()
        axes[0, 0].grid(alpha=0.3)
        
        # Returns by window
        axes[0, 1].bar(window_results['window'], window_results['total_return'] * 100)
        axes[0, 1].axhline(y=0, color='r', linestyle='-', alpha=0.5)
        axes[0, 1].set_title('Returns by Window', fontweight='bold')
        axes[0, 1].set_xlabel('Window')
        axes[0, 1].set_ylabel('Return (%)')
        axes[0, 1].grid(axis='y', alpha=0.3)
        
        # Win rate by window
        axes[1, 0].plot(window_results['window'], window_results['win_rate'] * 100, marker='o', color='green')
        axes[1, 0].axhline(y=50, color='r', linestyle='--', alpha=0.5)
        axes[1, 0].set_title('Win Rate by Window', fontweight='bold')
        axes[1, 0].set_xlabel('Window')
        axes[1, 0].set_ylabel('Win Rate (%)')
        axes[1, 0].grid(alpha=0.3)
        
        # Max drawdown by window
        axes[1, 1].plot(window_results['window'], window_results['max_drawdown'] * 100, marker='o', color='red')
        axes[1, 1].axhline(y=15, color='orange', linestyle='--', alpha=0.5, label='Limit')
        axes[1, 1].set_title('Max Drawdown by Window', fontweight='bold')
        axes[1, 1].set_xlabel('Window')
        axes[1, 1].set_ylabel('Drawdown (%)')
        axes[1, 1].legend()
        axes[1, 1].grid(alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        plt.show()


# Import torch for deep learning optimization
try:
    import torch
except ImportError:
    logger.warning("PyTorch not available - deep learning optimization disabled")

