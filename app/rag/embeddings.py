"""Embedding 模型工厂。

M2-M3 早期: 用 MiniMax embo-01 (自研协议, 偶尔不稳)
M3 后期: 换阿里 DashScope text-embedding-v4 (中文友好, 协议稳定, 已用 DashScope key 顺手)

DashScope embedding 协议:
    POST /api/v1/services/embeddings/text-embedding/text-embedding
    请求: {"model", "input": {"texts": [...]}, "parameters": {"dimension": N}}
    响应: {"output": {"embeddings": [{"embedding": [...]}]}, "usage": {...}}
"""
from functools import lru_cache

import httpx
from langchain_core.embeddings import Embeddings

from app.core.config import settings


_EMBEDDING_URL = (
    "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
)


class DashScopeEmbeddings(Embeddings):
    """DashScope text-embedding-v4 的 LangChain 适配器。"""

    def __init__(self, model: str, api_key: str, dimension: int = 1536) -> None:
        self._model = model
        self._dimension = dimension
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _call(self, texts: list[str]) -> list[list[float]]:
        """同步调用 DashScope embedding API。"""
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                _EMBEDDING_URL,
                headers=self._headers,
                json={
                    "model": self._model,
                    "input": {"texts": texts},
                    "parameters": {"dimension": self._dimension},
                },
            )
            response.raise_for_status()
            data = response.json()

        embeddings = data.get("output", {}).get("embeddings", [])
        if not embeddings:
            raise RuntimeError(f"DashScope embedding 返回空: {data}")

        return [item["embedding"] for item in embeddings]

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(self._call, texts)

    async def aembed_query(self, text: str) -> list[float]:
        vectors = await asyncio.to_thread(self._call, [text])
        return vectors[0]

    # === 同步版本 (基类要求) ===

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._call(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._call([text])[0]


# 让 asyncio.to_thread 可用
import asyncio


@lru_cache(maxsize=1)
def get_embeddings() -> Embeddings:
    """获取 Embedding 模型单例。"""
    if not settings.dashscope_api_key:
        raise ValueError("DASHSCOPE_API_KEY 未配置!请在 .env 里设置。")
    if not settings.embedding_model:
        raise ValueError("EMBEDDING_MODEL 未配置!请在 .env 里设置, 例如 text-embedding-v4。")
    return DashScopeEmbeddings(
        model=settings.embedding_model,
        api_key=settings.dashscope_api_key,
        dimension=settings.embedding_dim,
    )
