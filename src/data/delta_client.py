"""Delta Exchange API client for fetching market data."""

import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import pandas as pd
import requests
from requests.exceptions import RequestException

from src.core.config import settings
from src.core.logger import logger
from src.utils.retry import retry_with_backoff


class DeltaExchangeClient:
    """Client for interacting with Delta Exchange API."""
    
    def __init__(self):
        self.api_key = settings.delta_api_key
        self.api_secret = settings.delta_api_secret
        self.base_url = settings.delta_api_url
        self.session = requests.Session()
        
    def _generate_signature(self, method: str, endpoint: str, payload: str = "") -> str:
        """Generate HMAC signature for authenticated requests."""
        timestamp = str(int(time.time()))
        signature_data = method + timestamp + endpoint + payload
        signature = hmac.new(
            self.api_secret.encode(),
            signature_data.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature, timestamp
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0, exceptions=(RequestException, ConnectionError))
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        authenticated: bool = False
    ) -> Dict:
        """Make HTTP request to Delta Exchange API with automatic retry."""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if authenticated:
            payload = ""
            signature, timestamp = self._generate_signature(method, endpoint, payload)
            headers.update({
                "api-key": self.api_key,
                "signature": signature,
                "timestamp": timestamp
            })
        
        try:
            logger.debug(f"API request", method=method, endpoint=endpoint)
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            logger.debug(f"API request successful", endpoint=endpoint, status=response.status_code)
            return response.json()
        except RequestException as e:
            logger.error("API request failed", error=str(e), endpoint=endpoint, url=url)
            raise
    
    def get_ohlc_candles(
        self,
        symbol: str,
        resolution: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 500
    ) -> pd.DataFrame:
        """Fetch OHLC candlestick data.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSD')
            resolution: Candle resolution ('1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '1d')
            start: Start datetime
            end: End datetime
            limit: Maximum number of candles to fetch
            
        Returns:
            DataFrame with OHLC data
        """
        # Ensure resolution is in string format (Delta Exchange India requires this)
        # Convert numeric to string if needed
        resolution_map = {
            '1': '1m', '3': '3m', '5': '5m', '15': '15m', '30': '30m',
            '60': '1h', '120': '2h', '240': '4h', '360': '6h',
            '1440': '1d', '1D': '1d'
        }
        resolution = resolution_map.get(resolution, resolution)
        
        # Ensure resolution is lowercase for consistency
        resolution = resolution.lower()
        
        params = {
            'resolution': resolution,
            'symbol': symbol,
        }
        
        # Get current timestamp
        current_time = int(time.time())
        
        # Handle end timestamp - ensure it's not in the future
        if end:
            end_timestamp = int(end.timestamp())
            if end_timestamp > current_time:
                end_timestamp = current_time
                logger.warning("End date in future, using current time", 
                             requested=end, current=datetime.fromtimestamp(current_time))
            params['end'] = end_timestamp
        else:
            params['end'] = current_time
        
        # Handle start timestamp
        if start:
            start_timestamp = int(start.timestamp())
            # BTCUSD launched on Dec 18, 2023
            launch_timestamp = 1702905039
            if start_timestamp < launch_timestamp:
                start_timestamp = launch_timestamp
                logger.warning("Start date before BTCUSD launch, using launch date",
                             requested=start, launch_date=datetime.fromtimestamp(launch_timestamp))
            params['start'] = start_timestamp
        else:
            # Default to last 'limit' candles
            if resolution == '1d':
                start = datetime.utcnow() - timedelta(days=limit)
            else:
                # Extract minutes from resolution string
                if 'm' in resolution:
                    minutes = int(resolution.replace('m', ''))
                elif 'h' in resolution:
                    minutes = int(resolution.replace('h', '')) * 60
                else:
                    minutes = 1440
                start = datetime.utcnow() - timedelta(minutes=minutes * limit)
            params['start'] = int(start.timestamp())
        
        try:
            endpoint = "/v2/history/candles"
            response = self._make_request("GET", endpoint, params=params)
            
            if not response.get('success') or not response.get('result'):
                logger.warning("No candle data returned", symbol=symbol, resolution=resolution)
                return pd.DataFrame()
            
            candles = response['result']
            
            # Convert to DataFrame
            df = pd.DataFrame(candles)
            
            if df.empty:
                return df
            
            # Rename columns
            column_map = {
                'time': 'timestamp',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            }
            df = df.rename(columns=column_map)
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            
            # Add symbol and timeframe
            df['symbol'] = symbol
            df['timeframe'] = resolution
            
            # Select and order columns
            df = df[['timestamp', 'symbol', 'timeframe', 'open', 'high', 'low', 'close', 'volume']]
            
            # Sort by timestamp
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            logger.info(
                "Fetched candle data",
                symbol=symbol,
                resolution=resolution,
                count=len(df),
                start=df['timestamp'].min(),
                end=df['timestamp'].max()
            )
            
            return df
            
        except Exception as e:
            logger.error("Failed to fetch candles", error=str(e), symbol=symbol, resolution=resolution)
            return pd.DataFrame()
    
    def get_ticker(self, symbol: str) -> Dict:
        """Get current ticker data for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Ticker data dictionary
        """
        try:
            endpoint = f"/v2/tickers/{symbol}"
            response = self._make_request("GET", endpoint)
            
            if response.get('success') and response.get('result'):
                return response['result']
            return {}
            
        except Exception as e:
            logger.error("Failed to fetch ticker", error=str(e), symbol=symbol)
            return {}
    
    def get_account_balance(self) -> Dict:
        """Get account balance (for authenticated requests).
        
        Returns:
            Account balance data
        """
        try:
            endpoint = "/v2/wallet/balances"
            response = self._make_request("GET", endpoint, authenticated=True)
            
            if response.get('success') and response.get('result'):
                return response['result']
            return {}
            
        except Exception as e:
            logger.error("Failed to fetch account balance", error=str(e))
            return {}

