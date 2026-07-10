"""
缓存抽象层
定义统一的缓存接口，方便后续切换实现
"""
from abc import ABC, abstractmethod
from typing import Optional, Any


class BaseCache(ABC):
    """缓存抽象基类"""

    @abstractmethod
    async def get(self, key: str) -> Optional[dict]:
        """获取缓存"""
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 86400) -> None:
        """设置缓存"""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """删除缓存"""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        ...
