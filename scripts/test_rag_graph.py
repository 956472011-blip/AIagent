"""测试 RAG Agent 的 LangGraph 流程。

运行方式:
    uv run python scripts/test_rag_graph.py

测试内容:
    1. 问候语 → 直接回复
    2. 正经问题 → 检索 + 生成 + 自检
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.agents.rag.graph import get_rag_graph, visualize_graph


async def test_greeting():
    """测试问候语场景。"""
    print("\n" + "=" * 50)
    print("测试 1: 问候语")
    print("=" * 50)

    graph = get_rag_graph()

    # 初始状态
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

    # 执行
    result = await graph.ainvoke(initial_state)

    print(f"意图: {result.get('intent')}")
    print(f"答案: {result.get('answer')}")
    print(f"路由: {result.get('route')}")

    return result


async def test_question():
    """测试问题场景（需要检索）。"""
    print("\n" + "=" * 50)
    print("测试 2: 正经问题")
    print("=" * 50)

    graph = get_rag_graph()

    # 初始状态
    initial_state = {
        "query": "什么是 RAG？",
        "intent": "",
        "rewritten_query": "",
        "chunks": [],
        "answer": "",
        "faithfulness_score": 0.0,
        "reflection": "",
        "retry_count": 0,
        "route": "",
    }

    # 执行
    result = await graph.ainvoke(initial_state)

    print(f"意图: {result.get('intent')}")
    print(f"检索到 {len(result.get('chunks', []))} 个 chunks")
    print(f"忠实度: {result.get('faithfulness_score'):.2f}")
    print(f"自检评语: {result.get('reflection')}")
    print(f"重试次数: {result.get('retry_count')}")
    print(f"\n答案:\n{result.get('answer')}")

    return result


def print_graph_visualization():
    """打印流程图。"""
    print("\n" + "=" * 50)
    print("流程图 (Mermaid)")
    print("=" * 50)
    mermaid = visualize_graph()
    print(mermaid)


async def main():
    """主测试流程。"""
    print("=" * 50)
    print("RAG Agent LangGraph 测试")
    print("=" * 50)

    # 打印流程图
    print_graph_visualization()

    # 测试问候语
    await test_greeting()

    # 测试问题
    await test_question()

    print("\n" + "=" * 50)
    print("测试完成！")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
