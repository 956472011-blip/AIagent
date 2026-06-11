"""Hybrid 检索器:BM25 关键词召回 + 向量语义召回,RRF 融合。

设计:
    - 启动时从 Qdrant 拉一次全部 chunk, 内存里建 BM25 索引
    - 检索时双路召回 (BM25 top_n + Vector top_n), 用 RRF 融合去重
    - 返回 top_k 个 Document (按 RRF 分数排)

为什么需要 hybrid:
    - 向量召回:语义相关但容易"跑题" (问"维度"可能召到"大小"段落)
    - 关键词召回:精准但不会泛化 (问"RAG 步骤"能精准命中"步骤"段落)
    - 融合后:两者互补,鲁棒性显著提升
"""
from __future__ import annotations

import asyncio
from functools import lru_cache

import jieba
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from app.rag.vectorstore import QdrantDocumentStore, get_vectorstore


_RRF_K = 60  # RRF 平滑常数,业界常用 60
_DEFAULT_TOP_N = 20  # 每路召回多少候选


def _tokenize(text: str) -> list[str]:
    """中文友好分词:jieba 切词 + 转小写。

    English text 也兼容 (jieba 会按空格分)。
    """
    return [token.strip().lower() for token in jieba.cut(text) if token.strip()]


class HybridRetriever:
    """双路召回 + RRF 融合。"""

    def __init__(
        self,
        store: QdrantDocumentStore,
        *,
        k: int = 4,
        top_n: int = _DEFAULT_TOP_N,
    ) -> None:
        self.store = store
        self.k = k
        self.top_n = top_n
        self._corpus: list[Document] = []  # 全部 chunk
        self._bm25: BM25Okapi | None = None  # BM25 索引

    async def warmup(self) -> None:
        """从 Qdrant 拉全部 chunk, 内存建 BM25 索引。

        启动期调用一次即可。Qdrant 里数据变更后需要重新 warmup。
        """
        self.store.ensure_collection()
        # 用一个大 limit 拉全部, 简单粗暴
        from qdrant_client import models

        records, _next = await asyncio.to_thread(
            self.client.scroll,
            collection_name=self.store.collection_name,
            limit=10_000,
            with_payload=True,
            with_vectors=False,
            scroll_filter=models.Filter(must=[]),  # 全部
        )
        self._corpus = [
            Document(
                page_content=str(record.payload.get("page_content", "")),
                metadata=dict(record.payload.get("metadata") or {}),
            )
            for record in records
        ]
        tokenized_corpus = [_tokenize(doc.page_content) for doc in self._corpus]
        self._bm25 = BM25Okapi(tokenized_corpus) if tokenized_corpus else None

    @property
    def client(self):
        """透出 qdrant client 给 scroll 用。"""
        return self.store.client

    def _bm25_search(self, query: str) -> list[Document]:
        """BM25 召回 top_n。"""
        if self._bm25 is None or not self._corpus:
            return []
        tokens = _tokenize(query)
        scores = self._bm25.get_scores(tokens)
        # 按分数降序取 top_n
        ranked = sorted(enumerate(scores), key=lambda pair: pair[1], reverse=True)
        top = ranked[: self.top_n]
        return [self._corpus[idx] for idx, _score in top]

    @staticmethod
    def _rrf_fuse(
        ranked_lists: list[list[Document]],
        k: int = _RRF_K,
    ) -> list[Document]:
        """Reciprocal Rank Fusion:多个排名列表融合成一个去重排名。

        score(d) = Σ_i  1 / (k + rank_i(d))
        同一 doc 在不同列表出现, 分数累加, 自然去重。
        """
        scores: dict[int, float] = {}
        index_by_id: dict[int, Document] = {}
        for ranked in ranked_lists:
            for rank, doc in enumerate(ranked, start=1):
                # 用 page_content + metadata 做身份标识
                key = hash((doc.page_content, tuple(sorted(doc.metadata.items()))))
                index_by_id[key] = doc
                scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
        fused = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
        return [index_by_id[key] for key, _score in fused]

    async def retrieve(self, query: str) -> list[Document]:
        """双路召回 + RRF 融合, 返回 top_k。"""
        if self._bm25 is None:
            await self.warmup()

        # 两路并发
        bm25_task = asyncio.to_thread(self._bm25_search, query)
        vector_task = self.store.similarity_search(query, k=self.top_n)
        bm25_hits, vector_hits = await asyncio.gather(bm25_task, vector_task)

        fused = self._rrf_fuse([bm25_hits, vector_hits])
        return fused[: self.k]


@lru_cache(maxsize=1)
def get_hybrid_retriever() -> HybridRetriever:
    """获取 hybrid 检索器单例(需先调 warmup)。"""
    return HybridRetriever(get_vectorstore())
