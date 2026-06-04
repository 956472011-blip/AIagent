"""LLM 工厂。

设计要点:
- 单例模式:模块级缓存,避免每次请求重新构造 ChatModel(连接复用)
- OpenAI 协议兼容:用 ChatOpenAI,只要服务端支持 OpenAI 协议(OpenAI 官方、
  Anthropic 代理、国内中转如 minimaxi 等)就能用
- 缺 key 直接崩:fail fast,绝不带病上线
"""
from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.core.config import settings


@lru_cache(maxsize=1)
def get_llm() -> BaseChatModel:
    """获取 ChatModel 单例。

    @lru_cache 让函数变成"记忆化":第一次调用实例化,后续调用直接返回缓存。
    Java 类比:Spring @Bean + @Scope("singleton"),但更轻量。

    Raises:
        ValueError: OPENAI_API_KEY 未配置时直接抛出
    """
    if not settings.openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY 未配置!请在 .env 里设置后重启服务。"
        )

    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=0.7,
        streaming=True,  # M1 必备:开启流式输出
    )
