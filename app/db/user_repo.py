"""用户数据访问层。

类比 Java:
    - UserRepository ≈ Spring Data JPA Repository
"""
from __future__ import annotations

from typing import Any

from app.db.database import db_pool
from app.db.security import hash_password, verify_password


class UserRepository:
    """用户数据访问。"""

    @staticmethod
    async def create_user(
        username: str,
        email: str,
        password: str,
        full_name: str | None = None,
    ) -> dict[str, Any]:
        """创建用户。"""
        password_hash = hash_password(password)

        async with db_pool.get_connection() as conn:
            user_id = await conn.fetchval(
                """
                INSERT INTO users (username, email, password_hash, full_name)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                username,
                email,
                password_hash,
                full_name,
            )

            return {
                "id": user_id,
                "username": username,
                "email": email,
                "full_name": full_name,
            }

    @staticmethod
    async def get_by_username(username: str) -> dict[str, Any] | None:
        """根据用户名查询用户。"""
        async with db_pool.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT id, username, email, password_hash, full_name, is_active FROM users WHERE username = $1",
                username,
            )

            if row is None:
                return None

            return dict(row)

    @staticmethod
    async def get_by_email(email: str) -> dict[str, Any] | None:
        """根据邮箱查询用户。"""
        async with db_pool.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT id, username, email FROM users WHERE email = $1",
                email,
            )

            if row is None:
                return None

            return dict(row)

    @staticmethod
    async def get_by_id(user_id: int) -> dict[str, Any] | None:
        """根据 ID 查询用户。"""
        async with db_pool.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT id, username, email, full_name FROM users WHERE id = $1",
                user_id,
            )

            if row is None:
                return None

            return dict(row)

    @staticmethod
    async def authenticate(username: str, password: str) -> dict[str, Any] | None:
        """验证用户登录。"""
        user = await UserRepository.get_by_username(username)

        if user is None:
            return None

        if not verify_password(password, user["password_hash"]):
            return None

        if not user["is_active"]:
            return None

        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
        }


# 全局实例
user_repo = UserRepository()
