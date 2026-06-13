"""RAG Agent 状态定义。

State 是 LangGraph 的核心概念：
    - 所有节点共享的数据结构
    - 节点读取 State → 执行逻辑 → 返回 State 更新
    - 类似 Java 里的"请求上下文对象"，贯穿整个处理链路

类比 Spring:
    State ≈ HttpServletRequest + 业务数据的聚合
    节点 ≈ Filter/Interceptor，可以读取和修改 State
"""
from __future__ import annotations

from typing import Annotated
from typing import TypedDict

from langchain_core.documents import Document
from langgraph.graph import add_messages


def _merge_chunks(left: list[Document], right: list[Document]) -> list[Document]:
    """合并 chunks，右侧覆盖左侧（重试时用新结果）。"""
    return right if right else left


class RAGState(TypedDict):
    """RAG Agent 的共享状态。

    字段分组:
        - 输入层: query（用户原始问题）
        - 意图层: intent（问候/问题）
        - 检索层: rewritten_query, chunks
        - 生成层: answer
        - 自检层: faithfulness_score, reflection
        - 控制层: retry_count, route

    企业级设计要点:
        1. 字段命名清晰，一看就懂
        2. 每个阶段有独立的字段，便于调试和监控
        3. 控制字段放在最后，与业务逻辑分离
    """

    # ===== 输入层 =====
    query: str
    """用户原始问题，不可变。"""

    # ===== 意图层 =====
    intent: str
    """意图分类: "greeting" | "question"。

    greeting: 问候语，直接友好回复，跳过检索
    question: 正经问题，走完整 RAG 流程
    """

    # ===== 检索层 =====
    rewritten_query: str
    """LLM 改写后的问题（可选）。

    作用:
        - 补全模糊指代（"它" → 具体名词）
        - 展开缩写
        - 提升检索召回率

    注意: 当前 MVP 版本暂不启用，预留字段。
    """

    chunks: Annotated[list[Document], _merge_chunks]
    """检索到的上下文 chunks。

    LangGraph 的 Annotated 语法:
        - list[Document] 是类型
        - _merge_chunks 是 merge 函数，定义如何合并多次更新的结果

    为什么需要 merge?
        - 重试时，第二次检索的结果应该覆盖第一次
        - 默认行为是追加，我们改为覆盖
    """

    # ===== 生成层 =====
    answer: str
    """生成的答案。

    格式: 带引用标注的 Markdown，如:
        RAG 是检索增强生成技术 [1]。它结合了检索和生成 [2]。
    """

    # ===== 自检层 =====
    faithfulness_score: float
    """忠实度分数 0.0-1.0。

    含义: 答案有多少内容是基于 chunks 的，有多少是幻觉。
    阈值: < 0.7 触发重试
    """

    reflection: str
    """自检评语，记录为什么需要/不需要重试。

    用途:
        - 调试时查看 LLM 的判断理由
        - 审计日志，追溯决策过程
    """

    # ===== 控制层 =====
    retry_count: int
    """当前重试次数。

    最大重试次数: 1（MVP 版本）
    防止无限循环。
    """

    route: str
    """路由决策: "end" | "retry"。

    end: 流程结束，返回答案
    retry: 重试检索+生成
    """
