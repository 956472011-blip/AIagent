"""聊天服务层。

企业级设计:
    - 业务逻辑与 API 层分离
    - 便于单元测试
    - 支持多种 Agent 类型扩展
"""
from __future__ import annotations

from typing import AsyncIterator

from app.agents.rag.graph import get_rag_graph
from app.agents.rag.state import RAGState


class ChatService:
    """聊天服务,封装 Agent 调用逻辑。"""

    async def chat(self, query: str) -> dict:
        """非流式聊天。

        Args:
            query: 用户问题

        Returns:
            包含 answer、intent、faithfulness_score 等的字典
        """
        graph = get_rag_graph()

        initial_state: RAGState = {
            "query": query,
            "intent": "",
            "rewritten_query": "",
            "chunks": [],
            "answer": "",
            "faithfulness_score": 0.0,
            "reflection": "",
            "retry_count": 0,
            "route": "",
        }

        result_state = await graph.ainvoke(initial_state)
        return result_state

    async def stream_chat(self, query: str) -> AsyncIterator[dict]:
        """流式聊天,返回节点状态更新。

        Args:
            query: 用户问题

        Yields:
            节点状态更新事件 {"node": str, "output": dict}
        """
        graph = get_rag_graph()

        initial_state: RAGState = {
            "query": query,
            "intent": "",
            "rewritten_query": "",
            "chunks": [],
            "answer": "",
            "faithfulness_score": 0.0,
            "reflection": "",
            "retry_count": 0,
            "route": "",
        }

        async for event in graph.astream(initial_state, stream_mode="updates"):
            for node_name, node_output in event.items():
                yield {"node": node_name, "output": node_output}


# 单例模式
_chat_service: ChatService | None = None


def get_chat_service() -> ChatService:
    """获取聊天服务单例。"""
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service