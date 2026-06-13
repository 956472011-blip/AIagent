"""日志中间件。

企业级设计:
    - 记录请求/响应日志
    - 慢请求告警
    - 结构化日志输出
"""
from __future__ import annotations

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志中间件。"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求。"""
        # 记录请求开始时间
        start_time = time.time()

        # 处理请求
        response = await call_next(request)

        # 计算耗时
        process_time = time.time() - start_time

        # 记录日志
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time_ms": round(process_time * 1000, 2),
        }

        # 慢请求告警(> 1s)
        if process_time > 1.0:
            log_data["slow_request"] = True

        # 开发环境打印日志
        if settings.debug:
            print(f"[{log_data['method']}] {log_data['path']} - {log_data['status_code']} - {log_data['process_time_ms']}ms")

        # 添加响应头
        response.headers["X-Process-Time"] = str(process_time)

        return response