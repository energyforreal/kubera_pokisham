"""Automatic data synchronization service to maintain database freshness."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.database import SessionLocal, OHLCVData
from src.data.delta_client import DeltaExchangeClient
from src.core.logger import logger
from src.core.config import trading_config


class DataSyncService:
    """Service to automatically sync fresh data from Delta Exchange."""
    
    def __init__(self):
        self.delta_client = DeltaExchangeClient()
        self.db = SessionLocal()
        
        # Load configuration
        sync_config = trading_config.data.get('sync', {})
        self.sync_interval = sync_config.get('interval', 3600)  # Default 1 hour
        self.symbols = sync_config.get('symbols', ['BTCUSD'])
        self.timeframes = sync_config.get('timeframes', ['4h'])
        self.batch_size = sync_config.get('batch_size', 1000)
        self.retry_attempts = sync_config.get('retry_attempts', 3)
        self.retry_delay = sync_config.get('retry_delay', 300)
        self.is_running = False
        
    async def start_sync(self):
        """Start the data synchronization service."""
        self.is_running = True
        logger.info("Data synchronization service started")
        
        while self.is_running:
            try:
                await self.sync_latest_data()
                await asyncio.sleep(self.sync_interval)
            except Exception as e:
                logger.error("Data sync error", error=str(e))
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def sync_latest_data(self):
        """Sync the latest data for all configured symbols and timeframes."""
        for symbol in self.symbols:
            for timeframe in self.timeframes:
                try:
                    await self.sync_symbol_timeframe(symbol, timeframe)
                except Exception as e:
                    logger.error(f"Failed to sync {symbol} {timeframe}", error=str(e))
    
    async def sync_symbol_timeframe(self, symbol: str, timeframe: str):
        """Sync data for a specific symbol and timeframe."""
        # Get the latest timestamp in database
        latest_timestamp = self.get_latest_timestamp(symbol, timeframe)
        
        if latest_timestamp:
            # Fetch data from latest timestamp to now
            start_time = latest_timestamp + timedelta(seconds=1)
            end_time = datetime.now(timezone.utc)
        else:
            # No data exists, fetch last 7 days
            start_time = datetime.now(timezone.utc) - timedelta(days=7)
            end_time = datetime.now(timezone.utc)
        
        # Fetch fresh data from Delta Exchange
        df = self.delta_client.get_ohlc_candles(
            symbol=symbol,
            resolution=timeframe,
            start=start_time,
            end=end_time,
            limit=self.batch_size
        )
        
        if not df.empty:
            # Store new data in database
            await self.store_candles(df, symbol, timeframe)
            logger.info(f"Synced {len(df)} new candles for {symbol} {timeframe}")
    
    def get_latest_timestamp(self, symbol: str, timeframe: str) -> Optional[datetime]:
        """Get the latest timestamp for a symbol/timeframe in database."""
        from sqlalchemy import func
        
        result = self.db.query(func.max(OHLCVData.time)).filter(
            OHLCVData.symbol == symbol,
            OHLCVData.timeframe == timeframe
        ).scalar()
        
        return result  # ORM automatically handles type conversion
    
    async def store_candles(self, df: pd.DataFrame, symbol: str, timeframe: str):
        """Store new candles in database with deduplication."""
        new_records = 0
        updated_records = 0
        
        for _, row in df.iterrows():
            try:
                # Check if record exists
                result = self.db.execute(
                    text("SELECT id FROM ohlcv_data WHERE symbol = :symbol AND timeframe = :timeframe AND time = :time"),
                    {"symbol": symbol, "timeframe": timeframe, "time": str(row['timestamp'])}
                ).fetchone()
                
                if result:
                    # Update existing record
                    self.db.execute(
                        text("UPDATE ohlcv_data SET open = :open, high = :high, low = :low, close = :close, volume = :volume WHERE id = :id"),
                        {"open": float(row['open']), "high": float(row['high']), "low": float(row['low']), 
                         "close": float(row['close']), "volume": float(row['volume']), "id": result[0]}
                    )
                    updated_records += 1
                else:
                    # Insert new record
                    self.db.execute(
                        text("INSERT INTO ohlcv_data (symbol, timeframe, time, open, high, low, close, volume) VALUES (:symbol, :timeframe, :time, :open, :high, :low, :close, :volume)"),
                        {"symbol": symbol, "timeframe": timeframe, "time": str(row['timestamp']), 
                         "open": float(row['open']), "high": float(row['high']), 
                         "low": float(row['low']), "close": float(row['close']), "volume": float(row['volume'])}
                    )
                    new_records += 1
            except Exception as e:
                logger.error(f"Failed to store candle", error=str(e), symbol=symbol, timeframe=timeframe, time=row['timestamp'])
                continue
        
        self.db.commit()
        logger.info(f"Stored {new_records} new, {updated_records} updated candles for {symbol} {timeframe}")
    
    def stop_sync(self):
        """Stop the data synchronization service."""
        self.is_running = False
        self.close()
        logger.info("Data synchronization service stopped")
    
    def close(self):
        """Close database session and cleanup resources."""
        if hasattr(self, 'db') and self.db:
            try:
                self.db.close()
                logger.debug("DataSyncService database session closed")
            except Exception as e:
                logger.warning(f"Error closing DataSyncService database session: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.close()
    
    def get_sync_status(self) -> Dict:
        """Get current synchronization status."""
        return {
            "is_running": self.is_running,
            "sync_interval": self.sync_interval,
            "last_sync": datetime.now(timezone.utc).isoformat() if self.is_running else None
        }
