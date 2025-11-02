"""Risk management and calculation."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from src.core.config import trading_config
from src.core.database import Trade, PerformanceMetrics
from src.core.logger import logger, get_component_logger


class RiskManager:
    """Calculate and monitor risk metrics."""
    
    def __init__(self, db: Session):
        # Initialize component logger
        self.logger = get_component_logger("risk_manager")
        
        self.db = db
        self.config = trading_config.risk_management
        
        self.logger.info("initialization", "Risk manager initialized", {
            "max_daily_loss_percent": self.config.get('max_daily_loss_percent', 5),
            "max_drawdown_percent": self.config.get('max_drawdown_percent', 15),
            "max_consecutive_losses": self.config.get('max_consecutive_losses', 5)
        })
    
    def calculate_var(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """Calculate Value at Risk (VaR).
        
        Args:
            returns: Array of returns
            confidence: Confidence level (default 95%)
            
        Returns:
            VaR value
        """
        if len(returns) == 0:
            return 0.0
        
        var = np.percentile(returns, (1 - confidence) * 100)
        return float(var)
    
    def calculate_cvar(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """Calculate Conditional Value at Risk (CVaR/Expected Shortfall).
        
        Args:
            returns: Array of returns
            confidence: Confidence level
            
        Returns:
            CVaR value
        """
        if len(returns) == 0:
            return 0.0
        
        var = self.calculate_var(returns, confidence)
        cvar = returns[returns <= var].mean()
        
        return float(cvar) if not np.isnan(cvar) else 0.0
    
    def calculate_max_drawdown(self, equity_curve: pd.Series) -> Dict:
        """Calculate maximum drawdown and related metrics.
        
        Args:
            equity_curve: Series of equity values
            
        Returns:
            Dict with max_drawdown, duration, start, end
        """
        if len(equity_curve) == 0:
            return {'max_drawdown': 0.0, 'duration': 0, 'start': None, 'end': None}
        
        # Calculate running maximum
        running_max = equity_curve.cummax()
        
        # Calculate drawdown
        drawdown = (equity_curve - running_max) / running_max
        
        max_dd = drawdown.min()
        
        # Find drawdown period
        if max_dd < 0:
            max_dd_idx = drawdown.idxmin()
            # Find start of drawdown (last peak before max dd)
            start_idx = running_max[:max_dd_idx].idxmax()
            # Find end of drawdown (when equity recovers)
            recovery = equity_curve[max_dd_idx:] >= running_max[max_dd_idx]
            end_idx = recovery.idxmax() if recovery.any() else equity_curve.index[-1]
            
            duration = (end_idx - start_idx).days if hasattr(end_idx - start_idx, 'days') else 0
        else:
            start_idx, end_idx = None, None
            duration = 0
        
        return {
            'max_drawdown': float(max_dd),
            'max_drawdown_pct': float(max_dd * 100),
            'duration': duration,
            'start': start_idx,
            'end': end_idx
        }
    
    def calculate_sharpe_ratio(
        self,
        returns: np.ndarray,
        risk_free_rate: float = 0.02,
        periods_per_year: int = 252
    ) -> float:
        """Calculate Sharpe Ratio.
        
        Args:
            returns: Array of returns
            risk_free_rate: Annual risk-free rate
            periods_per_year: Trading periods per year
            
        Returns:
            Sharpe ratio
        """
        if len(returns) == 0 or returns.std() == 0:
            return 0.0
        
        # Annualize returns and volatility
        annual_return = returns.mean() * periods_per_year
        annual_volatility = returns.std() * np.sqrt(periods_per_year)
        
        sharpe = (annual_return - risk_free_rate) / annual_volatility
        
        return float(sharpe)
    
    def calculate_sortino_ratio(
        self,
        returns: np.ndarray,
        risk_free_rate: float = 0.02,
        periods_per_year: int = 252
    ) -> float:
        """Calculate Sortino Ratio (uses downside deviation).
        
        Args:
            returns: Array of returns
            risk_free_rate: Annual risk-free rate
            periods_per_year: Trading periods per year
            
        Returns:
            Sortino ratio
        """
        if len(returns) == 0:
            return 0.0
        
        # Downside returns only
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        
        annual_return = returns.mean() * periods_per_year
        downside_std = downside_returns.std() * np.sqrt(periods_per_year)
        
        sortino = (annual_return - risk_free_rate) / downside_std
        
        return float(sortino)
    
    def get_daily_metrics(self, date: Optional[datetime] = None) -> Dict:
        """Get risk metrics for a specific date.
        
        Args:
            date: Date to get metrics for (default: today)
            
        Returns:
            Dict with daily risk metrics
        """
        import time
        start_time = time.time()
        
        if date is None:
            date = datetime.now(timezone.utc).date()
        
        self.logger.info("risk_calculation", f"Calculating daily risk metrics for {date}", {"date": date.isoformat()})
        
        # Get performance metrics
        perf = self.db.query(PerformanceMetrics).filter(
            PerformanceMetrics.date >= datetime.combine(date, datetime.min.time())
        ).order_by(PerformanceMetrics.date.desc()).first()
        
        if not perf:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.warning("risk_calculation", f"No performance data found for {date}", {
                "date": date.isoformat(),
                "duration_ms": duration_ms
            })
            return {
                'date': date,
                'balance': 0,
                'daily_pnl': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0
            }
        
        metrics = {
            'date': date,
            'balance': perf.balance,
            'daily_pnl': perf.daily_pnl,
            'daily_pnl_pct': perf.daily_pnl_percent,
            'total_pnl': perf.total_pnl,
            'win_rate': perf.win_rate,
            'max_drawdown': perf.max_drawdown,
            'sharpe_ratio': perf.sharpe_ratio,
            'consecutive_losses': perf.consecutive_losses
        }
    
    def get_recent_returns(self, days: int = 30) -> np.ndarray:
        """Get recent trade returns.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Array of returns
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        trades = self.db.query(Trade).filter(
            Trade.timestamp >= cutoff_date,
            Trade.is_closed.is_(True),
            Trade.pnl_percent.isnot(None)
        ).all()
        
        if not trades:
            return np.array([])
        
        returns = np.array([t.pnl_percent / 100 for t in trades])
        return returns
    
    def calculate_all_metrics(self) -> Dict:
        """Calculate all risk metrics.
        
        Returns:
            Dict with comprehensive risk metrics
        """
        # Get recent returns
        returns = self.get_recent_returns(days=30)
        
        # Get all closed trades for equity curve
        all_trades = self.db.query(Trade).filter(
            Trade.is_closed.is_(True)
        ).order_by(Trade.timestamp).all()
        
        if not all_trades:
            return {
                'var_95': 0.0,
                'cvar_95': 0.0,
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0,
                'max_drawdown': 0.0,
                'num_trades': 0
            }
        
        # Build equity curve
        equity = [10000]  # Starting balance
        for trade in all_trades:
            equity.append(equity[-1] + trade.pnl)
        
        equity_series = pd.Series(equity)
        
        # Calculate metrics
        var_95 = self.calculate_var(returns, 0.95)
        cvar_95 = self.calculate_cvar(returns, 0.95)
        sharpe = self.calculate_sharpe_ratio(returns)
        sortino = self.calculate_sortino_ratio(returns)
        dd_metrics = self.calculate_max_drawdown(equity_series)
        
        metrics = {
            'var_95': var_95,
            'cvar_95': cvar_95,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'max_drawdown': dd_metrics['max_drawdown'],
            'max_drawdown_pct': dd_metrics['max_drawdown_pct'],
            'drawdown_duration_days': dd_metrics['duration'],
            'num_trades': len(all_trades),
            'current_equity': float(equity[-1])
        }
        
        logger.info("Risk metrics calculated", metrics=metrics)
        
        return metrics

