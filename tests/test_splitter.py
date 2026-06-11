"""M2 测试:文档切块。"""
from langchain_core.documents import Document

from app.rag.splitter import split_documents


def test_split_documents_keeps_metadata_and_adds_chunk_id() -> None:
    documents = [
        Document(
            page_content="第一段讲 RAG。第二段讲向量检索。第三段讲引用。",
            metadata={"source": "demo.md"},
        )
    ]

    chunks = split_documents(documents, chunk_size=12, chunk_overlap=0)

    assert len(chunks) > 1
    assert all(chunk.metadata["source"] == "demo.md" for chunk in chunks)
    assert [chunk.metadata["chunk_id"] for chunk in chunks] == list(range(len(chunks)))
