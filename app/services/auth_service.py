"""认证服务层。

企业级设计:
    - JWT Token 生成和验证
    - 用户注册和登录逻辑
    - 密码加密和校验
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.db.repositories.user_repo import UserRepository


class AuthService:
    """认证服务,封装 JWT 和用户管理逻辑。"""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """校验密码。"""
        return verify_password(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        """加密密码。"""
        return hash_password(password)

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None) -> str:
        """生成 JWT Token。"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        return encoded_jwt

    async def register(self, username: str, password: str, email: str | None = None) -> dict:
        """用户注册。"""
        # 检查用户名是否已存在
        existing_user = await self.user_repo.get_by_username(username)
        if existing_user:
            raise ValueError("用户名已存在")

        # 创建用户
        hashed_password = self.hash_password(password)
        user = await self.user_repo.create(
            username=username,
            hashed_password=hashed_password,
            email=email,
        )

        return {"id": user["id"], "username": user["username"], "email": user.get("email")}

    async def login(self, username: str, password: str) -> dict:
        """用户登录。"""
        user = await self.user_repo.get_by_username(username)
        if not user:
            raise ValueError("用户名或密码错误")

        if not self.verify_password(password, user["hashed_password"]):
            raise ValueError("用户名或密码错误")

        # 生成 Token
        access_token = self.create_access_token(
            data={"sub": user["username"], "user_id": user["id"]},
            expires_delta=timedelta(minutes=settings.jwt_expire_minutes),
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {"id": user["id"], "username": user["username"]},
        }