"""文档加载器。

职责:把磁盘文件 (PDF/DOCX/TXT/MD) 转成 LangChain Document 列表。
不切块、不向量化 —— 那是 splitter 和 embedder 的事。

注: 0.16.x 版的 unstructured 在解析小 markdown 时会段错误 (Windows 上尤为明显),
所以纯文本类 (md/txt) 走内置读取,二进制类 (pdf/docx) 才走 unstructured。
"""
from pathlib import Path

from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_core.documents import Document


def load(path: str | Path) -> list[Document]:
    """加载一个文件,返回 Document 列表(可能多页/多元素)。

    Java 类比:类似 Tika 的 parse() 调用,输出结构化元素。
    """
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix in {".md", ".txt"}:
        return _load_text(file_path)

    return _load_with_unstructured(file_path)


def _load_text(path: Path) -> list[Document]:
    """纯文本文件:直接读,包成单元素 Document 列表。"""
    content = path.read_text(encoding="utf-8")
    return [Document(page_content=content, metadata={"source": str(path)})]


def _load_with_unstructured(path: Path) -> list[Document]:
    """PDF/DOCX 等二进制:交给 unstructured 解析。"""
    loader = UnstructuredFileLoader(str(path))
    return loader.load()
