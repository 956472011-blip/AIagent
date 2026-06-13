"""测试 RAG Agent 的 LangGraph 流程。

运行方式:
    pytest app/tests/test_agents/test_rag_graph.py -v

测试内容:
    1. 问候语 → 直接回复
    2. 正经问题 → 检索 + 生成 + 自检
"""
import pytest

from app.agents.rag.graph import get_rag_graph, visualize_graph


@pytest.mark.asyncio
async def test_greeting():
    """测试问候语场景。"""
    graph = get_rag_graph()

    initial_state = {
        "query": "你好",
        "intent": "",
        "rewritten_query": "",
        "chunks": [],
        "answer": "",
        "faithfulness_score": 0.0,
        "reflection": "",
        "retry_count": 0,
        "route": "",
    }

    result = await graph.ainvoke(initial_state)

    assert result.get("intent") == "greeting"
    assert "你好" in result.get("answer", "")
    assert result.get("route") == "end"


@pytest.mark.asyncio
async def test_question():
    """测试问题场景(需要检索)。"""
    graph = get_rag_graph()

    initial_state = {
        "query": "什么是 RAG?",
        "intent": "",
        "rewritten_query": "",
        "chunks": [],
        "answer": "",
        "faithfulness_score": 0.0,
        "reflection": "",
        "retry_count": 0,
        "route": "",
    }

    result = await graph.ainvoke(initial_state)

    assert result.get("intent") == "question"
    assert len(result.get("chunks", [])) > 0
    assert result.get("faithfulness_score", 0.0) >= 0.0
    assert result.get("retry_count", 0) <= 1


def test_graph_visualization():
    """测试流程图生成。"""
    mermaid = visualize_graph()
    assert "classify_intent" in mermaid
    assert "retrieve" in mermaid
    assert "generate_answer" in mermaid
