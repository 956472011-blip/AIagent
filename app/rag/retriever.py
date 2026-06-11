"""RAG 检索器。"""
from functools import lru_cache

from langchain_core.documents import Document

from app.rag.vectorstore import QdrantDocumentStore, get_vectorstore


class Retriever:
    """从知识库检索与问题最相关的文档块。"""

    def __init__(self, store: QdrantDocumentStore, k: int = 4) -> None:
        self.store = store
        self.k = k

    async def retrieve(self, query: str) -> list[Document]:
        return await self.store.similarity_search(query, k=self.k)


@lru_cache(maxsize=1)
def get_retriever() -> Retriever:
    """获取检索器单例。"""
    return Retriever(get_vectorstore())
