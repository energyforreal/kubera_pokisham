"""Download historical data for trading agent."""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.delta_client import DeltaExchangeClient
from src.core.database import SessionLocal, OHLCVData
from src.core.logger import logger
from sqlalchemy import text


def download_historical_data(
    symbols=None, 
    timeframes=None, 
    days_back=30
):
    """
    Download historical market data.
    
    Args:
        symbols: List of trading symbols (default: ['BTCUSD'])
        timeframes: List of timeframes (default: ['15m', '1h', '4h'])
        days_back: Number of days of historical data to download (default: 30)
    """
    if symbols is None:
        symbols = ['BTCUSD']
    
    if timeframes is None:
        timeframes = ['15m', '1h', '4h']
    
    client = DeltaExchangeClient()
    db = SessionLocal()
    
    try:
        total_downloaded = 0
        
        print("\n" + "="*60)
        print("📥 HISTORICAL DATA DOWNLOAD")
        print("="*60)
        print(f"Symbols: {', '.join(symbols)}")
        print(f"Timeframes: {', '.join(timeframes)}")
        print(f"Period: Last {days_back} days")
        print("="*60 + "\n")
        
        for symbol in symbols:
            for timeframe in timeframes:
                print(f"📊 Downloading {symbol} {timeframe}...", end=" ")
                
                try:
                    # Calculate how many candles we need
                    # For 15m: 96 candles/day * days_back
                    # For 1h: 24 candles/day * days_back
                    # For 4h: 6 candles/day * days_back
                    candles_per_day = {
                        '15m': 96,
                        '1h': 24,
                        '4h': 6,
                        '1d': 1
                    }
                    
                    limit = candles_per_day.get(timeframe, 24) * days_back
                    limit = min(limit, 2000)  # API limit
                    
                    # Download data
                    df = client.get_ohlc_candles(
                        symbol=symbol,
                        resolution=timeframe,
                        limit=limit
                    )
                    
                    if df is None or df.empty:
                        print("❌ No data")
                        logger.warning(f"No data for {symbol} {timeframe}")
                        continue
                    
                    # Store in database (use raw SQL for flexibility with timestamp/time column)
                    new_records = 0
                    updated_records = 0
                    
                    for _, row in df.iterrows():
                        try:
                            # Use raw SQL with time column (after schema fix)
                            result = db.execute(
                                text("SELECT id FROM ohlcv_data WHERE symbol = :symbol AND timeframe = :timeframe AND time = :time"),
                                {"symbol": symbol, "timeframe": timeframe, "time": str(row['timestamp'])}
                            ).fetchone()
                            
                            if result:
                                # Update existing record
                                db.execute(
                                    text("UPDATE ohlcv_data SET open = :open, high = :high, low = :low, close = :close, volume = :volume WHERE id = :id"),
                                    {"open": float(row['open']), "high": float(row['high']), "low": float(row['low']), 
                                     "close": float(row['close']), "volume": float(row['volume']), "id": result[0]}
                                )
                                updated_records += 1
                            else:
                                # Insert new record using time column (after schema fix)
                                db.execute(
                                    text("INSERT INTO ohlcv_data (symbol, timeframe, time, open, high, low, close, volume) VALUES (:symbol, :timeframe, :time, :open, :high, :low, :close, :volume)"),
                                    {"symbol": symbol, "timeframe": timeframe, "time": str(row['timestamp']), 
                                     "open": float(row['open']), "high": float(row['high']), 
                                     "low": float(row['low']), "close": float(row['close']), "volume": float(row['volume'])}
                                )
                                new_records += 1
                        except Exception as e:
                            logger.error(f"Failed to store candle", error=str(e), symbol=symbol, timeframe=timeframe, time=row['timestamp'])
                            continue
                    
                    db.commit()
                    
                    print(f"✅ {len(df)} candles ({new_records} new, {updated_records} updated)")
                    logger.info(
                        f"Downloaded {symbol} {timeframe}",
                        candles=len(df),
                        new=new_records,
                        updated=updated_records
                    )
                    
                    total_downloaded += new_records
                    
                except Exception as e:
                    print(f"❌ Error: {str(e)}")
                    logger.error(f"Failed to download {symbol} {timeframe}", error=str(e))
                    db.rollback()
        
        print("\n" + "="*60)
        print(f"✅ Download complete! Total new records: {total_downloaded}")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Historical data download failed", error=str(e), exc_info=True)
        print(f"\n❌ Download failed: {str(e)}\n")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Download historical trading data')
    parser.add_argument(
        '--symbols',
        nargs='+',
        help='Trading symbols (default: BTCUSD)',
        default=['BTCUSD']
    )
    parser.add_argument(
        '--timeframes',
        nargs='+',
        help='Timeframes (default: 15m 1h 4h)',
        default=['15m', '1h', '4h']
    )
    parser.add_argument(
        '--days',
        type=int,
        help='Number of days to download (default: 30)',
        default=30
    )
    
    args = parser.parse_args()
    
    download_historical_data(
        symbols=args.symbols,
        timeframes=args.timeframes,
        days_back=args.days
    )

