"""Cache module."""

from backend.cache.redis_cache import SmartCache, get_cache, invalidate_cache

__all__ = ['SmartCache', 'get_cache', 'invalidate_cache']


