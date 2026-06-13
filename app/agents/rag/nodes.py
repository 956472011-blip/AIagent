"""RAG Agent 的节点函数。

节点是 LangGraph 的执行单元:
    - 每个节点是一个纯函数
    - 输入: 当前 State
    - 输出: State 的部分更新（返回 dict）

类比 Java:
    节点 ≈ Spring 的一个 Service 方法
    State ≈ 方法参数 + 返回值的聚合
    返回 dict ≈ 只返回需要更新的字段（增量更新）

设计原则:
    1. 单一职责：每个节点只做一件事
    2. 纯函数：无副作用，便于测试和调试
    3. 明确输入输出：清楚读取什么，写入什么
"""
from __future__ import annotations

import json
import re
from typing import Literal

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.agents.rag.prompts import (
    FAITHFULNESS_CHECK_PROMPT,
    GENERATE_ANSWER_PROMPT,
    GREETING_REPLY_PROMPT,
    INTENT_CLASSIFY_PROMPT,
    REWRITE_QUERY_PROMPT,
)
from app.agents.rag.state import RAGState
from app.core.config import settings
from app.rag.hybrid_retriever import get_hybrid_retriever
from app.rag.reranker import get_reranker


# ===== LLM 实例 =====

def _filter_think_block(text: str) -> str:
    """过滤 MiniMax-M3 的 <think> 块。

    MiniMax-M3 是推理模型，输出会包含 <think>...</think> 推理过程。
    企业级应用需要过滤掉这些内部推理，只返回最终答案。
    """
    # 使用字符串形式的正则，避免 Vite/Rolldown 解析问题
    pattern = r"<think>[\s\S]*?</think>"
    return re.sub(pattern, "", text).strip()


def _get_llm(streaming: bool = False) -> ChatOpenAI:
    """获取 LLM 实例（统一配置）。"""
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        streaming=streaming,
        temperature=0.0,  # 企业场景用低温度，输出更稳定
    )


# ===== 节点 1: 意图分类 =====

def classify_intent(state: RAGState) -> dict:
    """判断用户意图: greeting / question。

    读取: query
    写入: intent

    企业级设计:
        - 用 LLM 分类，准确率高
        - 低成本：问题短，token 消耗少
        - 可扩展：未来可加更多意图类型
    """
    query = state["query"]

    # 简单规则优先（快速路径）
    greeting_keywords = ["你好", "您好", "hi", "hello", "在吗", "早上好", "晚上好"]
    if any(kw in query.lower() for kw in greeting_keywords) and len(query) < 10:
        return {"intent": "greeting"}

    # LLM 分类（复杂情况）
    llm = _get_llm()
    prompt = INTENT_CLASSIFY_PROMPT.format(query=query)
    response = llm.invoke([HumanMessage(content=prompt)])

    intent = response.content.strip().lower()
    intent = _filter_think_block(intent)
    # 校验输出，防止 LLM 输出意外内容
    if intent not in ["greeting", "question"]:
        intent = "question"  # 默认走问题流程

    return {"intent": intent}


# ===== 节点 2: 问候回复 =====

def reply_greeting(state: RAGState) -> dict:
    """友好回复问候语，跳过检索。

    读取: query
    写入: answer, route

    设计:
        - 直接生成友好回复
        - 不走检索流程，节省成本
        - route 设为 "end"，终止流程
    """
    query = state["query"]
    llm = _get_llm()
    prompt = GREETING_REPLY_PROMPT.format(query=query)
    response = llm.invoke([HumanMessage(content=prompt)])

    return {
        "answer": _filter_think_block(response.content),
        "route": "end",
    }


# ===== 节点 3: 查询改写（预留）=====

def rewrite_query(state: RAGState) -> dict:
    """LLM 改写问题，提升检索效果。

    读取: query
    写入: rewritten_query

    MVP 版本: 暂不启用，直接返回原 query。
    未来可开启，提升召回率。
    """
    # MVP: 暂不启用改写，直接用原问题
    return {"rewritten_query": state["query"]}

    # 未来启用时的逻辑:
    # llm = _get_llm()
    # prompt = REWRITE_QUERY_PROMPT.format(query=state["query"])
    # response = llm.invoke([HumanMessage(content=prompt)])
    # return {"rewritten_query": response.content.strip()}


# ===== 节点 4: 检索 =====

async def retrieve(state: RAGState) -> dict:
    """Hybrid 检索 + Rerank 精排。

    读取: query 或 rewritten_query
    写入: chunks

    设计:
        - 复用 M3 的 hybrid_retriever（BM25 + 向量 RRF）
        - 复用 M3 的 reranker（DashScope qwen3-rerank）
        - 先召回 20 条候选，rerank 选 4 条
    """
    query = state.get("rewritten_query") or state["query"]

    # Hybrid 检索
    retriever = get_hybrid_retriever()
    await retriever.warmup()

    # 扩大候选数给 rerank
    retriever.top_n = 20
    retriever.k = 20
    candidates = await retriever.retrieve(query)

    # Rerank 精排
    if candidates:
        reranker = get_reranker()
        top_chunks = await reranker.rerank(query, candidates, top_k=4)
    else:
        top_chunks = []

    return {"chunks": top_chunks}


# ===== 节点 5: 生成答案 =====

def generate_answer(state: RAGState) -> dict:
    """基于 chunks 生成答案，强制引用标注。

    读取: query, chunks
    写入: answer

    设计:
        - Prompt 强制要求引用标注 [1] [2]
        - chunks 带序号传给 LLM
        - 无 chunks 时生成"文档未提供"回复
    """
    query = state["query"]
    chunks = state.get("chunks", [])

    # 无检索结果时的处理
    if not chunks:
        return {
            "answer": "根据现有文档无法回答该问题，请提供更多上下文或尝试其他问题。",
            "route": "end",
        }

    # 构造带序号的 chunks 文本
    chunks_text = ""
    for i, chunk in enumerate(chunks, start=1):
        source = chunk.metadata.get("source", "未知来源")
        chunks_text += f"[{i}] 来源: {source}\n内容: {chunk.page_content}\n\n"

    # LLM 生成
    llm = _get_llm()
    prompt = GENERATE_ANSWER_PROMPT.format(query=query, chunks_text=chunks_text)
    response = llm.invoke([HumanMessage(content=prompt)])

    return {"answer": _filter_think_block(response.content)}


# ===== 节点 6: 忠实度检查 =====

def check_faithfulness(state: RAGState) -> dict:
    """检查答案是否忠实于 chunks，无幻觉。

    读取: query, chunks, answer
    写入: faithfulness_score, reflection, route

    设计:
        - LLM 打分 0.0-1.0
        - < 0.7 触发重试
        - 返回 JSON 格式，解析提取分数和理由
    """
    query = state["query"]
    chunks = state.get("chunks", [])
    answer = state.get("answer", "")

    # 无 chunks 或无答案时，直接结束
    if not chunks or not answer:
        return {
            "faithfulness_score": 0.0,
            "reflection": "无检索结果或无答案",
            "route": "end",
        }

    # 构造 chunks 文本
    chunks_text = "\n".join([chunk.page_content for chunk in chunks])

    # LLM 检查
    llm = _get_llm()
    prompt = FAITHFULNESS_CHECK_PROMPT.format(
        query=query,
        chunks_text=chunks_text,
        answer=answer,
    )
    response = llm.invoke([HumanMessage(content=prompt)])

    # 解析 JSON 结果
    try:
        # 提取 JSON（LLM 可能输出额外文本）
        content = response.content.strip()
        json_match = re.search(r"\{[^}]+\}", content)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {"score": 0.7, "reason": "无法解析", "need_retry": False}

        score = float(result.get("score", 0.7))
        reason = result.get("reason", "")
        need_retry = result.get("need_retry", score < 0.7)
    except (json.JSONDecodeError, ValueError):
        score = 0.7
        reason = "解析失败，默认通过"
        need_retry = False

    return {
        "faithfulness_score": score,
        "reflection": reason,
        "route": "retry" if need_retry else "end",
    }


# ===== 节点 7: 路由决策 =====

def decide_route(state: RAGState) -> Literal["retrieve", "generate", "end"]:
    """根据当前状态决定下一步。

    这个节点不修改 State，只返回路由目标。
    LangGraph 用返回值决定走哪条边。

    路由规则:
        1. greeting → 直接 end（已在 reply_greeting 设置）
        2. chunks 为空 → end（已在 generate_answer 设置）
        3. faithfulness < 0.7 且 retry_count < 1 → retrieve（重试）
        4. 其他 → end
    """
    intent = state.get("intent", "question")
    route = state.get("route", "end")
    retry_count = state.get("retry_count", 0)

    # 已经决定结束
    if route == "end":
        return "end"

    # 需要重试，且未超过最大次数
    if route == "retry" and retry_count < 1:
        return "retrieve"

    # 默认结束
    return "end"


# ===== 节点 8: 重试计数 =====

def increment_retry(state: RAGState) -> dict:
    """增加重试计数。

    在重试前调用，更新 retry_count。
    """
    return {"retry_count": state.get("retry_count", 0) + 1}