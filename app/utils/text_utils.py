"""文本处理工具函数。

企业级设计:
    - 文本清洗
    - 引用标注提取
    - 摘要生成
"""
from __future__ import annotations

import re


def extract_citations(text: str) -> list[str]:
    """提取文本中的引用标注 [1] [2]。

    Args:
        text: 原始文本

    Returns:
        引用标注列表,如 ["1", "2", "3"]
    """
    pattern = r"\[(\d+)\]"
    matches = re.findall(pattern, text)
    return list(set(matches))


def truncate_text(text: str, max_length: int = 200) -> str:
    """截断文本,保留指定长度。

    Args:
        text: 原始文本
        max_length: 最大长度

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text

    return text[:max_length] + "..."


def clean_whitespace(text: str) -> str:
    """清理多余空白字符。

    Args:
        text: 原始文本

    Returns:
        清理后的文本
    """
    # 替换多个连续空格为单个空格
    text = re.sub(r"\s+", " ", text)
    # 去除首尾空格
    return text.strip()


def format_chunks_with_sources(chunks: list) -> str:
    """格式化 chunks 文本,添加来源标注。

    Args:
        chunks: Document 列表

    Returns:
        格式化后的文本
    """
    formatted = ""
    for i, chunk in enumerate(chunks, start=1):
        source = chunk.metadata.get("source", "未知来源")
        formatted += f"[{i}] 来源: {source}\n内容: {chunk.page_content}\n\n"

    return formatted
