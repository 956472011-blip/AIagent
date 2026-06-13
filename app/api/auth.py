"""认证 API 端点。

企业级 JWT 认证流程:
    1. 用户注册: POST /auth/register
    2. 用户登录: POST /auth/login → 返回 JWT Token
    3. Token 验证: 每次请求通过 Authorization Header 携带 Token
    4. Token 过期: 需要重新登录获取新 Token

前端交互:
    - 登录成功: 存储 Token 到 LocalStorage/Cookie
    - 每次请求: Headers 添加 Authorization: Bearer <token>
    - Token 过期: 自动跳转登录页
"""
from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.db.repositories.user_repo import UserRepository, get_user_repo
from app.middlewares.auth_middleware import CurrentUser, get_current_user
from app.models.user import UserCreate, UserLogin, Token, UserResponse
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


# === Service 依赖注入 ===

def get_auth_service(user_repo: UserRepository = Depends(get_user_repo)) -> AuthService:
    """获取认证服务实例。"""
    return AuthService(user_repo)


# === API 端点 ===

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    req: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """用户注册。

    流程:
        1. 校验用户名/邮箱是否存在
        2. 加密密码(bcrypt)
        3. 创建用户记录
        4. 返回用户信息

    错误:
        - 400: 用户名已存在
        - 400: 邮箱已存在
    """
    try:
        user = await auth_service.register(
            username=req.username,
            password=req.password,
            email=req.email,
        )
        return UserResponse(**user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=Token)
async def login(
    req: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """用户登录。

    流程:
        1. 校验用户名密码
        2. 生成 JWT Token
        3. 返回 Token

    错误:
        - 401: 用户名或密码错误

    Token 有效期: 默认 30 分钟(可通过 JWT_EXPIRE_MINUTES 配置)
    """
    try:
        result = await auth_service.login(
            username=req.username,
            password=req.password,
        )
        return Token(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser,
) -> UserResponse:
    """获取当前用户信息。

    需要 Token: Authorization: Bearer <token>

    返回:
        - id: 用户 ID
        - username: 用户名
        - email: 邮箱
    """
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user.get("email"),
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """刷新 Token。

    需要 Token: Authorization: Bearer <token>

    流程:
        1. 验证当前 Token
        2. 生成新的 Token
        3. 返回新 Token

    用途:
        - Token 快过期时,无需重新登录,直接刷新
    """
    access_token = auth_service.create_access_token(
        data={"sub": current_user["username"], "user_id": current_user["id"]},
        expires_delta=timedelta(minutes=settings.jwt_expire_minutes),
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user={"id": current_user["id"], "username": current_user["username"]},
    )