"""M2 测试:文档入库接口。"""
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from app.main import app


client = TestClient(app)


def test_upload_document_ingests_chunks() -> None:
    from app.api import ingest as ingest_module

    def fake_load(_path):
        return [Document(page_content="企业知识库", metadata={"source": "demo.md"})]

    def fake_split_documents(_documents):
        return [Document(page_content="企业知识库", metadata={"source": "demo.md", "chunk_id": 0})]

    class FakeVectorStore:
        async def add_documents(self, documents):
            return len(documents)

    original_load = ingest_module.load
    original_split_documents = ingest_module.split_documents
    original_get_vectorstore = ingest_module.get_vectorstore
    ingest_module.load = fake_load  # type: ignore[assignment]
    ingest_module.split_documents = fake_split_documents  # type: ignore[assignment]
    ingest_module.get_vectorstore = lambda: FakeVectorStore()  # type: ignore[assignment]
    try:
        response = client.post(
            "/ingest/upload",
            files={"file": ("demo.md", b"# demo", "text/markdown")},
        )
    finally:
        ingest_module.load = original_load
        ingest_module.split_documents = original_split_documents
        ingest_module.get_vectorstore = original_get_vectorstore

    assert response.status_code == 200
    assert response.json()["filename"] == "demo.md"
    assert response.json()["documents"] == 1
    assert response.json()["chunks"] == 1


def test_upload_document_rejects_unsupported_file_type() -> None:
    response = client.post(
        "/ingest/upload",
        files={"file": ("demo.exe", b"bad", "application/octet-stream")},
    )

    assert response.status_code == 400
