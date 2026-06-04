"""FastAPI 应用入口。

M0 职责:创建应用 + 注册健康检查 + 暴露元信息。
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app import __version__
from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期:M0 阶段仅打日志,后续阶段在此初始化 DB/LLM 连接。"""
    print(f"[startup] {settings.app_name} v{__version__} env={settings.app_env}")
    yield
    print(f"[shutdown] {settings.app_name} goodbye")


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    debug=settings.debug,
    lifespan=lifespan,
)

# 路由注册(后续 /chat, /ingest 等都在这里挂)
app.include_router(health_router)
app.include_router(chat_router)


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    """根路径,返回服务基本信息(方便 curl 快速确认服务在跑)。"""
    return {
        "name": settings.app_name,
        "version": __version__,
        "env": settings.app_env,
    }
