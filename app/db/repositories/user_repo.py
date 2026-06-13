"""用户仓储层。

企业级设计:
    - 数据访问逻辑与业务逻辑分离
    - 统一的接口定义
    - 便于切换数据源(MySQL/PostgreSQL/MongoDB)
"""
from __future__ import annotations

from typing import Any

from app.db.database import db_pool
from app.core.security import hash_password, verify_password


class UserRepository:
    """用户数据访问对象。"""

    async def create(
        self,
        username: str,
        hashed_password: str,
        email: str | None = None,
        full_name: str | None = None,
    ) -> dict[str, Any]:
        """创建用户。

        Args:
            username: 用户名
            hashed_password: 已加密的密码
            email: 邮箱(可选)
            full_name: 全名(可选)

        Returns:
            创建的用户信息
        """
        async with db_pool.get_connection() as conn:
            user_id = await conn.fetchval(
                """
                INSERT INTO users (username, email, password_hash, full_name)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                username,
                email,
                hashed_password,
                full_name,
            )

            return {
                "id": user_id,
                "username": username,
                "hashed_password": hashed_password,
                "email": email,
                "full_name": full_name,
            }

    async def get_by_username(self, username: str) -> dict[str, Any] | None:
        """根据用户名查询用户。"""
        async with db_pool.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT id, username, email, password_hash, full_name, is_active FROM users WHERE username = $1",
                username,
            )

            if row is None:
                return None

            return dict(row)

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        """根据邮箱查询用户。"""
        async with db_pool.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT id, username, email FROM users WHERE email = $1",
                email,
            )

            if row is None:
                return None

            return dict(row)

    async def get_by_id(self, user_id: int) -> dict[str, Any] | None:
        """根据 ID 查询用户。"""
        async with db_pool.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT id, username, email, full_name FROM users WHERE id = $1",
                user_id,
            )

            if row is None:
                return None

            return dict(row)


# 单例模式
_user_repo: UserRepository | None = None


def get_user_repo() -> UserRepository:
    """获取用户仓储单例。"""
    if _user_repo is None:
        _user_repo = UserRepository()
    return _user_repo