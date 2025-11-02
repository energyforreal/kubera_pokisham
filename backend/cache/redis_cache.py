"""Redis caching layer with multi-level strategy."""

import json
import os
import pickle
from datetime import timedelta
from typing import Any, Callable, Optional, Dict
from collections import OrderedDict

import redis
from redis import Redis
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import logger


class L1Cache:
    """Level 1: In-memory cache for recent data (recent 1000 candles)."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        
        # Remove oldest if exceeded max size
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def delete(self, key: str) -> None:
        """Delete value from cache."""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self) -> None:
        """Clear entire cache."""
        self.cache.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)


class RedisCache:
    """Level 2: Redis cache for last 7 days data."""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.client: Optional[Redis] = None
        self.connected = False
        
        try:
            self.client = redis.from_url(
                self.redis_url,
                decode_responses=False,  # We'll handle encoding ourselves
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.client.ping()
            self.connected = True
            logger.info("Redis cache connected", url=self.redis_url.split('@')[-1])
        except Exception as e:
            logger.warning(f"Redis connection failed, cache disabled", error=str(e))
            self.client = None
            self.connected = False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        if not self.connected or not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Redis get failed", key=key, error=str(e))
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in Redis with TTL (time to live in seconds)."""
        if not self.connected or not self.client:
            return False
        
        try:
            serialized = pickle.dumps(value)
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.warning(f"Redis set failed", key=key, error=str(e))
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from Redis."""
        if not self.connected or not self.client:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis delete failed", key=key, error=str(e))
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self.connected or not self.client:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Redis clear pattern failed", pattern=pattern, error=str(e))
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self.connected or not self.client:
            return False
        
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.warning(f"Redis exists failed", key=key, error=str(e))
            return False


class SmartCache:
    """Multi-level caching strategy combining L1 (memory) + L2 (Redis) + L3 (Database)."""
    
    # TTL constants (in seconds)
    TTL_LIVE_PRICE = 5          # 5 seconds
    TTL_FEATURES = 60           # 1 minute
    TTL_PREDICTIONS = 300       # 5 minutes
    TTL_ANALYTICS = 3600        # 1 hour
    TTL_OHLCV = 604800          # 7 days
    
    def __init__(self, redis_url: Optional[str] = None):
        self.l1_cache = L1Cache(max_size=1000)
        self.l2_cache = RedisCache(redis_url)
        logger.info("Multi-level cache initialized", l1_enabled=True, l2_enabled=self.l2_cache.connected)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (checks L1 -> L2 -> returns None).
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        # Try L1 cache first
        value = self.l1_cache.get(key)
        if value is not None:
            return value
        
        # Try L2 cache
        value = self.l2_cache.get(key)
        if value is not None:
            # Populate L1 cache
            self.l1_cache.set(key, value)
            return value
        
        return None
    
    def set(self, key: str, value: Any, cache_type: str = 'features') -> None:
        """
        Set value in cache with appropriate TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            cache_type: Type of data (live_price, features, predictions, analytics, ohlcv)
        """
        # Determine TTL based on cache type
        ttl_map = {
            'live_price': self.TTL_LIVE_PRICE,
            'features': self.TTL_FEATURES,
            'predictions': self.TTL_PREDICTIONS,
            'analytics': self.TTL_ANALYTICS,
            'ohlcv': self.TTL_OHLCV
        }
        ttl = ttl_map.get(cache_type, self.TTL_FEATURES)
        
        # Set in L1 cache
        self.l1_cache.set(key, value)
        
        # Set in L2 cache with TTL
        self.l2_cache.set(key, value, ttl)
    
    def get_or_compute(
        self,
        key: str,
        compute_fn: Callable[[], Any],
        cache_type: str = 'features'
    ) -> Any:
        """
        Get value from cache or compute if not exists.
        
        Args:
            key: Cache key
            compute_fn: Function to compute value if not cached
            cache_type: Type of data for TTL determination
            
        Returns:
            Cached or computed value
        """
        # Try to get from cache
        value = self.get(key)
        if value is not None:
            return value
        
        # Compute value
        value = compute_fn()
        
        # Cache result
        if value is not None:
            self.set(key, value, cache_type)
        
        return value
    
    def invalidate(self, key: str) -> None:
        """
        Invalidate cache entry across all levels.
        
        Args:
            key: Cache key to invalidate
        """
        self.l1_cache.delete(key)
        self.l2_cache.delete(key)
    
    def invalidate_pattern(self, pattern: str) -> None:
        """
        Invalidate all cache entries matching pattern.
        
        Args:
            pattern: Pattern to match (e.g., "ohlcv:BTCUSD:*")
        """
        # L1 cache - invalidate matching keys
        keys_to_delete = [k for k in self.l1_cache.cache.keys() if self._matches_pattern(k, pattern)]
        for key in keys_to_delete:
            self.l1_cache.delete(key)
        
        # L2 cache - Redis supports pattern matching
        self.l2_cache.clear_pattern(pattern)
    
    def on_new_candle(self, symbol: str, timeframe: str) -> None:
        """
        Invalidate cache when new candle closes.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (e.g., 15m)
        """
        patterns = [
            f"ohlcv:{symbol}:{timeframe}",
            f"features:{symbol}:{timeframe}",
            f"prediction:{symbol}:{timeframe}"
        ]
        
        for pattern in patterns:
            self.invalidate_pattern(pattern)
        
        logger.debug(f"Cache invalidated for new candle", symbol=symbol, timeframe=timeframe)
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            'l1_size': self.l1_cache.size(),
            'l1_max_size': self.l1_cache.max_size,
            'l2_connected': self.l2_cache.connected
        }
    
    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches pattern (simple wildcard support)."""
        if '*' not in pattern:
            return key == pattern
        
        # Convert pattern to regex-like matching
        import re
        regex_pattern = pattern.replace('*', '.*')
        return bool(re.match(f"^{regex_pattern}$", key))


# Global cache instance
_cache: Optional[SmartCache] = None


def get_cache() -> SmartCache:
    """Get global cache instance."""
    global _cache
    if _cache is None:
        _cache = SmartCache()
    return _cache


def invalidate_cache():
    """Invalidate all cache."""
    global _cache
    if _cache:
        _cache.l1_cache.clear()
        if _cache.l2_cache.connected:
            _cache.l2_cache.clear_pattern("*")
    logger.info("Cache invalidated")


