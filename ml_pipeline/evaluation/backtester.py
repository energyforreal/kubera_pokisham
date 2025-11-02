"""Vectorized backtesting engine for trading strategies."""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import logger, get_component_logger


class VectorizedBacktester:
    """High-performance vectorized backtesting engine."""
    
    def __init__(
        self,
        data: pd.DataFrame,
        initial_balance: float = 10000.0,
        transaction_cost: float = 0.001,
        slippage: float = 0.0005
    ):
        """
        Initialize backtester.
        
        Args:
            data: OHLCV dataframe with features and signals
            initial_balance: Starting capital
            transaction_cost: Transaction cost (0.1% = 0.001)
            slippage: Slippage (0.05% = 0.0005)
        """
        # Initialize component logger
        self.logger = get_component_logger("ml_training")
        
        self.data = data.copy()
        self.initial_balance = initial_balance
        self.transaction_cost = transaction_cost
        self.slippage = slippage
        
        # Results
        self.trades = []
        self.equity_curve = None
        self.metrics = {}
        
        self.logger.info("initialization", "Vectorized backtester initialized", {
            "data_points": len(data),
            "initial_balance": initial_balance,
            "transaction_cost": transaction_cost,
            "slippage": slippage
        })
    
    def run(self, signals: pd.Series = None, signal_column: str = 'signal') -> Dict:
        """
        Run vectorized backtest.
        
        Args:
            signals: Series of trading signals (1=HOLD, 2=BUY, 0=SELL) or None to use signal_column
            signal_column: Column name in data containing signals
        
        Returns:
            Dictionary with backtest results
        """
        import time
        start_time = time.time()
        
        self.logger.info("backtest_start", "Starting vectorized backtest", {
            "data_points": len(self.data),
            "initial_balance": self.initial_balance,
            "signal_column": signal_column
        })
        
        try:
            # Use provided signals or extract from data
            if signals is None:
                if signal_column not in self.data.columns:
                    raise ValueError(f"Signal column '{signal_column}' not found in data")
                signals = self.data[signal_column]
            
            # Run the backtest logic
            results = self._execute_backtest(signals)
            
            duration_ms = (time.time() - start_time) * 1000
            self.logger.info("backtest_complete", "Backtest completed successfully", {
                "total_trades": len(self.trades),
                "final_balance": results.get('final_balance', 0),
                "total_return": results.get('total_return', 0),
                "sharpe_ratio": results.get('sharpe_ratio', 0),
                "max_drawdown": results.get('max_drawdown', 0),
                "duration_ms": duration_ms
            })
            
            return results
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error("backtest_error", "Backtest failed", {
                "error": str(e),
                "duration_ms": duration_ms
            }, error=e)
            raise
        
        # Use provided signals or from dataframe
        if signals is None:
            if signal_column not in self.data.columns:
                raise ValueError(f"Signal column '{signal_column}' not found")
            signals = self.data[signal_column]
        
        # Ensure same length
        if len(signals) != len(self.data):
            raise ValueError("Signals and data must have same length")
        
        # Convert signals to positions: 0=SELL/Short, 1=HOLD/Flat, 2=BUY/Long
        # Map to: -1=short, 0=flat, 1=long
        positions = signals.map({0: -1, 1: 0, 2: 1})
        
        # Calculate returns
        returns = self.data['close'].pct_change()
        
        # Strategy returns = position(t-1) * return(t)
        strategy_returns = positions.shift(1) * returns
        
        # Apply costs when position changes
        position_changes = positions.diff().fillna(0)
        costs = position_changes.abs() * (self.transaction_cost + self.slippage)
        strategy_returns = strategy_returns - costs
        
        # Calculate equity curve
        self.equity_curve = (1 + strategy_returns).cumprod() * self.initial_balance
        
        # Extract discrete trades
        self.trades = self._extract_trades(positions, self.data['close'], strategy_returns)
        
        # Calculate comprehensive metrics
        self.metrics = self._calculate_metrics(strategy_returns, self.equity_curve)
        
        logger.info("Backtest complete", 
                   total_trades=len(self.trades),
                   final_balance=self.equity_curve.iloc[-1],
                   total_return=self.metrics['total_return'])
        
        return {
            'equity_curve': self.equity_curve,
            'trades': self.trades,
            'metrics': self.metrics,
            'positions': positions,
            'returns': strategy_returns
        }
    
    def _extract_trades(
        self,
        positions: pd.Series,
        prices: pd.Series,
        returns: pd.Series
    ) -> List[Dict]:
        """Extract individual trades from position series."""
        trades = []
        
        # Find position changes
        position_changes = positions.diff()
        
        entry_idx = None
        entry_price = None
        entry_position = None
        
        for idx in range(len(positions)):
            current_pos = positions.iloc[idx]
            
            # Entry: moved from 0 to non-zero
            if entry_idx is None and current_pos != 0:
                entry_idx = idx
                entry_price = prices.iloc[idx]
                entry_position = current_pos
            
            # Exit: moved to 0 or reversed position
            elif entry_idx is not None and (current_pos == 0 or current_pos != entry_position):
                exit_price = prices.iloc[idx]
                
                # Calculate P&L
                if entry_position == 1:  # Long
                    pnl_pct = (exit_price / entry_price - 1) - (self.transaction_cost + self.slippage)
                else:  # Short
                    pnl_pct = (entry_price / exit_price - 1) - (self.transaction_cost + self.slippage)
                
                trades.append({
                    'entry_idx': entry_idx,
                    'exit_idx': idx,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'position': 'long' if entry_position == 1 else 'short',
                    'pnl_percent': pnl_pct,
                    'holding_periods': idx - entry_idx
                })
                
                # Reset if position is 0
                if current_pos == 0:
                    entry_idx = None
                else:
                    # New position started
                    entry_idx = idx
                    entry_price = exit_price
                    entry_position = current_pos
        
        return trades
    
    def _calculate_metrics(self, returns: pd.Series, equity: pd.Series) -> Dict:
        """Calculate comprehensive backtest metrics."""
        # Remove NaN values
        returns = returns.fillna(0)
        
        # Total return
        total_return = (equity.iloc[-1] / self.initial_balance) - 1
        
        # Annualized metrics (assuming daily data, adjust for your timeframe)
        periods_per_year = 252  # Trading days per year
        total_periods = len(returns)
        years = total_periods / periods_per_year
        
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        annual_volatility = returns.std() * np.sqrt(periods_per_year)
        
        # Sharpe ratio
        sharpe = annual_return / annual_volatility if annual_volatility > 0 else 0
        
        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(periods_per_year) if len(downside_returns) > 0 else 0
        sortino = annual_return / downside_std if downside_std > 0 else 0
        
        # Maximum drawdown
        cumulative = equity / equity.cummax()
        drawdown = 1 - cumulative
        max_drawdown = drawdown.max()
        max_drawdown_dollars = equity.cummax().max() - equity.min()
        
        # Calmar ratio
        calmar = abs(annual_return / max_drawdown) if max_drawdown > 0 else 0
        
        # Win rate and profit factor (from trades)
        if self.trades:
            wins = [t for t in self.trades if t['pnl_percent'] > 0]
            losses = [t for t in self.trades if t['pnl_percent'] < 0]
            
            win_rate = len(wins) / len(self.trades)
            
            gross_profit = sum(t['pnl_percent'] for t in wins) if wins else 0
            gross_loss = abs(sum(t['pnl_percent'] for t in losses)) if losses else 0
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf
            
            avg_win = np.mean([t['pnl_percent'] for t in wins]) if wins else 0
            avg_loss = np.mean([t['pnl_percent'] for t in losses]) if losses else 0
            avg_trade = np.mean([t['pnl_percent'] for t in self.trades])
            
            expectancy = (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))
        else:
            win_rate = 0
            profit_factor = 0
            avg_win = 0
            avg_loss = 0
            avg_trade = 0
            expectancy = 0
        
        return {
            'total_return': total_return,
            'total_return_percent': total_return * 100,
            'annual_return': annual_return,
            'annual_return_percent': annual_return * 100,
            'annual_volatility': annual_volatility,
            'annual_volatility_percent': annual_volatility * 100,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar,
            'max_drawdown': max_drawdown,
            'max_drawdown_percent': max_drawdown * 100,
            'max_drawdown_dollars': max_drawdown_dollars,
            'total_trades': len(self.trades),
            'win_rate': win_rate,
            'win_rate_percent': win_rate * 100,
            'profit_factor': profit_factor,
            'avg_win_percent': avg_win * 100,
            'avg_loss_percent': avg_loss * 100,
            'avg_trade_percent': avg_trade * 100,
            'expectancy': expectancy,
            'expectancy_percent': expectancy * 100,
            'final_balance': equity.iloc[-1],
            'peak_balance': equity.max(),
            'periods': len(returns)
        }
    
    def get_trade_analysis(self) -> pd.DataFrame:
        """Get detailed trade analysis."""
        if not self.trades:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.trades)
        
        # Add cumulative P&L
        df['cumulative_pnl'] = df['pnl_percent'].cumsum()
        
        # Add win/loss indicator
        df['result'] = df['pnl_percent'].apply(lambda x: 'Win' if x > 0 else ('Loss' if x < 0 else 'Breakeven'))
        
        return df
    
    def plot_results(self, save_path: Optional[str] = None):
        """Plot backtest results."""
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(3, 2, figsize=(15, 12))
        
        # Equity curve
        axes[0, 0].plot(self.equity_curve.index, self.equity_curve.values)
        axes[0, 0].axhline(y=self.initial_balance, color='r', linestyle='--', alpha=0.5)
        axes[0, 0].set_title('Equity Curve', fontweight='bold')
        axes[0, 0].set_ylabel('Balance ($)')
        axes[0, 0].grid(alpha=0.3)
        
        # Drawdown
        cumulative = self.equity_curve / self.equity_curve.cummax()
        drawdown = (1 - cumulative) * 100
        axes[0, 1].fill_between(drawdown.index, 0, drawdown.values, alpha=0.3, color='red')
        axes[0, 1].set_title('Drawdown', fontweight='bold')
        axes[0, 1].set_ylabel('Drawdown (%)')
        axes[0, 1].grid(alpha=0.3)
        
        # Trade P&L distribution
        if self.trades:
            pnls = [t['pnl_percent'] * 100 for t in self.trades]
            axes[1, 0].hist(pnls, bins=30, alpha=0.7, edgecolor='black')
            axes[1, 0].axvline(x=0, color='r', linestyle='--')
            axes[1, 0].set_title('Trade P&L Distribution', fontweight='bold')
            axes[1, 0].set_xlabel('P&L (%)')
            axes[1, 0].set_ylabel('Frequency')
            axes[1, 0].grid(alpha=0.3)
            
            # Cumulative P&L
            cumulative_pnl = np.cumsum(pnls)
            axes[1, 1].plot(cumulative_pnl)
            axes[1, 1].axhline(y=0, color='r', linestyle='--', alpha=0.5)
            axes[1, 1].set_title('Cumulative Trade P&L', fontweight='bold')
            axes[1, 1].set_xlabel('Trade #')
            axes[1, 1].set_ylabel('Cumulative P&L (%)')
            axes[1, 1].grid(alpha=0.3)
        
        # Monthly returns
        monthly_returns = self.equity_curve.resample('M').last().pct_change() * 100
        axes[2, 0].bar(range(len(monthly_returns)), monthly_returns.values)
        axes[2, 0].axhline(y=0, color='r', linestyle='-', alpha=0.3)
        axes[2, 0].set_title('Monthly Returns', fontweight='bold')
        axes[2, 0].set_ylabel('Return (%)')
        axes[2, 0].grid(alpha=0.3)
        
        # Metrics table
        metrics_text = f"""
        Total Return: {self.metrics['total_return_percent']:.2f}%
        Annual Return: {self.metrics['annual_return_percent']:.2f}%
        Sharpe Ratio: {self.metrics['sharpe_ratio']:.2f}
        Sortino Ratio: {self.metrics['sortino_ratio']:.2f}
        Max Drawdown: {self.metrics['max_drawdown_percent']:.2f}%
        
        Total Trades: {self.metrics['total_trades']}
        Win Rate: {self.metrics['win_rate_percent']:.2f}%
        Profit Factor: {self.metrics['profit_factor']:.2f}
        Expectancy: {self.metrics['expectancy_percent']:.2f}%
        """
        axes[2, 1].text(0.1, 0.5, metrics_text, fontsize=11, verticalalignment='center',
                       family='monospace')
        axes[2, 1].axis('off')
        axes[2, 1].set_title('Performance Metrics', fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")
        
        plt.show()
        
        return fig


class WalkForwardOptimizer:
    """Walk-forward optimization for strategy validation."""
    
    def __init__(
        self,
        data: pd.DataFrame,
        train_window: int = 180,  # days
        test_window: int = 30,    # days
        step_size: int = 7        # days
    ):
        """
        Initialize walk-forward optimizer.
        
        Args:
            data: Full dataset
            train_window: Training window size (days)
            test_window: Testing window size (days)
            step_size: Step size for rolling window (days)
        """
        self.data = data
        self.train_window = train_window
        self.test_window = test_window
        self.step_size = step_size
    
    def create_windows(self) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """Create rolling train/test windows."""
        windows = []
        
        start = 0
        total_window = self.train_window + self.test_window
        
        while start + total_window <= len(self.data):
            train_end = start + self.train_window
            test_end = train_end + self.test_window
            
            train_data = self.data.iloc[start:train_end]
            test_data = self.data.iloc[train_end:test_end]
            
            windows.append((train_data, test_data))
            start += self.step_size
        
        return windows
    
    def optimize(self, strategy_fn, param_grid: Dict) -> Dict:
        """
        Perform walk-forward optimization.
        
        Args:
            strategy_fn: Function that trains strategy and returns signals
            param_grid: Dictionary of parameters to test
        
        Returns:
            Optimization results
        """
        windows = self.create_windows()
        results = []
        
        logger.info(f"Walk-forward optimization", windows=len(windows))
        
        for i, (train_data, test_data) in enumerate(windows):
            # Train strategy on training window
            best_params = self._grid_search(strategy_fn, train_data, param_grid)
            
            # Test on out-of-sample data
            signals = strategy_fn(test_data, **best_params)
            
            # Backtest on test window
            backtester = VectorizedBacktester(test_data)
            result = backtester.run(signals)
            
            results.append({
                'window': i,
                'train_start': train_data.index[0],
                'train_end': train_data.index[-1],
                'test_start': test_data.index[0],
                'test_end': test_data.index[-1],
                'best_params': best_params,
                'test_metrics': result['metrics']
            })
            
            logger.info(f"Window {i+1}/{len(windows)}", sharpe=result['metrics']['sharpe_ratio'])
        
        return self._aggregate_results(results)
    
    def _grid_search(self, strategy_fn, data: pd.DataFrame, param_grid: Dict) -> Dict:
        """Simple grid search for best parameters."""
        # For now, return default params
        # TODO: Implement full grid search with parameter combinations
        return {k: v[0] if isinstance(v, list) else v for k, v in param_grid.items()}
    
    def _aggregate_results(self, results: List[Dict]) -> Dict:
        """Aggregate walk-forward results."""
        # Extract metrics from all windows
        sharpe_ratios = [r['test_metrics']['sharpe_ratio'] for r in results]
        returns = [r['test_metrics']['total_return'] for r in results]
        
        return {
            'avg_sharpe': np.mean(sharpe_ratios),
            'avg_return': np.mean(returns),
            'std_sharpe': np.std(sharpe_ratios),
            'std_return': np.std(returns),
            'windows': len(results),
            'detailed_results': results
        }


class MonteCarloSimulator:
    """Monte Carlo simulation for strategy robustness testing."""
    
    def __init__(self, historical_returns: np.ndarray, n_simulations: int = 1000):
        """
        Initialize Monte Carlo simulator.
        
        Args:
            historical_returns: Historical strategy returns
            n_simulations: Number of simulations to run
        """
        self.returns = historical_returns[~np.isnan(historical_returns)]
        self.n_simulations = n_simulations
    
    def simulate(self, periods: int = 252, initial_balance: float = 10000) -> Dict:
        """
        Run Monte Carlo simulation.
        
        Args:
            periods: Number of periods to simulate (252 = 1 year daily)
            initial_balance: Starting balance
        
        Returns:
            Simulation results
        """
        logger.info(f"Running Monte Carlo simulation", simulations=self.n_simulations, periods=periods)
        
        simulations = []
        final_balances = []
        
        for _ in range(self.n_simulations):
            # Bootstrap sample from historical returns
            simulated_returns = np.random.choice(self.returns, size=periods, replace=True)
            
            # Calculate equity curve
            equity = (1 + simulated_returns).cumprod() * initial_balance
            simulations.append(equity)
            final_balances.append(equity[-1])
        
        simulations = np.array(simulations)
        final_balances = np.array(final_balances)
        
        # Calculate percentiles
        percentiles = {
            'p5': np.percentile(simulations, 5, axis=0),
            'p25': np.percentile(simulations, 25, axis=0),
            'p50': np.percentile(simulations, 50, axis=0),
            'p75': np.percentile(simulations, 75, axis=0),
            'p95': np.percentile(simulations, 95, axis=0)
        }
        
        # Calculate statistics on final balances
        prob_profit = (final_balances > initial_balance).mean()
        prob_loss = (final_balances < initial_balance).mean()
        
        return {
            'simulations': simulations,
            'percentiles': percentiles,
            'final_balances': final_balances,
            'mean_final_balance': final_balances.mean(),
            'std_final_balance': final_balances.std(),
            'prob_profit': prob_profit,
            'prob_loss': prob_loss,
            'worst_case_p5': np.percentile(final_balances, 5),
            'best_case_p95': np.percentile(final_balances, 95)
        }
    
    def plot_simulation(self, results: Dict, save_path: Optional[str] = None):
        """Plot Monte Carlo simulation results."""
        import matplotlib.pyplot as plt
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Equity curve percentiles
        percentiles = results['percentiles']
        x = range(len(percentiles['p50']))
        
        ax1.fill_between(x, percentiles['p5'], percentiles['p95'], alpha=0.2, label='5-95 percentile')
        ax1.fill_between(x, percentiles['p25'], percentiles['p75'], alpha=0.3, label='25-75 percentile')
        ax1.plot(x, percentiles['p50'], linewidth=2, label='Median')
        ax1.set_title('Monte Carlo Simulation - Equity Curves', fontweight='bold')
        ax1.set_xlabel('Period')
        ax1.set_ylabel('Balance ($)')
        ax1.legend()
        ax1.grid(alpha=0.3)
        
        # Final balance distribution
        ax2.hist(results['final_balances'], bins=50, alpha=0.7, edgecolor='black')
        ax2.axvline(x=results['mean_final_balance'], color='r', linestyle='--', label='Mean')
        ax2.set_title('Final Balance Distribution', fontweight='bold')
        ax2.set_xlabel('Final Balance ($)')
        ax2.set_ylabel('Frequency')
        ax2.legend()
        ax2.grid(alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        plt.show()

