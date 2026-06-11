"""快速探测入库全链路各步耗时。"""
import asyncio
import time
from pathlib import Path

from app.core.config import settings
from app.rag.embeddings import get_embeddings
from app.rag.loader import load
from app.rag.splitter import split_documents
from app.rag.vectorstore import get_vectorstore


async def main() -> None:
    path = Path("test-docs/rag-intro.md")
    print(f"文件存在: {path.exists()}, 大小: {path.stat().st_size}B")

    t = time.perf_counter()
    docs = load(path)
    print(f"[1] loader 解析: {len(docs)} docs, 耗时 {time.perf_counter()-t:.2f}s")

    t = time.perf_counter()
    chunks = split_documents(docs)
    print(f"[2] splitter 切片: {len(chunks)} chunks, 耗时 {time.perf_counter()-t:.2f}s")

    t = time.perf_counter()
    embs = await get_embeddings().aembed_documents([c.page_content for c in chunks])
    print(f"[3] embedding: {len(embs)} 个向量, dim={len(embs[0])}, 耗时 {time.perf_counter()-t:.2f}s")

    t = time.perf_counter()
    await get_vectorstore().add_documents(chunks)
    print(f"[4] 写 Qdrant 集合 `{settings.qdrant_collection}`: 耗时 {time.perf_counter()-t:.2f}s")

    print(">>> probe done <<<")


if __name__ == "__main__":
    asyncio.run(main())
