"""数据模型定义。

企业级设计:
    - 使用 SQLModel(结合 SQLAlchemy + Pydantic)
    - 类型安全 + ORM 映射
    - 统一的数据模型定义
"""
from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """用户模型。"""

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=50)
    hashed_password: str = Field(max_length=255)
    email: str | None = Field(default=None, unique=True, max_length=100)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        """模型配置。"""
        from_attributes = True


class UserCreate(SQLModel):
    """用户注册请求体。"""

    username: str = Field(max_length=50)
    password: str = Field(min_length=6, max_length=100)
    email: str | None = Field(default=None, max_length=100)


class UserLogin(SQLModel):
    """用户登录请求体。"""

    username: str
    password: str


class Token(SQLModel):
    """Token 响应体。"""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    """Token payload。"""

    sub: str  # username
    user_id: int
    exp: datetime | None = None