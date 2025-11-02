"""Multi-Timeframe Data Synchronization Service."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import pandas as pd

from src.core.config import trading_config
from src.core.logger import logger
from src.data.delta_client import DeltaExchangeClient
from src.data.feature_engineer import FeatureEngineer
from src.data.data_validator import DataValidator
from src.utils.timestamp import get_current_time_utc, format_timestamp


class MultiTimeframeDataSync:
    """Manages synchronized data fetching across multiple timeframes."""
    
    def __init__(self):
        """Initialize the data sync service."""
        self.delta_client = DeltaExchangeClient()
        self.feature_engineer = FeatureEngineer()
        self.validator = DataValidator()
        
        # Data storage with metadata
        self.data_store: Dict[str, Dict] = {}  # {symbol_timeframe: {df, timestamp, quality}}
        
        # Sync intervals (seconds)
        self.sync_intervals = {
            '15m': 60,    # Sync every 1 minute
            '1h': 300,    # Sync every 5 minutes
            '4h': 1800    # Sync every 30 minutes
        }
        
        # Last sync times
        self.last_sync: Dict[str, datetime] = {}
        
        # Configuration - handle both singular and plural symbol configs
        symbol_config = trading_config.trading.get('symbols', trading_config.trading.get('symbol', 'BTCUSD'))
        if isinstance(symbol_config, str):
            self.symbols = [symbol_config]
        else:
            self.symbols = symbol_config
        
        self.timeframes = ['15m', '1h', '4h']
        
        self.is_running = False
        self.sync_task = None
        
        logger.info(
            "MultiTimeframeDataSync initialized",
            symbols=self.symbols,
            timeframes=self.timeframes,
            sync_intervals=self.sync_intervals
        )
    
    def _get_cache_key(self, symbol: str, timeframe: str) -> str:
        """Generate cache key."""
        return f"{symbol}_{timeframe}"
    
    def _is_data_stale(self, symbol: str, timeframe: str) -> bool:
        """Check if data needs refreshing."""
        cache_key = self._get_cache_key(symbol, timeframe)
        
        if cache_key not in self.last_sync:
            return True
        
        last_sync_time = self.last_sync[cache_key]
        age = (get_current_time_utc() - last_sync_time).total_seconds()
        threshold = self.sync_intervals.get(timeframe, 300)
        
        return age >= threshold
    
    async def _fetch_and_store(self, symbol: str, timeframe: str):
        """Fetch data and store with metadata."""
        cache_key = self._get_cache_key(symbol, timeframe)
        
        try:
            # Fetch OHLC data
            df = self.delta_client.get_ohlc_candles(
                symbol=symbol,
                resolution=timeframe,
                limit=500
            )
            
            if df.empty:
                logger.warning(f"No data fetched for {symbol} {timeframe}")
                return False
            
            # Validate
            df, metrics = self.validator.validate_and_clean(df)
            
            if df.empty:
                logger.warning(f"Data validation failed for {symbol} {timeframe}")
                return False
            
            # Create features
            df = self.feature_engineer.create_features(df)
            
            if df.empty:
                logger.warning(f"Feature engineering failed for {symbol} {timeframe}")
                return False
            
            # Store with metadata
            self.data_store[cache_key] = {
                'df': df,
                'timestamp': get_current_time_utc(),
                'quality_score': metrics.get('quality_score', 0),
                'num_candles': len(df),
                'symbol': symbol,
                'timeframe': timeframe
            }
            
            self.last_sync[cache_key] = get_current_time_utc()
            
            logger.debug(
                f"Data synced",
                symbol=symbol,
                timeframe=timeframe,
                candles=len(df),
                quality=metrics.get('quality_score', 0)
            )
            
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to sync data for {symbol} {timeframe}",
                error=str(e)
            )
            return False
    
    async def sync_all(self):
        """Sync all symbol-timeframe combinations that are stale."""
        sync_count = 0
        
        for symbol in self.symbols:
            for timeframe in self.timeframes:
                if self._is_data_stale(symbol, timeframe):
                    success = await self._fetch_and_store(symbol, timeframe)
                    if success:
                        sync_count += 1
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.1)
        
        if sync_count > 0:
            logger.info(f"Synced {sync_count} timeframe datasets")
        
        return sync_count
    
    async def sync_loop(self):
        """Background sync loop."""
        logger.info("Multi-timeframe sync loop started")
        
        # Initial sync
        await self.sync_all()
        
        while self.is_running:
            try:
                # Check each timeframe independently
                for timeframe in self.timeframes:
                    interval = self.sync_intervals.get(timeframe, 300)
                    
                    for symbol in self.symbols:
                        if self._is_data_stale(symbol, timeframe):
                            await self._fetch_and_store(symbol, timeframe)
                
                # Wait 30 seconds before next check
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in sync loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait longer on error
    
    async def start(self):
        """Start the background sync service."""
        if self.is_running:
            logger.warning("Sync service already running")
            return
        
        self.is_running = True
        self.sync_task = asyncio.create_task(self.sync_loop())
        logger.info("Multi-timeframe sync service started")
    
    def stop(self):
        """Stop the background sync service."""
        self.is_running = False
        if self.sync_task:
            self.sync_task.cancel()
        logger.info("Multi-timeframe sync service stopped")
    
    def get_data(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Get data for a specific symbol and timeframe.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (15m, 1h, 4h)
            
        Returns:
            DataFrame with features or None if not available
        """
        cache_key = self._get_cache_key(symbol, timeframe)
        
        if cache_key not in self.data_store:
            logger.warning(f"No data available for {symbol} {timeframe}")
            return None
        
        data = self.data_store[cache_key]
        
        # Check freshness
        age = (get_current_time_utc() - data['timestamp']).total_seconds()
        max_age = self.sync_intervals.get(timeframe, 300) * 2  # Allow 2x interval
        
        if age > max_age:
            logger.warning(
                f"Data for {symbol} {timeframe} is stale",
                age_seconds=age,
                max_age=max_age
            )
        
        return data['df']
    
    def get_all_data(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """Get data for all timeframes for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary mapping timeframe to DataFrame
        """
        result = {}
        
        for timeframe in self.timeframes:
            df = self.get_data(symbol, timeframe)
            if df is not None:
                result[timeframe] = df
        
        return result
    
    def get_data_quality(self, symbol: str, timeframe: str) -> Dict:
        """Get quality metrics for cached data."""
        cache_key = self._get_cache_key(symbol, timeframe)
        
        if cache_key not in self.data_store:
            return {
                'available': False,
                'reason': 'not_cached'
            }
        
        data = self.data_store[cache_key]
        age = (get_current_time_utc() - data['timestamp']).total_seconds()
        
        return {
            'available': True,
            'quality_score': data['quality_score'],
            'num_candles': data['num_candles'],
            'age_seconds': age,
            'timestamp': format_timestamp(data['timestamp']),
            'is_fresh': age < self.sync_intervals.get(timeframe, 300)
        }
    
    def get_status(self) -> Dict:
        """Get sync service status."""
        status = {
            'is_running': self.is_running,
            'symbols': self.symbols,
            'timeframes': self.timeframes,
            'cached_datasets': len(self.data_store),
            'datasets': []
        }
        
        for cache_key, data in self.data_store.items():
            age = (get_current_time_utc() - data['timestamp']).total_seconds()
            status['datasets'].append({
                'key': cache_key,
                'symbol': data['symbol'],
                'timeframe': data['timeframe'],
                'age_seconds': age,
                'quality_score': data['quality_score'],
                'num_candles': data['num_candles']
            })
        
        return status
    
    def clear_cache(self):
        """Clear all cached data."""
        self.data_store.clear()
        self.last_sync.clear()
        logger.info("Data cache cleared")

