"""Data quality validation and cleaning."""

from datetime import datetime, timedelta
from typing import Optional, Tuple

import numpy as np
import pandas as pd

from src.core.logger import logger


class DataValidator:
    """Validate and clean market data."""
    
    def __init__(self):
        self.quality_metrics = {}
    
    def validate_and_clean(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
        """Run all validation checks and clean data.
        
        Args:
            df: Raw OHLCV DataFrame
            
        Returns:
            Tuple of (cleaned DataFrame, quality metrics dict)
        """
        if df.empty:
            return df, {'status': 'empty'}
        
        original_count = len(df)
        metrics = {'original_count': original_count}
        
        # Check for missing data
        df, missing_stats = self._handle_missing_data(df)
        metrics['missing_data'] = missing_stats
        
        # Check for duplicates
        df, duplicate_count = self._remove_duplicates(df)
        metrics['duplicates_removed'] = duplicate_count
        
        # Validate timestamps
        df, timestamp_issues = self._validate_timestamps(df)
        metrics['timestamp_issues'] = timestamp_issues
        
        # Check for outliers
        df, outlier_stats = self._detect_outliers(df)
        metrics['outliers'] = outlier_stats
        
        # Validate OHLC relationships
        df, ohlc_errors = self._validate_ohlc(df)
        metrics['ohlc_errors'] = ohlc_errors
        
        # Volume validation
        df, volume_anomalies = self._validate_volume(df)
        metrics['volume_anomalies'] = volume_anomalies
        
        final_count = len(df)
        metrics['final_count'] = final_count
        metrics['rows_removed'] = original_count - final_count
        metrics['quality_score'] = self._calculate_quality_score(metrics)
        
        logger.info(
            "Data validation complete",
            original=original_count,
            final=final_count,
            removed=metrics['rows_removed'],
            quality_score=metrics['quality_score']
        )
        
        return df, metrics
    
    def _handle_missing_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
        """Handle missing data."""
        missing_stats = {}
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            missing_count = df[col].isna().sum()
            missing_stats[col] = missing_count
            
            if missing_count > 0:
                logger.warning(f"Missing data in {col}", count=missing_count)
                
                # Forward fill for price data
                if col != 'volume':
                    df[col] = df[col].fillna(method='ffill')
                else:
                    # Zero fill for volume
                    df[col] = df[col].fillna(0)
        
        # Drop rows that still have NaN
        rows_before = len(df)
        df = df.dropna(subset=['open', 'high', 'low', 'close'])
        rows_after = len(df)
        
        missing_stats['rows_dropped'] = rows_before - rows_after
        
        return df, missing_stats
    
    def _remove_duplicates(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """Remove duplicate timestamps."""
        duplicate_count = df.duplicated(subset=['timestamp', 'symbol', 'timeframe']).sum()
        
        if duplicate_count > 0:
            logger.warning("Duplicate timestamps found", count=duplicate_count)
            df = df.drop_duplicates(subset=['timestamp', 'symbol', 'timeframe'], keep='last')
        
        return df, duplicate_count
    
    def _validate_timestamps(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
        """Validate timestamp consistency."""
        issues = {}
        
        if 'timestamp' not in df.columns:
            return df, issues
        
        # Check for future timestamps
        now = datetime.utcnow()
        future_count = (df['timestamp'] > now).sum()
        if future_count > 0:
            logger.warning("Future timestamps detected", count=future_count)
            df = df[df['timestamp'] <= now]
            issues['future_timestamps'] = future_count
        
        # Check timestamp ordering
        if not df['timestamp'].is_monotonic_increasing:
            logger.warning("Timestamps not in order, sorting")
            df = df.sort_values('timestamp').reset_index(drop=True)
            issues['unsorted'] = True
        
        # Check for large gaps
        if len(df) > 1:
            time_diffs = df['timestamp'].diff()
            median_diff = time_diffs.median()
            large_gaps = (time_diffs > median_diff * 3).sum()
            if large_gaps > 0:
                logger.warning("Large time gaps detected", count=large_gaps)
                issues['large_gaps'] = large_gaps
        
        return df, issues
    
    def _detect_outliers(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
        """Detect and handle outliers using IQR method."""
        outlier_stats = {}
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col not in df.columns:
                continue
            
            # Calculate IQR
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            # Define outlier bounds
            lower_bound = Q1 - 3 * IQR
            upper_bound = Q3 + 3 * IQR
            
            # Count outliers
            outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
            outlier_stats[col] = outliers
            
            if outliers > 0:
                logger.warning(f"Outliers in {col}", count=outliers, bounds=(lower_bound, upper_bound))
                
                # Cap outliers instead of removing
                df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
        
        return df, outlier_stats
    
    def _validate_ohlc(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """Validate OHLC relationships (High >= Low, etc.)."""
        errors = 0
        
        # Check High >= Low
        invalid_hl = df['high'] < df['low']
        if invalid_hl.any():
            error_count = invalid_hl.sum()
            errors += error_count
            logger.warning("Invalid High/Low relationship", count=error_count)
            # Fix by swapping
            df.loc[invalid_hl, ['high', 'low']] = df.loc[invalid_hl, ['low', 'high']].values
        
        # Check Open, Close within High/Low range
        invalid_open = (df['open'] > df['high']) | (df['open'] < df['low'])
        invalid_close = (df['close'] > df['high']) | (df['close'] < df['low'])
        
        if invalid_open.any():
            error_count = invalid_open.sum()
            errors += error_count
            logger.warning("Open price outside High/Low range", count=error_count)
            df.loc[invalid_open, 'open'] = df.loc[invalid_open, 'close']
        
        if invalid_close.any():
            error_count = invalid_close.sum()
            errors += error_count
            logger.warning("Close price outside High/Low range", count=error_count)
            # Clip to range
            df.loc[invalid_close, 'close'] = df.loc[invalid_close, 'close'].clip(
                lower=df.loc[invalid_close, 'low'],
                upper=df.loc[invalid_close, 'high']
            )
        
        # Check for zero or negative prices
        price_cols = ['open', 'high', 'low', 'close']
        invalid_prices = (df[price_cols] <= 0).any(axis=1)
        if invalid_prices.any():
            error_count = invalid_prices.sum()
            errors += error_count
            logger.warning("Zero or negative prices", count=error_count)
            df = df[~invalid_prices]
        
        return df, errors
    
    def _validate_volume(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """Validate volume data."""
        anomalies = 0
        
        # Check for negative volume
        negative_vol = df['volume'] < 0
        if negative_vol.any():
            count = negative_vol.sum()
            anomalies += count
            logger.warning("Negative volume detected", count=count)
            df.loc[negative_vol, 'volume'] = 0
        
        # Check for extremely high volume (> 10x median)
        median_vol = df['volume'].median()
        if median_vol > 0:
            high_vol = df['volume'] > (median_vol * 10)
            if high_vol.any():
                count = high_vol.sum()
                anomalies += count
                logger.warning("Extremely high volume", count=count)
                # Cap at 10x median
                df.loc[high_vol, 'volume'] = median_vol * 10
        
        return df, anomalies
    
    def _calculate_quality_score(self, metrics: dict) -> float:
        """Calculate overall data quality score (0-100).
        
        Args:
            metrics: Quality metrics dictionary
            
        Returns:
            Quality score from 0 to 100
        """
        if metrics.get('original_count', 0) == 0:
            return 0.0
        
        original = metrics['original_count']
        final = metrics['final_count']
        
        # Base score from data retention
        retention_score = (final / original) * 100
        
        # Penalties for issues
        penalties = 0
        
        # Missing data penalty
        missing_total = sum(metrics.get('missing_data', {}).values())
        penalties += min((missing_total / original) * 20, 10)
        
        # Outlier penalty
        outlier_total = sum(metrics.get('outliers', {}).values())
        penalties += min((outlier_total / original) * 10, 5)
        
        # OHLC error penalty
        ohlc_errors = metrics.get('ohlc_errors', 0)
        penalties += min((ohlc_errors / original) * 15, 10)
        
        # Volume anomaly penalty
        volume_anomalies = metrics.get('volume_anomalies', 0)
        penalties += min((volume_anomalies / original) * 5, 5)
        
        # Calculate final score
        score = max(retention_score - penalties, 0)
        
        return round(score, 2)

