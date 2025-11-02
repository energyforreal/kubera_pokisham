"""Feature engineering module for creating technical indicators."""

from typing import List

import numpy as np
import pandas as pd
import talib

from src.core.config import trading_config
from src.core.logger import logger


class FeatureEngineer:
    """Create technical indicators and features for ML models."""
    
    def __init__(self):
        self.config = trading_config.features
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create all technical indicator features.
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            DataFrame with added features
        """
        if df.empty or len(df) < 200:
            logger.warning("Insufficient data for feature engineering", rows=len(df), minimum_required=200)
            # Return empty DataFrame to prevent invalid predictions
            return pd.DataFrame()
        
        df = df.copy()
        
        # Price-based features
        df = self._add_moving_averages(df)
        df = self._add_price_features(df)
        
        # Momentum indicators
        df = self._add_momentum_indicators(df)
        
        # Volatility indicators
        df = self._add_volatility_indicators(df)
        
        # Volume indicators
        df = self._add_volume_indicators(df)
        
        # Derived features
        df = self._add_derived_features(df)
        
        # Drop NaN values (from indicator calculation)
        df = df.dropna().reset_index(drop=True)
        
        logger.info("Features created", total_features=len(df.columns), rows=len(df))
        
        return df
    
    def _add_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Simple and Exponential Moving Averages."""
        # SMA
        for period in self.config.get('sma_periods', [10, 20, 50, 100, 200]):
            df[f'sma_{period}'] = talib.SMA(df['close'], timeperiod=period)
        
        # EMA
        for period in self.config.get('ema_periods', [9, 12, 26, 50]):
            df[f'ema_{period}'] = talib.EMA(df['close'], timeperiod=period)
        
        # VWAP (Volume Weighted Average Price)
        df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
        
        return df
    
    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add price-based features."""
        # Price changes
        df['price_change'] = df['close'].pct_change()
        df['price_change_abs'] = df['close'].diff()
        
        # High-Low range
        df['hl_range'] = df['high'] - df['low']
        df['hl_range_pct'] = (df['high'] - df['low']) / df['close']
        
        # Close position in range
        df['close_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])
        
        # Typical price
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        
        # Bollinger Bands
        bb_period = self.config.get('bollinger_period', 20)
        bb_std = self.config.get('bollinger_std', 2)
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
            df['close'],
            timeperiod=bb_period,
            nbdevup=bb_std,
            nbdevdn=bb_std
        )
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        return df
    
    def _add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum indicators."""
        # RSI
        rsi_period = self.config.get('rsi_period', 14)
        df['rsi'] = talib.RSI(df['close'], timeperiod=rsi_period)
        
        # MACD
        macd_fast = self.config.get('macd_fast', 12)
        macd_slow = self.config.get('macd_slow', 26)
        macd_signal = self.config.get('macd_signal', 9)
        df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(
            df['close'],
            fastperiod=macd_fast,
            slowperiod=macd_slow,
            signalperiod=macd_signal
        )
        
        # Stochastic
        stoch_period = self.config.get('stoch_period', 14)
        df['stoch_k'], df['stoch_d'] = talib.STOCH(
            df['high'],
            df['low'],
            df['close'],
            fastk_period=stoch_period,
            slowk_period=3,
            slowd_period=3
        )
        
        # Williams %R
        df['willr'] = talib.WILLR(df['high'], df['low'], df['close'], timeperiod=14)
        
        # Rate of Change
        df['roc'] = talib.ROC(df['close'], timeperiod=10)
        
        # Momentum
        df['momentum'] = talib.MOM(df['close'], timeperiod=10)
        
        # CCI (Commodity Channel Index)
        df['cci'] = talib.CCI(df['high'], df['low'], df['close'], timeperiod=20)
        
        return df
    
    def _add_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility indicators."""
        # ATR (Average True Range)
        atr_period = self.config.get('atr_period', 14)
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=atr_period)
        df['atr_pct'] = df['atr'] / df['close']
        
        # NATR (Normalized ATR)
        df['natr'] = talib.NATR(df['high'], df['low'], df['close'], timeperiod=atr_period)
        
        # Historical volatility
        df['volatility'] = df['price_change'].rolling(window=20).std()
        
        return df
    
    def _add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume indicators."""
        if self.config.get('obv_enabled', True):
            # OBV (On-Balance Volume)
            df['obv'] = talib.OBV(df['close'], df['volume'])
            
        # Volume SMA
        vol_period = self.config.get('volume_sma_period', 20)
        df['volume_sma'] = talib.SMA(df['volume'], timeperiod=vol_period)
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Money Flow Index
        df['mfi'] = talib.MFI(df['high'], df['low'], df['close'], df['volume'], timeperiod=14)
        
        # Accumulation/Distribution
        df['ad'] = talib.AD(df['high'], df['low'], df['close'], df['volume'])
        
        return df
    
    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features and ratios."""
        # Price to MA ratios
        for period in [20, 50, 200]:
            if f'sma_{period}' in df.columns:
                df[f'price_to_sma_{period}'] = df['close'] / df[f'sma_{period}']
        
        # MA crossovers
        if 'sma_20' in df.columns and 'sma_50' in df.columns:
            df['sma_20_50_diff'] = df['sma_20'] - df['sma_50']
            df['sma_20_50_cross'] = np.where(df['sma_20'] > df['sma_50'], 1, -1)
        
        # RSI levels
        if 'rsi' in df.columns:
            df['rsi_overbought'] = np.where(df['rsi'] > 70, 1, 0)
            df['rsi_oversold'] = np.where(df['rsi'] < 30, 1, 0)
        
        # MACD signal
        if 'macd' in df.columns and 'macd_signal' in df.columns:
            df['macd_cross'] = np.where(df['macd'] > df['macd_signal'], 1, -1)
        
        # Trend strength
        if 'ema_12' in df.columns and 'ema_26' in df.columns:
            df['trend_strength'] = (df['ema_12'] - df['ema_26']) / df['close']
        
        return df
    
    def get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """Get list of feature columns (excluding OHLCV and metadata).
        
        Args:
            df: DataFrame with features
            
        Returns:
            List of feature column names
        """
        exclude_cols = ['timestamp', 'symbol', 'timeframe', 'open', 'high', 'low', 'close', 'volume']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        return feature_cols
    
    def prepare_for_model(self, df: pd.DataFrame, target_col: str = 'target') -> tuple:
        """Prepare features and target for model training.
        
        Args:
            df: DataFrame with features and target
            target_col: Name of target column
            
        Returns:
            Tuple of (features DataFrame, target Series, feature names)
        """
        feature_cols = self.get_feature_columns(df)
        
        # Remove target from features if present
        if target_col in feature_cols:
            feature_cols.remove(target_col)
        
        X = df[feature_cols].copy()
        y = df[target_col].copy() if target_col in df.columns else None
        
        # Replace inf with nan and fill
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.ffill().fillna(0)
        
        return X, y, feature_cols

