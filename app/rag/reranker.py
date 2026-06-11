"""Reranker 精排:对 hybrid 召回的候选做 Cross-Encoder 打分排序。

为什么需要 rerank:
    - 向量检索 (Bi-Encoder) 速度快但"粗":把问题/段落分别编码再算距离, 看不到细粒度交互
    - 关键词召回 (BM25) 精准但"硬":不会做语义泛化
    - Rerank (Cross-Encoder) 把"问题 + 段落"拼起来过一次 transformer, 慢但准
    - 折中: Bi-Encoder 召回 30 条 -> Cross-Encoder 精排选 4 条

本实现走 DashScope gte-rerank API (阿里云灵积):
    - 中文场景最稳的 rerank 之一
    - 极便宜: ¥0.001 / 千 token
    - 接口: HTTPS POST, 无需下载大模型
    - 配置: .env 配 DASHSCOPE_API_KEY 即可
"""
from __future__ import annotations

import asyncio
from functools import lru_cache

import httpx
from langchain_core.documents import Document

from app.core.config import settings


_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank"
_DEFAULT_MODEL = "qwen3-rerank"


class DashScopeReranker:
    """基于阿里云 gte-rerank 的精排器。

    用法:
        reranker = DashScopeReranker()  # 单例
        top_docs = await reranker.rerank(query, candidates, top_k=4)
    """

    def __init__(self, model: str = _DEFAULT_MODEL) -> None:
        self.model = model

    def _api_key(self) -> str:
        """从 settings 读, 缺失时给出明确报错。"""
        # 我们用 openai_api_key 字段存(DashScope key 跟 minimaxi key 是两件事, 但 config 里没单独字段)
        # 优先读 DASHSCOPE_API_KEY, 读不到再用 OPENAI_API_KEY(灵活但容易混)
        # 简化: 走 settings 的额外字段, 没有就抛错
        from app.core.config import settings

        key = getattr(settings, "dashscope_api_key", None)
        if not key:
            raise ValueError("DASHSCOPE_API_KEY 未配置!请在 .env 里设置 DASHSCOPE_API_KEY=<你的key>")
        return key

    async def rerank(
        self,
        query: str,
        documents: list[Document],
        *,
        top_k: int = 4,
    ) -> list[Document]:
        """对候选 documents 精排, 返回 top_k。

        - 候选数 < top_k 时直接返回全部
        - HTTP 走 httpx async, 配 DashScope 鉴权
        """
        if not documents:
            return []
        k = min(top_k, len(documents))
        if len(documents) <= k:
            return documents

        api_key = self._api_key()
        payload = {
            "model": self.model,
            "input": {
                "query": query,
                "documents": [doc.page_content for doc in documents],
            },
            "parameters": {"top_n": k, "return_documents": False},
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        results = data.get("output", {}).get("results", [])
        if not results:
            raise RuntimeError(f"DashScope rerank 返回空 results: {data}")

        # results 按 relevance_score 降序, 但我们再排一次保证稳
        ranked = sorted(results, key=lambda r: r.get("relevance_score", 0), reverse=True)
        return [documents[r["index"]] for r in ranked[:k]]


@lru_cache(maxsize=1)
def get_reranker() -> DashScopeReranker:
    """获取 reranker 单例。"""
    return DashScopeReranker()
