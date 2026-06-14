"""用户仓储层。

企业级设计:
    - 数据访问逻辑与业务逻辑分离
    - 统一的接口定义
    - 便于切换数据源(MySQL/PostgreSQL/MongoDB)
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.core.security import hash_password, verify_password


# 内存存储(演示用,生产环境应使用数据库)
_users_db: dict[str, dict[str, Any]] = {}


class UserRepository:
    """用户数据访问对象。"""

    async def create(
        self,
        username: str,
        hashed_password: str,
        email: str | None = None,
        full_name: str | None = None,
    ) -> dict[str, Any]:
        """创建用户。"""
        # 模拟数据库自增 ID
        user_id = len(_users_db) + 1
        user_data = {
            "id": user_id,
            "username": username,
            "hashed_password": hashed_password,
            "email": email,
            "full_name": full_name,
        }
        _users_db[username] = user_data
        return user_data

    async def get_by_username(self, username: str) -> dict[str, Any] | None:
        """根据用户名查询用户。"""
        return _users_db.get(username)

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        """根据邮箱查询用户。"""
        for user in _users_db.values():
            if user.get("email") == email:
                return user
        return None

    async def get_by_id(self, user_id: int) -> dict[str, Any] | None:
        """根据 ID 查询用户。"""
        for user in _users_db.values():
            if user.get("id") == user_id:
                return user
        return None


# 单例模式(使用 lru_cache 更安全)
@lru_cache(maxsize=1)
def get_user_repo() -> UserRepository:
    """获取用户仓储单例。"""
    return UserRepository()