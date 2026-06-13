"""Redis Session 管理。

企业级设计:
    - Session 存 Redis，支持分布式部署
    - HttpOnly Cookie 存储 session_id，安全
    - 支持登出立即失效（删 Redis key）

类比 Java:
    - RedisSessionStore ≈ Spring Session Redis
"""
from __future__ import annotations

import json
import secrets
from typing import Any

import redis.asyncio as redis

from app.core.config import settings


class SessionManager:
    """Redis Session 管理器。"""

    def __init__(self) -> None:
        self._redis: redis.Redis | None = None

    async def connect(self) -> None:
        """连接 Redis。"""
        self._redis = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            decode_responses=True,
        )

    async def disconnect(self) -> None:
        """断开 Redis 连接。"""
        if self._redis:
            await self._redis.close()
            self._redis = None

    def _get_key(self, session_id: str) -> str:
        """Redis key 格式: session:{session_id}"""
        return f"session:{session_id}"

    async def create_session(self, user_id: int, username: str) -> str:
        """创建 Session，返回 session_id。"""
        session_id = secrets.token_urlsafe(32)
        session_data = {
            "user_id": user_id,
            "username": username,
        }

        if self._redis is None:
            raise RuntimeError("Redis 未连接")

        # 存储到 Redis，设置过期时间
        await self._redis.setex(
            self._get_key(session_id),
            settings.session_expire_seconds,
            json.dumps(session_data),
        )

        return session_id

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        """获取 Session 数据。"""
        if self._redis is None:
            raise RuntimeError("Redis 未连接")

        data = await self._redis.get(self._get_key(session_id))
        if data is None:
            return None

        return json.loads(data)

    async def delete_session(self, session_id: str) -> None:
        """删除 Session（登出时用）。"""
        if self._redis:
            await self._redis.delete(self._get_key(session_id))

    async def extend_session(self, session_id: str) -> None:
        """延长 Session 过期时间（用户活跃时调用）。"""
        if self._redis:
            await self._redis.expire(
                self._get_key(session_id),
                settings.session_expire_seconds,
            )


# 全局单例
session_manager = SessionManager()
