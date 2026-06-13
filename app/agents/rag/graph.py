"""RAG Agent 的 StateGraph 组装。

StateGraph 是 LangGraph 的核心:
    - 声明式定义流程（节点 + 边）
    - 支持条件分支、循环
    - 可视化、可调试

类比 Java:
    StateGraph ≈ Spring 的流程编排器
    节点 ≈ Bean/Service
    边 ≈ 方法调用链
    条件边 ≈ if/switch 分支

设计要点:
    1. 节点命名清晰，体现功能
    2. 边的类型：普通边（固定）、条件边（动态）
    3. 入口节点：START，出口节点：END
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.rag.nodes import (
    check_faithfulness,
    classify_intent,
    decide_route,
    generate_answer,
    increment_retry,
    reply_greeting,
    retrieve,
    rewrite_query,
)
from app.agents.rag.state import RAGState


def build_rag_graph() -> StateGraph:
    """构建 RAG Agent 的 StateGraph。

    流程图:

        START → classify_intent
                    │
        ┌───────────┼───────────┐
        │           │           │
     greeting    question   (其他)
        │           │           │
        ▼           ▼           │
   reply_greeting  rewrite      │
        │           │           │
        │           ▼           │
        │        retrieve       │
        │           │           │
        │           ▼           │
        │     generate_answer   │
        │           │           │
        │           ▼           │
        │   check_faithfulness  │
        │           │           │
        │     ┌─────┴─────┐     │
        │     │           │     │
        │   retry       end     │
        │     │           │     │
        │     ▼           ▼     │
        │ increment_retry  END   │
        │     │                 │
        │     ▼                 │
        │  retrieve             │
        │     │                 │
        └─────┴─────────────────┘
              (循环)
    """
    # 创建 StateGraph，指定 State 类型
    graph = StateGraph(RAGState)

    # ===== 添加节点 =====
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("reply_greeting", reply_greeting)
    graph.add_node("rewrite_query", rewrite_query)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("check_faithfulness", check_faithfulness)
    graph.add_node("increment_retry", increment_retry)

    # ===== 添加边 =====

    # 入口边：START → classify_intent
    graph.add_edge(START, "classify_intent")

    # 条件边：classify_intent → greeting/question
    graph.add_conditional_edges(
        "classify_intent",
        # 路由函数：根据 intent 决定下一步
        lambda state: "reply_greeting" if state.get("intent") == "greeting" else "rewrite_query",
        # 路由映射：返回值 → 目标节点
        {
            "reply_greeting": "reply_greeting",
            "rewrite_query": "rewrite_query",
        },
    )

    # 普通边：rewrite_query → retrieve
    graph.add_edge("rewrite_query", "retrieve")

    # 普通边：retrieve → generate_answer
    graph.add_edge("retrieve", "generate_answer")

    # 普通边：generate_answer → check_faithfulness
    graph.add_edge("generate_answer", "check_faithfulness")

    # 条件边：check_faithfulness → retry/end
    graph.add_conditional_edges(
        "check_faithfulness",
        # 路由函数：根据 route 决定下一步
        lambda state: state.get("route", "end"),
        # 路由映射
        {
            "retry": "increment_retry",
            "end": END,
        },
    )

    # 普通边：increment_retry → retrieve（重试循环）
    graph.add_edge("increment_retry", "retrieve")

    # 普通边：reply_greeting → END
    graph.add_edge("reply_greeting", END)

    return graph


# ===== 编译后的 Graph 实例 =====

def get_rag_graph():
    """获取编译后的 RAG Graph（可执行）。"""
    graph = build_rag_graph()
    return graph.compile()


# ===== 可视化（调试用）=====

def visualize_graph():
    """生成流程图图片（需要 graphviz）。"""
    graph = build_rag_graph()
    compiled = graph.compile()

    # 生成 Mermaid 图（文本格式，无需 graphviz）
    try:
        mermaid = compiled.get_graph().draw_mermaid()
        return mermaid
    except Exception as e:
        return f"无法生成可视化: {e}"