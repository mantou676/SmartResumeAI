"""
进程内 LRU 缓存
基于 dict 的简单实现，用于无 Redis 时的降级方案
"""
import time
from typing import Optional, Any
from collections import OrderedDict
from .base import BaseCache


class MemoryCache(BaseCache):
    """基于 OrderedDict 的 LRU 内存缓存"""

    def __init__(self, max_size: int = 100):
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size

    async def get(self, key: str) -> Optional[dict]:
        """获取缓存，命中时移到队尾（LRU）"""
        if key not in self._cache:
            return None
        entry = self._cache[key]
        # 检查过期
        if entry["expires_at"] < time.time():
            del self._cache[key]
            return None
        # LRU: 移到末尾
        self._cache.move_to_end(key)
        return entry["value"]

    async def set(self, key: str, value: Any, ttl: int = 86400) -> None:
        """写入缓存，超出容量时淘汰最久未使用的"""
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl
        }
        # LRU 淘汰
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    async def delete(self, key: str) -> None:
        """删除缓存"""
        self._cache.pop(key, None)

    async def exists(self, key: str) -> bool:
        """检查是否存在且未过期"""
        if key not in self._cache:
            return False
        if self._cache[key]["expires_at"] < time.time():
            del self._cache[key]
            return False
        return True

    @property
    def size(self) -> int:
        return len(self._cache)
