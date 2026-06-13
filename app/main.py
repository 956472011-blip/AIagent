"""FastAPI 应用入口。

企业级设计:
    - 生命周期管理: 数据库连接池
    - 路由注册: 模块化路由
    - 中间件: 认证、日志
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app import __version__
from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.ingest import router as ingest_router
from app.core.config import settings
from app.db.database import db_pool


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期:启动时连接数据库,关闭时断开。"""
    print(f"[startup] {settings.app_name} v{__version__} env={settings.app_env}")

    # 连接 PostgreSQL
    print("[startup] Connecting to PostgreSQL...")
    await db_pool.connect()
    print("[startup] PostgreSQL connected")

    yield

    # 断开连接
    print("[shutdown] Disconnecting...")
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
app.include_router(chat_router)
app.include_router(ingest_router)


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    """根路径,返回服务基本信息。"""
    return {
        "name": settings.app_name,
        "version": __version__,
        "env": settings.app_env,
    }
