"""Embedding 模型工厂。

MiniMax 的 embeddings 端点走自研协议(不是 OpenAI 协议),
所以这里直接用 httpx 调用,不用 langchain_openai。
请求: {"model", "texts":[...], "type":"db"}
响应: {"vectors": [[...], ...], "total_tokens": N, "base_resp": {...}}
"""
from functools import lru_cache

import httpx
from langchain_core.embeddings import Embeddings

from app.core.config import settings


class MiniMaxEmbeddings(Embeddings):
    """MiniMax embedding 接口的 LangChain 适配器。

    LangChain 协议要求实现两个方法:
    - aembed_documents(texts) -> List[List[float]]   入库时批量调用
    - aembed_query(text)       -> List[float]         检索时单条调用
    """

    def __init__(self, model: str, api_key: str, base_url: str) -> None:
        self._model = model
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        # OpenAI 协议兼容的 base_url 通常是 .../v1,我们这里要拼 .../v1/embeddings
        self._url = base_url.rstrip("/") + "/embeddings"

    async def _embed(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self._url,
                headers=self._headers,
                json={"model": self._model, "texts": texts, "type": "db"},
            )
            response.raise_for_status()
            payload = response.json()

        if payload.get("base_resp", {}).get("status_code") != 0:
            raise RuntimeError(f"MiniMax embedding 失败: {payload}")

        vectors = payload.get("vectors")
        if not vectors:
            raise RuntimeError(f"MiniMax embedding 返回空 vectors: {payload}")

        return vectors

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """批量嵌入文档。"""
        return await self._embed(texts)

    async def aembed_query(self, text: str) -> list[float]:
        """单条嵌入查询。"""
        vectors = await self._embed([text])
        return vectors[0]

    # === 同步版本(基类要求) ===

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                self._url,
                headers=self._headers,
                json={"model": self._model, "texts": texts, "type": "db"},
            )
            response.raise_for_status()
            payload = response.json()
        if payload.get("base_resp", {}).get("status_code") != 0:
            raise RuntimeError(f"MiniMax embedding 失败: {payload}")
        vectors = payload.get("vectors")
        if not vectors:
            raise RuntimeError(f"MiniMax embedding 返回空 vectors: {payload}")
        return vectors

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed_sync(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embed_sync([text])[0]


@lru_cache(maxsize=1)
def get_embeddings() -> Embeddings:
    """获取 Embedding 模型单例。"""
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY 未配置!请在 .env 里设置后重启服务。")

    return MiniMaxEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )
