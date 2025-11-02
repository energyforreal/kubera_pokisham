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
from src.core.logger import logger, get_component_logger
from src.utils.retry import retry_with_backoff


class DeltaExchangeClient:
    """Client for interacting with Delta Exchange API."""
    
    def __init__(self):
        # Initialize component logger
        self.logger = get_component_logger("delta_client")
        
        self.api_key = settings.delta_api_key
        self.api_secret = settings.delta_api_secret
        self.base_url = settings.delta_api_url
        self.session = requests.Session()
        
        self.logger.info("initialization", "Delta Exchange client initialized", {"base_url": self.base_url})
        
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
        limit: int = 500,
        use_pagination: bool = True
    ) -> pd.DataFrame:
        """Fetch OHLC candlestick data with automatic pagination.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSD')
            resolution: Candle resolution ('1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '1d')
            start: Start datetime
            end: End datetime
            limit: Maximum number of candles to fetch (may require multiple API calls)
            use_pagination: If True, automatically paginate to fetch more than 2000 candles
            
        Returns:
            DataFrame with OHLC data
            
        Note:
            Delta Exchange API returns max ~2000 candles per request.
            Set use_pagination=True to automatically fetch more data.
        """
        request_start_time = time.time()
        self.logger.info("api_request", f"Fetching OHLC candles for {symbol}", {
            "symbol": symbol,
            "resolution": resolution,
            "limit": limit,
            "use_pagination": use_pagination
        })
        
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
            if isinstance(start, datetime):
                start_timestamp = int(start.timestamp())
            else:
                start_timestamp = int(start)
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
                start = datetime.now(timezone.utc) - timedelta(days=limit)
            else:
                # Extract minutes from resolution string
                if 'm' in resolution:
                    minutes = int(resolution.replace('m', ''))
                elif 'h' in resolution:
                    minutes = int(resolution.replace('h', '')) * 60
                else:
                    minutes = 1440
                start = datetime.now(timezone.utc) - timedelta(minutes=minutes * limit)
            params['start'] = int(start.timestamp())
        
        try:
            endpoint = "/v2/history/candles"
            
            # Delta Exchange returns max ~2000 candles per request
            # If limit > 2000 and use_pagination=True, fetch in batches
            MAX_CANDLES_PER_REQUEST = 2000
            all_candles = []
            
            if use_pagination and limit > MAX_CANDLES_PER_REQUEST:
                logger.info(f"Fetching {limit} candles with pagination", 
                           symbol=symbol, resolution=resolution)
                
                # Calculate number of batches needed
                batches_needed = (limit + MAX_CANDLES_PER_REQUEST - 1) // MAX_CANDLES_PER_REQUEST
                current_end = params['end']
                
                for batch in range(batches_needed):
                    batch_params = params.copy()
                    batch_params['end'] = current_end
                    
                    response = self._make_request("GET", endpoint, params=batch_params)
                    
                    if not response.get('success') or not response.get('result'):
                        logger.warning("No more candle data available", 
                                     symbol=symbol, batch=batch+1)
                        break
                    
                    batch_candles = response['result']
                    if not batch_candles:
                        break
                        
                    all_candles.extend(batch_candles)
                    
                    # Update end time to earliest timestamp from this batch for next iteration
                    if batch_candles:
                        earliest_time = min(c['time'] for c in batch_candles)
                        current_end = earliest_time - 1  # Go 1 second earlier
                    
                    # Stop if we have enough candles
                    if len(all_candles) >= limit:
                        break
                    
                    # Respect rate limits - small delay between requests
                    if batch < batches_needed - 1:
                        time.sleep(0.2)  # 200ms delay
                
                candles = all_candles[:limit]  # Trim to requested limit
            else:
                # Single request for <= 2000 candles
                response = self._make_request("GET", endpoint, params=params)
                
                if not response.get('success') or not response.get('result'):
                    logger.warning("No candle data returned", symbol=symbol, resolution=resolution)
                    return pd.DataFrame()
                
                candles = response['result']
            
            # Convert to DataFrame
            df = pd.DataFrame(candles)
            
            if df.empty:
                duration_ms = (time.time() - request_start_time) * 1000
                self.logger.warning("api_response", f"No candles returned for {symbol}", {
                    "symbol": symbol,
                    "resolution": resolution,
                    "duration_ms": duration_ms
                })
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
            if df['timestamp'].dtype == 'object':
                # If timestamp is already a datetime string, parse it directly
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            else:
                # If timestamp is numeric (seconds since epoch), convert with unit='s'
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            
            # Add symbol and timeframe
            df['symbol'] = symbol
            df['timeframe'] = resolution
            
            # Select and order columns
            df = df[['timestamp', 'symbol', 'timeframe', 'open', 'high', 'low', 'close', 'volume']]
            
            # Sort by timestamp
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            duration_ms = (time.time() - request_start_time) * 1000
            self.logger.info("api_response", f"Successfully fetched candles for {symbol}", {
                "symbol": symbol,
                "resolution": resolution,
                "count": len(df),
                "start": df['timestamp'].min().isoformat() if not df.empty else None,
                "end": df['timestamp'].max().isoformat() if not df.empty else None,
                "duration_ms": duration_ms
            })
            
            return df
            
        except Exception as e:
            duration_ms = (time.time() - request_start_time) * 1000
            self.logger.error("api_error", f"Failed to fetch candles for {symbol}", {
                "symbol": symbol,
                "resolution": resolution,
                "error": str(e),
                "duration_ms": duration_ms
            }, error=e)
            return pd.DataFrame()
    
    def get_ticker(self, symbol: str) -> Dict:
        """Get current ticker data for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Ticker data dictionary
        """
        try:
            request_start_time = time.time()
            self.logger.info("api_request", f"Fetching ticker for {symbol}", {"symbol": symbol})
            
            endpoint = f"/v2/tickers/{symbol}"
            response = self._make_request("GET", endpoint)
            
            duration_ms = (time.time() - request_start_time) * 1000
            
            if response.get('success') and response.get('result'):
                ticker_data = response['result']
                self.logger.info("api_response", f"Successfully fetched ticker for {symbol}", {
                    "symbol": symbol,
                    "price": ticker_data.get('close', 0),
                    "volume": ticker_data.get('volume', 0),
                    "duration_ms": duration_ms
                })
                return ticker_data
            else:
                self.logger.warning("api_response", f"No ticker data for {symbol}", {
                    "symbol": symbol,
                    "duration_ms": duration_ms
                })
                return {}
            
        except Exception as e:
            duration_ms = (time.time() - request_start_time) * 1000
            self.logger.error("api_error", f"Failed to fetch ticker for {symbol}", {
                "symbol": symbol,
                "error": str(e),
                "duration_ms": duration_ms
            }, error=e)
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

