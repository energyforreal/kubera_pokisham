"""
Test Delta Exchange API Connection
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.data.delta_client import DeltaExchangeClient
from src.core.config import settings

def test_delta_connection():
    """Test Delta Exchange API connection and credentials."""
    
    print("=" * 70)
    print("           DELTA EXCHANGE CONNECTION TEST")
    print("=" * 70)
    print()
    
    # Check if credentials are loaded
    print("[STEP 1/4] Checking credentials...")
    print("-" * 70)
    
    api_key_loaded = bool(settings.delta_api_key and settings.delta_api_key != "")
    api_secret_loaded = bool(settings.delta_api_secret and settings.delta_api_secret != "")
    
    print(f"API URL: {settings.delta_api_url}")
    print(f"API Key loaded: {'[YES]' if api_key_loaded else '[NO - empty or missing]'}")
    print(f"API Secret loaded: {'[YES]' if api_secret_loaded else '[NO - empty or missing]'}")
    
    if not api_key_loaded or not api_secret_loaded:
        print()
        print("[ERROR] Delta Exchange credentials not found!")
        print()
        print("Please create a .env file in the config/ folder with:")
        print()
        print("  DELTA_API_KEY=your_api_key_here")
        print("  DELTA_API_SECRET=your_api_secret_here")
        print("  DELTA_API_URL=https://api.india.delta.exchange")
        print()
        print("See config/env.example for reference.")
        print()
        return False
    
    print()
    
    # Initialize client
    print("[STEP 2/4] Initializing Delta Exchange client...")
    print("-" * 70)
    
    try:
        client = DeltaExchangeClient()
        print("[SUCCESS] Client initialized successfully")
    except Exception as e:
        print(f"[FAILED] Failed to initialize client: {e}")
        return False
    
    print()
    
    # Test ticker fetch
    print("[STEP 3/4] Testing ticker fetch for BTCUSD...")
    print("-" * 70)
    
    try:
        ticker = client.get_ticker("BTCUSD")
        
        if ticker:
            print("[SUCCESS] Ticker fetch successful!")
            print()
            print(f"  Symbol: {ticker.get('symbol', 'N/A')}")
            print(f"  Current Price: ${ticker.get('close', 'N/A')}")
            print(f"  24h Change: {ticker.get('change_24h', 'N/A')}%")
            print(f"  24h Volume: {ticker.get('volume', 'N/A')}")
            print(f"  High: ${ticker.get('high', 'N/A')}")
            print(f"  Low: ${ticker.get('low', 'N/A')}")
        else:
            print("[FAILED] Ticker fetch returned empty response")
            print("   This might indicate:")
            print("   - Invalid API credentials")
            print("   - Network connectivity issues")
            print("   - Delta Exchange API is down")
            return False
            
    except Exception as e:
        print(f"[FAILED] Ticker fetch failed: {e}")
        return False
    
    print()
    
    # Test OHLC candles fetch
    print("[STEP 4/4] Testing OHLC candles fetch...")
    print("-" * 70)
    
    try:
        df = client.get_ohlc_candles("BTCUSD", "15m", limit=10)
        
        if not df.empty:
            print(f"[SUCCESS] OHLC fetch successful!")
            print()
            print(f"  Candles fetched: {len(df)}")
            print(f"  Timeframe: 15 minutes")
            print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            print()
            print("  Latest candle:")
            latest = df.iloc[-1]
            print(f"    Time: {latest['timestamp']}")
            print(f"    Open: ${latest['open']}")
            print(f"    High: ${latest['high']}")
            print(f"    Low: ${latest['low']}")
            print(f"    Close: ${latest['close']}")
            print(f"    Volume: {latest['volume']}")
        else:
            print("[FAILED] OHLC fetch returned empty DataFrame")
            return False
            
    except Exception as e:
        print(f"[FAILED] OHLC fetch failed: {e}")
        return False
    
    print()
    print("=" * 70)
    print("           [SUCCESS] ALL TESTS PASSED!")
    print("=" * 70)
    print()
    print("Delta Exchange integration is working correctly!")
    print("Your trading bot can now fetch live market data.")
    print()
    
    return True


if __name__ == "__main__":
    success = test_delta_connection()
    sys.exit(0 if success else 1)

