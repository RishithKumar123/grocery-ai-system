import json
import time
from typing import Any, Optional
from app.core.config import settings
from app.core.logging import logger

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    logger.warning("redis-py package is missing or not installed.")


class RedisManager:
    """
    Enterprise Redis Client Manager.
    Provides high-performance caching for DB queries, embeddings, and rate-limiting.
    Falls back gracefully to an in-memory dictionary if Redis is unreachable.
    """

    def __init__(self):
        self.client = None
        self.is_connected = False
        self._fallback_cache = {}

        if HAS_REDIS and settings.REDIS_HOST:
            try:
                self.client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD or None,
                    decode_responses=True,
                    socket_timeout=2.0
                )
                self.client.ping()
                self.is_connected = True
                logger.info(f"RedisManager: Successfully connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            except Exception as e:
                logger.warning(f"RedisManager: Could not connect to Redis ({str(e)}). Operating in in-memory fallback mode.")
                self.client = None
                self.is_connected = False

    def get(self, key: str) -> Optional[Any]:
        """Fetch value by key."""
        if self.is_connected and self.client:
            try:
                val = self.client.get(key)
                if val is not None:
                    try:
                        return json.loads(val)
                    except (json.JSONDecodeError, TypeError):
                        return val
                return None
            except Exception as e:
                logger.error(f"RedisManager GET error for key '{key}': {str(e)}")

        # Fallback cache lookup
        item = self._fallback_cache.get(key)
        if item:
            val, expire_at = item
            if expire_at is None or expire_at > time.time():
                return val
            else:
                del self._fallback_cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value with optional time-to-live in seconds."""
        default_ttl = ttl or settings.CACHE_TTL_SECONDS
        json_val = json.dumps(value) if isinstance(value, (dict, list)) else str(value)

        if self.is_connected and self.client:
            try:
                self.client.set(key, json_val, ex=default_ttl)
                return True
            except Exception as e:
                logger.error(f"RedisManager SET error for key '{key}': {str(e)}")

        # Fallback cache store
        expire_at = time.time() + default_ttl if default_ttl else None
        self._fallback_cache[key] = (value, expire_at)
        return True

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if self.is_connected and self.client:
            try:
                self.client.delete(key)
            except Exception as e:
                logger.error(f"RedisManager DELETE error for key '{key}': {str(e)}")

        if key in self._fallback_cache:
            del self._fallback_cache[key]
        return True

    def incr(self, key: str, ttl: int = 60) -> int:
        """Increment integer counter key (used for rate limiting)."""
        if self.is_connected and self.client:
            try:
                count = self.client.incr(key)
                if count == 1:
                    self.client.expire(key, ttl)
                return count
            except Exception as e:
                logger.error(f"RedisManager INCR error for key '{key}': {str(e)}")

        # Fallback cache increment
        item = self._fallback_cache.get(key)
        now = time.time()
        if item:
            val, expire_at = item
            if expire_at is None or expire_at > now:
                new_val = int(val) + 1
                self._fallback_cache[key] = (new_val, expire_at)
                return new_val

        self._fallback_cache[key] = (1, now + ttl)
        return 1


redis_client = RedisManager()
