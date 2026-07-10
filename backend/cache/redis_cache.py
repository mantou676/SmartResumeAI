"""
Redis 缓存实现（加分项）
连接阿里云 Redis (ApsaraDB)，不可用时静默降级
"""
import json
import logging
from typing import Optional, Any
from .base import BaseCache

logger = logging.getLogger(__name__)


class RedisCache(BaseCache):
    """Redis 缓存，封装 redis-py"""

    def __init__(self, redis_url: str, ttl: int = 86400):
        self._redis_url = redis_url
        self._default_ttl = ttl
        self._client = None
        self._available = False
        self._init_client()

    def _init_client(self):
        """初始化 Redis 连接（延迟导入避免冷启动加载）"""
        try:
            import redis.asyncio as aioredis
            self._client = aioredis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=3,
                retry_on_timeout=True,
                max_connections=10,
            )
            self._available = True
            logger.info("Redis 连接池已初始化")
        except Exception as e:
            logger.warning(f"Redis 初始化失败，将使用内存缓存降级: {e}")
            self._available = False

    @property
    def available(self) -> bool:
        return self._available and self._client is not None

    async def get(self, key: str) -> Optional[dict]:
        if not self.available:
            return None
        try:
            val = await self._client.get(key)
            return json.loads(val) if val else None
        except Exception as e:
            logger.warning(f"Redis GET 失败: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        if not self.available:
            return
        ttl = ttl or self._default_ttl
        try:
            await self._client.setex(
                key, ttl,
                json.dumps(value, ensure_ascii=False, default=str)
            )
        except Exception as e:
            logger.warning(f"Redis SET 失败: {e}")

    async def delete(self, key: str) -> None:
        if not self.available:
            return
        try:
            await self._client.delete(key)
        except Exception as e:
            logger.warning(f"Redis DELETE 失败: {e}")

    async def exists(self, key: str) -> bool:
        if not self.available:
            return False
        try:
            return await self._client.exists(key) > 0
        except Exception as e:
            logger.warning(f"Redis EXISTS 失败: {e}")
            return False
