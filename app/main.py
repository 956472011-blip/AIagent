"""FastAPI 应用入口。

M0 职责:创建应用 + 注册健康检查 + 暴露元信息。
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app import __version__
from app.api.auth.routes import router as auth_router
from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.ingest import router as ingest_router
from app.core.config import settings
from app.db.database import db_pool
from app.db.session import session_manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期：启动时连接数据库和 Redis，关闭时断开。"""
    print(f"[startup] {settings.app_name} v{__version__} env={settings.app_env}")

    # 连接 PostgreSQL
    print("[startup] Connecting to PostgreSQL...")
    await db_pool.connect()
    print("[startup] PostgreSQL connected")

    # 连接 Redis
    print("[startup] Connecting to Redis...")
    await session_manager.connect()
    print("[startup] Redis connected")

    yield

    # 断开连接
    print("[shutdown] Disconnecting...")
    await session_manager.disconnect()
    await db_pool.disconnect()
    print(f"[shutdown] {settings.app_name} goodbye")


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    debug=settings.debug,
    lifespan=lifespan,
)

# 路由注册
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(ingest_router)


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    """根路径,返回服务基本信息(方便 curl 快速确认服务在跑)。"""
    return {
        "name": settings.app_name,
        "version": __version__,
        "env": settings.app_env,
    }
