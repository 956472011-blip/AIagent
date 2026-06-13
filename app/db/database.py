"""数据库连接池。

企业级设计:
    - 使用 asyncpg 连接池，性能高
    - 启动时创建连接池，关闭时释放
    - 提供 get_connection 上下文管理器

类比 Java:
    - 连接池 ≈ HikariCP
    - get_connection ≈ @Transactional
"""
from __future__ import annotations

import asyncpg
from contextlib import asynccontextmanager
from typing import AsyncIterator

from app.core.config import settings


class DatabasePool:
    """PostgreSQL 连接池管理器。"""

    def __init__(self) -> None:
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """创建连接池。"""
        if self._pool is None:
            # 解析 database_url 或直接使用配置
            self._pool = await asyncpg.create_pool(
                host="118.25.107.222",
                port=5432,
                user="postgres",
                password="Kp7sQv2#zRg9mBn&tA5",
                database="aiagent",
                min_size=5,
                max_size=20,
            )

    async def disconnect(self) -> None:
        """关闭连接池。"""
        if self._pool:
            await self._pool.close()
            self._pool = None

    @asynccontextmanager
    async def get_connection(self) -> AsyncIterator[asyncpg.Connection]:
        """获取数据库连接（上下文管理器）。"""
        if self._pool is None:
            raise RuntimeError("数据库连接池未初始化")
        async with self._pool.acquire() as conn:
            yield conn

    @property
    def pool(self) -> asyncpg.Pool:
        """获取连接池实例。"""
        if self._pool is None:
            raise RuntimeError("数据库连接池未初始化")
        return self._pool


# 全局单例
db_pool = DatabasePool()