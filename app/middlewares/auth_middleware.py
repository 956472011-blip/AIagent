"""认证中间件。

企业级设计:
    - 统一的 JWT 认证逻辑
    - 依赖注入方式使用
    - 错误处理统一
"""
from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.db.repositories.user_repo import UserRepository, get_user_repo

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    user_repo: UserRepository = Depends(get_user_repo),
) -> dict:
    """获取当前登录用户。

    Args:
        credentials: HTTP Bearer Token
        user_repo: 用户仓储

    Returns:
        当前用户信息

    Raises:
        HTTPException: Token 无效或用户不存在
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已过期",
        )
    except jwt.InvalidTokenError:
        raise credentials_exception

    # 查询用户
    user = await user_repo.get_by_username(username)
    if user is None:
        raise credentials_exception

    return user


# 类型别名,简化使用
CurrentUser = Annotated[dict, Depends(get_current_user)]
