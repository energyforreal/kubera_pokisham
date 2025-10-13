"""Download historical data from Delta Exchange."""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.database import SessionLocal, OHLCVData, init_db
from src.core.logger import logger
from src.data.delta_client import DeltaExchangeClient
from src.data.data_validator import DataValidator


def download_and_save_data(symbol: str, timeframe: str, days: int):
    """Download and save historical data.
    
    Args:
        symbol: Trading symbol
        timeframe: Candle timeframe
        days: Number of days to download
    """
    logger.info(f"Downloading data for {symbol} ({timeframe}), last {days} days")
    
    # Initialize components
    client = DeltaExchangeClient()
    validator = DataValidator()
    db = SessionLocal()
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    try:
        # Fetch data
        df = client.get_ohlc_candles(
            symbol=symbol,
            resolution=timeframe,
            start=start_date,
            end=end_date,
            limit=days * 100
        )
        
        if df.empty:
            logger.error("No data fetched")
            return
        
        logger.info(f"Fetched {len(df)} candles")
        
        # Validate data
        df, metrics = validator.validate_and_clean(df)
        logger.info(f"Data quality score: {metrics.get('quality_score', 0):.2f}")
        
        # Save to database
        for _, row in df.iterrows():
            candle = OHLCVData(
                timestamp=row['timestamp'],
                symbol=row['symbol'],
                timeframe=row['timeframe'],
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume']
            )
            db.add(candle)
        
        db.commit()
        logger.info(f"✅ Saved {len(df)} candles to database")
        
        # Also save to CSV
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        csv_path = data_dir / f"{symbol}_{timeframe}_{days}d.csv"
        df.to_csv(csv_path, index=False)
        logger.info(f"✅ Saved to {csv_path}")
        
    except Exception as e:
        logger.error(f"Error downloading data: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Download historical data from Delta Exchange')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--timeframe', type=str, default='15m', help='Timeframe (15m, 1h, 4h, 1d)')
    parser.add_argument('--days', type=int, default=365, help='Number of days to download')
    
    args = parser.parse_args()
    
    # Initialize database
    init_db()
    
    # Download data
    download_and_save_data(args.symbol, args.timeframe, args.days)


if __name__ == "__main__":
    main()

