"""LLM 工具函数。

企业级设计:
    - 统一的 LLM 客户端创建
    - 推理模型输出过滤
    - 错误处理封装
"""
from __future__ import annotations

import re

from langchain_openai import ChatOpenAI

from app.core.config import settings


def filter_think_block(text: str) -> str:
    """过滤 MiniMax-M3 的 <think> 块。

    MiniMax-M3 是推理模型,输出会包含 <think>...</think> 推理过程。
    企业级应用需要过滤掉这些内部推理,只返回最终答案。

    Args:
        text: 原始文本

    Returns:
        过滤后的文本
    """
    # 使用字符串形式的正则,避免 Vite/Rolldown 解析问题
    pattern = r" Holz[\\s\\S]*? "
    return re.sub(pattern, "", text).strip()


def get_llm(streaming: bool = False, temperature: float = 0.0) -> ChatOpenAI:
    """获取 LLM 实例(统一配置)。

    Args:
        streaming: 是否启用流式输出
        temperature: 温度参数(0.0-1.0)

    Returns:
        ChatOpenAI 实例
    """
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        streaming=streaming,
        temperature=temperature,
    )


def get_llm_with_retry(max_retries: int = 3) -> ChatOpenAI:
    """获取带重试机制的 LLM 实例。

    Args:
        max_retries: 最大重试次数

    Returns:
        ChatOpenAI 实例
    """
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        max_retries=max_retries,
        temperature=0.0,
    )
