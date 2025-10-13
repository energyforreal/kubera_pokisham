"""Basic unit tests for core functionality."""

import sys
from pathlib import Path

import pytest
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data.feature_engineer import FeatureEngineer
from src.data.data_validator import DataValidator
from src.risk.position_sizer import PositionSizer
from src.risk.risk_manager import RiskManager


class TestFeatureEngineer:
    """Test feature engineering."""
    
    def test_create_features(self):
        """Test feature creation."""
        # Create sample OHLCV data
        dates = pd.date_range('2024-01-01', periods=300, freq='15T')
        df = pd.DataFrame({
            'timestamp': dates,
            'symbol': 'BTCUSDT',
            'timeframe': '15m',
            'open': np.random.uniform(40000, 45000, 300),
            'high': np.random.uniform(45000, 46000, 300),
            'low': np.random.uniform(39000, 40000, 300),
            'close': np.random.uniform(40000, 45000, 300),
            'volume': np.random.uniform(1000, 5000, 300)
        })
        
        engineer = FeatureEngineer()
        result = engineer.create_features(df)
        
        assert not result.empty
        assert 'rsi' in result.columns
        assert 'macd' in result.columns
        assert 'atr' in result.columns
        assert len(result.columns) > 20  # Should have many features


class TestDataValidator:
    """Test data validation."""
    
    def test_validate_clean_data(self):
        """Test data validation with clean data."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='15T'),
            'symbol': 'BTCUSDT',
            'timeframe': '15m',
            'open': np.random.uniform(40000, 45000, 100),
            'high': np.random.uniform(45000, 46000, 100),
            'low': np.random.uniform(39000, 40000, 100),
            'close': np.random.uniform(40000, 45000, 100),
            'volume': np.random.uniform(1000, 5000, 100)
        })
        
        validator = DataValidator()
        result, metrics = validator.validate_and_clean(df)
        
        assert not result.empty
        assert metrics['quality_score'] > 90  # Clean data should have high score
    
    def test_validate_dirty_data(self):
        """Test data validation with issues."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='15T'),
            'symbol': 'BTCUSDT',
            'timeframe': '15m',
            'open': [np.nan] * 10 + list(np.random.uniform(40000, 45000, 90)),
            'high': np.random.uniform(45000, 46000, 100),
            'low': np.random.uniform(39000, 40000, 100),
            'close': np.random.uniform(40000, 45000, 100),
            'volume': np.random.uniform(1000, 5000, 100)
        })
        
        validator = DataValidator()
        result, metrics = validator.validate_and_clean(df)
        
        assert not result.empty
        assert metrics['missing_data']['open'] == 10


class TestPositionSizer:
    """Test position sizing."""
    
    def test_fixed_fractional_sizing(self):
        """Test fixed fractional position sizing."""
        sizer = PositionSizer()
        
        size = sizer.calculate_position_size(
            balance=10000,
            risk_per_trade=0.02,
            confidence=1.0
        )
        
        assert size > 0
        assert size <= 10000 * 0.25  # Should not exceed max size
    
    def test_confidence_scaling(self):
        """Test that confidence scales position size."""
        sizer = PositionSizer()
        
        size_high = sizer.calculate_position_size(
            balance=10000,
            risk_per_trade=0.02,
            confidence=0.9
        )
        
        size_low = sizer.calculate_position_size(
            balance=10000,
            risk_per_trade=0.02,
            confidence=0.5
        )
        
        assert size_high > size_low


class TestRiskManager:
    """Test risk management."""
    
    def test_var_calculation(self):
        """Test VaR calculation."""
        returns = np.random.normal(0, 0.02, 1000)
        
        from src.core.database import SessionLocal
        db = SessionLocal()
        manager = RiskManager(db)
        
        var = manager.calculate_var(returns, 0.95)
        assert var < 0  # VaR should be negative
        
        db.close()
    
    def test_sharpe_ratio(self):
        """Test Sharpe ratio calculation."""
        returns = np.random.normal(0.001, 0.02, 252)  # Slightly positive returns
        
        from src.core.database import SessionLocal
        db = SessionLocal()
        manager = RiskManager(db)
        
        sharpe = manager.calculate_sharpe_ratio(returns)
        assert isinstance(sharpe, float)
        
        db.close()


def test_imports():
    """Test that all modules can be imported."""
    from src.core.config import settings, trading_config
    from src.core.database import init_db
    from src.data.delta_client import DeltaExchangeClient
    from src.ml.xgboost_model import XGBoostTradingModel
    from src.trading.paper_engine import PaperTradingEngine
    
    assert settings is not None
    assert trading_config is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

