"""Qdrant 向量库封装。"""
from functools import lru_cache
from uuid import uuid4

from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import settings
from app.rag.embeddings import get_embeddings


class QdrantDocumentStore:
    """最小文档向量库封装。"""

    def __init__(self, client: QdrantClient, collection_name: str) -> None:
        self.client = client
        self.collection_name = collection_name

    def ensure_collection(self) -> None:
        if self.client.collection_exists(self.collection_name):
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=settings.embedding_dim,
                distance=models.Distance.COSINE,
            ),
        )

    async def add_documents(self, documents: list[Document]) -> int:
        if not documents:
            return 0

        self.ensure_collection()
        vectors = await get_embeddings().aembed_documents(
            [document.page_content for document in documents]
        )
        points = [
            models.PointStruct(
                id=str(uuid4()),
                vector=vector,
                payload={
                    "page_content": document.page_content,
                    "metadata": document.metadata,
                },
            )
            for document, vector in zip(documents, vectors, strict=True)
        ]
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )
        return len(points)

    async def similarity_search(self, query: str, *, k: int = 4) -> list[Document]:
        self.ensure_collection()
        query_vector = await get_embeddings().aembed_query(query)
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=k,
            with_payload=True,
        )

        documents: list[Document] = []
        for point in response.points:
            payload = point.payload or {}
            documents.append(
                Document(
                    page_content=str(payload.get("page_content", "")),
                    metadata=dict(payload.get("metadata") or {}),
                )
            )
        return documents


@lru_cache(maxsize=1)
def get_vectorstore() -> QdrantDocumentStore:
    """获取 Qdrant 文档库单例。"""
    if not settings.qdrant_url:
        raise ValueError("QDRANT_URL 未配置!请在 .env 里设置后重启服务。")

    client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
    )
    return QdrantDocumentStore(client, settings.qdrant_collection)
