"""Simple in-memory cache for predictions to reduce API response times."""
import time
from typing import Dict, Optional
from datetime import datetime
from threading import Lock


class PredictionCache:
    """Thread-safe cache for ML predictions to avoid expensive recalculations.
    
    This cache stores predictions for a configurable TTL (time-to-live) period
    to significantly improve API response times for repeated requests.
    """
    
    def __init__(self, ttl_seconds: int = 300):
        """Initialize prediction cache.
        
        Args:
            ttl_seconds: Time to live for cached predictions (default: 5 minutes)
        """
        self.cache: Dict[str, tuple] = {}
        self.ttl_seconds = ttl_seconds
        self.lock = Lock()  # Thread-safe operations
    
    def get(self, symbol: str, timeframe: str) -> Optional[Dict]:
        """Get cached prediction if not expired.
        
        Args:
            symbol: Trading symbol (e.g., BTCUSD)
            timeframe: Timeframe (e.g., 15m, 1h)
            
        Returns:
            Cached prediction dict or None if not found/expired
        """
        key = self._make_key(symbol, timeframe)
        
        with self.lock:
            if key in self.cache:
                cached_data, timestamp = self.cache[key]
                age = time.time() - timestamp
                
                if age < self.ttl_seconds:
                    return cached_data.copy()  # Return a copy to prevent mutation
                else:
                    # Expired, remove it
                    del self.cache[key]
        
        return None
    
    def set(self, symbol: str, timeframe: str, data: Dict):
        """Cache prediction data.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            data: Prediction data to cache
        """
        key = self._make_key(symbol, timeframe)
        
        with self.lock:
            self.cache[key] = (data, time.time())
    
    def clear(self, symbol: str = None, timeframe: str = None):
        """Clear cache for specific symbol/timeframe or all.
        
        Args:
            symbol: Optional symbol to clear
            timeframe: Optional timeframe to clear
        """
        with self.lock:
            if symbol and timeframe:
                key = self._make_key(symbol, timeframe)
                if key in self.cache:
                    del self.cache[key]
            else:
                self.cache.clear()
    
    def get_stats(self) -> Dict:
        """Get cache statistics.
        
        Returns:
            Dict with cache stats (size, entries, etc.)
        """
        with self.lock:
            return {
                'size': len(self.cache),
                'entries': list(self.cache.keys()),
                'ttl_seconds': self.ttl_seconds
            }
    
    def _make_key(self, symbol: str, timeframe: str) -> str:
        """Create cache key from symbol and timeframe."""
        return f"{symbol}_{timeframe}"
    
    def cleanup_expired(self):
        """Remove all expired entries (manual cleanup)."""
        current_time = time.time()
        
        with self.lock:
            expired_keys = [
                key for key, (_, timestamp) in self.cache.items()
                if current_time - timestamp >= self.ttl_seconds
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            return len(expired_keys)

