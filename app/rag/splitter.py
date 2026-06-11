"""文档切块器。"""
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


_CHINESE_SEPARATORS = [
    "\n\n",
    "\n",
    "。",
    "！",
    "？",
    "；",
    "，",
    " ",
    "",
]


def split_documents(
    documents: list[Document],
    *,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[Document]:
    """把原始 Document 切成更适合检索的小块。"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=_CHINESE_SEPARATORS,
    )
    chunks = splitter.split_documents(documents)

    for index, chunk in enumerate(chunks):
        chunk.metadata = {
            **chunk.metadata,
            "chunk_id": index,
            "source": chunk.metadata.get("source", "unknown"),
        }

    return chunks
