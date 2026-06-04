"""健康检查端点。

设计原则:
- 不查 DB、不调 LLM、不读文件 —— 进程在 = 健康
- k8s 探活规范:区分 liveness(进程在) 和 readiness(业务通);M0 只做 liveness
"""
from fastapi import APIRouter
from pydantic import BaseModel

from app import __version__
from app.core.config import settings


router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """健康检查响应模型。

    Java 类比:@Data class HealthResponseDto { ... }
    Pydantic 的 BaseModel 默认会做字段校验 + 自动生成 JSON Schema。
    """

    status: str
    app_name: str
    version: str
    env: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """轻量健康检查,直接返回 200。

    注意:这是 async def(即使函数体内没有 await)。
    原因:让 FastAPI 把它注册为 async 路由,后续如果加异步健康检查(如 ping DB)
    不会因为同步阻塞导致整个 worker 卡死。
    """
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=__version__,
        env=settings.app_env,
    )
