"""认证 API：注册、登录、登出。

企业级设计:
    - Session 存 Redis，HttpOnly Cookie 存储 session_id
    - 登出立即失效（删 Redis）
    - 密码 bcrypt 加密

前端交互:
    - 登录成功：服务端设置 Cookie，前端跳转
    - 每次请求：浏览器自动带 Cookie
    - 登出：服务端删 Redis + 清 Cookie
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, EmailStr

from app.db.session import session_manager
from app.db.user_repo import user_repo
from app.core.config import settings


router = APIRouter(prefix="/auth", tags=["auth"])


# === 请求/响应模型 ===

class RegisterRequest(BaseModel):
    """注册请求。"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    full_name: str | None = Field(None, max_length=100, description="姓名")


class LoginRequest(BaseModel):
    """登录请求。"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    """用户信息响应。"""
    id: int
    username: str
    email: str
    full_name: str | None = None


class AuthStatusResponse(BaseModel):
    """认证状态响应。"""
    is_authenticated: bool
    user: UserResponse | None = None


# === 认证依赖 ===

async def get_current_user(request: Request) -> dict | None:
    """从 Session 获取当前用户（依赖注入）。"""
    session_id = request.cookies.get(settings.session_cookie_name)

    if not session_id:
        return None

    session_data = await session_manager.get_session(session_id)

    if not session_data:
        return None

    # 延长 Session 过期时间
    await session_manager.extend_session(session_id)

    return session_data


async def require_auth(request: Request) -> dict:
    """要求用户已登录（依赖注入）。"""
    user = await get_current_user(request)

    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    return user


# === API 端点 ===

@router.post("/register", response_model=UserResponse)
async def register(req: RegisterRequest) -> UserResponse:
    """用户注册。"""
    # 检查用户名是否已存在
    existing = await user_repo.get_by_username(req.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 检查邮箱是否已存在
    existing = await user_repo.get_by_email(req.email)
    if existing:
        raise HTTPException(status_code=400, detail="邮箱已存在")

    # 创建用户
    user = await user_repo.create_user(
        username=req.username,
        email=req.email,
        password=req.password,
        full_name=req.full_name,
    )

    return UserResponse(**user)


@router.post("/login", response_model=UserResponse)
async def login(req: LoginRequest, response: Response) -> UserResponse:
    """用户登录。

    流程:
        1. 验证用户名密码
        2. 创建 Session（存 Redis）
        3. 设置 HttpOnly Cookie
    """
    # 验证用户
    user = await user_repo.authenticate(req.username, req.password)

    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 创建 Session
    session_id = await session_manager.create_session(
        user_id=user["id"],
        username=user["username"],
    )

    # 设置 HttpOnly Cookie
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_id,
        httponly=settings.session_cookie_httponly,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        max_age=settings.session_expire_seconds,
    )

    return UserResponse(**user)


@router.post("/logout")
async def logout(request: Request, response: Response) -> dict:
    """用户登出。

    流程:
        1. 从 Cookie 获取 session_id
        2. 删除 Redis 中的 Session
        3. 清除 Cookie
    """
    session_id = request.cookies.get(settings.session_cookie_name)

    if session_id:
        # 删除 Redis Session
        await session_manager.delete_session(session_id)

    # 清除 Cookie
    response.delete_cookie(
        key=settings.session_cookie_name,
        httponly=settings.session_cookie_httponly,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
    )

    return {"message": "登出成功"}


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status(request: Request) -> AuthStatusResponse:
    """检查认证状态。

    前端用这个接口判断用户是否登录。
    """
    user = await get_current_user(request)

    if user:
        # 获取完整用户信息
        full_user = await user_repo.get_by_id(user["user_id"])
        return AuthStatusResponse(
            is_authenticated=True,
            user=UserResponse(**full_user) if full_user else None,
        )

    return AuthStatusResponse(is_authenticated=False, user=None)