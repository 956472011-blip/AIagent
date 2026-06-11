"""文档入库接口。"""
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.config import settings
from app.rag.loader import load
from app.rag.splitter import split_documents
from app.rag.vectorstore import get_vectorstore


router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestResponse(BaseModel):
    filename: str
    documents: int
    chunks: int
    collection: str


@router.post("/upload", response_model=IngestResponse)
async def upload_document(file: UploadFile) -> IngestResponse:
    """上传文档并写入向量库。"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".txt", ".md", ".pdf", ".docx"}:
        raise HTTPException(status_code=400, detail="仅支持 txt/md/pdf/docx 文件")

    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="文件内容不能为空")

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / Path(file.filename).name
            path.write_bytes(content)

            documents = load(path)
            chunks = split_documents(documents)
            await get_vectorstore().add_documents(chunks)

        return IngestResponse(
            filename=file.filename,
            documents=len(documents),
            chunks=len(chunks),
            collection=settings.qdrant_collection,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"文档入库失败: {exc}") from exc
