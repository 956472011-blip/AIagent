"""RAG Agent 流式对话端点。

改造说明:
    - M2: 简单 RAG (LCEL chain)
    - M4: LangGraph 智能体 (意图分类 + 检索 + 生成 + 自检)

企业级设计:
    1. 流式输出: 用户体验好，实时看到答案生成
    2. SSE 协议: 简单、HTTP 兼容、浏览器原生支持
    3. 引用标注: 答案带 [1][2]，可追溯来源
    4. 自检结果: 返回忠实度分数，用户可判断可信度
"""
from __future__ import annotations

import json
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agents.rag.graph import get_rag_graph
from app.agents.rag.state import RAGState


router = APIRouter(prefix="/chat", tags=["chat"])


# === 请求/响应模型 ===

class ChatRequest(BaseModel):
    """聊天请求体。"""
    query: str = Field(..., min_length=1, max_length=2000, description="用户问题")


class ChatResponse(BaseModel):
    """非流式响应体。"""
    answer: str
    intent: str = Field(description="意图: greeting/question")
    faithfulness_score: float = Field(default=0.0, description="忠实度分数 0-1")
    citations: list[dict] = Field(default_factory=list, description="引用来源")
    reflection: str = Field(default="", description="自检评语")
    retry_count: int = Field(default=0, description="重试次数")


# === SSE 事件格式 ===

def _format_sse_event(event: str, data: dict | str) -> str:
    """格式化 SSE 事件。

    格式: event: <事件名>\ndata: <数据>\n\n
    """
    if isinstance(data, dict):
        data_str = json.dumps(data, ensure_ascii=False)
    else:
        data_str = data
    return f"event: {event}\ndata: {data_str}\n\n"


def _format_citations(chunks: list) -> list[dict]:
    """从 chunks 提取引用信息。"""
    citations = []
    for i, chunk in enumerate(chunks, start=1):
        citations.append({
            "index": i,
            "source": chunk.metadata.get("source", "unknown"),
            "content_preview": chunk.page_content[:100] + "..." if len(chunk.page_content) > 100 else chunk.page_content,
        })
    return citations


# === LangGraph 流式执行 ===

async def _stream_rag_agent(query: str) -> AsyncIterator[str]:
    """流式执行 RAG Agent，实时输出节点状态和答案。

    企业级 SSE 设计:
        1. 节点状态事件: 用户能看到当前在做什么（检索/生成/自检）
        2. 答案流事件: 实时看到答案生成
        3. 结果事件: 最终结果（引用、分数等）

    事件类型:
        - node: 节点状态更新
        - answer: 答案内容片段
        - result: 最终结果
        - done: 流结束
        - error: 错误
    """
    try:
        graph = get_rag_graph()

        # 初始状态
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

        # LangGraph 支持流式输出节点状态
        # stream_mode="updates": 每个节点完成后输出一次状态更新
        current_state = initial_state

        async for event in graph.astream(initial_state, stream_mode="updates"):
            # event 是 dict，key 是节点名，value 是节点返回的状态更新
            for node_name, node_output in event.items():
                # 发送节点状态事件
                yield _format_sse_event("node", {
                    "node": node_name,
                    "status": "completed",
                })

                # 更新当前状态
                if isinstance(node_output, dict):
                    for key, value in node_output.items():
                        current_state[key] = value

                # 特殊处理：generate_answer 完成后，流式输出答案
                if node_name == "generate_answer" and "answer" in node_output:
                    answer = node_output["answer"]
                    # 模拟流式输出（实际 LLM 已经生成完毕）
                    # 企业级改进: 可以在 generate_answer 节点内真正流式生成
                    yield _format_sse_event("answer", answer)

        # 发送最终结果
        result = ChatResponse(
            answer=current_state.get("answer", ""),
            intent=current_state.get("intent", "question"),
            faithfulness_score=current_state.get("faithfulness_score", 0.0),
            citations=_format_citations(current_state.get("chunks", [])),
            reflection=current_state.get("reflection", ""),
            retry_count=current_state.get("retry_count", 0),
        )
        yield _format_sse_event("result", result.model_dump())

        # 结束
        yield _format_sse_event("done", "流结束")

    except Exception as exc:
        yield _format_sse_event("error", str(exc))


# === 端点 ===

@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """非流式端点（用于测试/简单场景）。

    直接执行完整流程，返回最终结果。
    """
    try:
        graph = get_rag_graph()

        initial_state: RAGState = {
            "query": req.query,
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

        return ChatResponse(
            answer=result_state.get("answer", ""),
            intent=result_state.get("intent", "question"),
            faithfulness_score=result_state.get("faithfulness_score", 0.0),
            citations=_format_citations(result_state.get("chunks", [])),
            reflection=result_state.get("reflection", ""),
            retry_count=result_state.get("retry_count", 0),
        )

    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"RAG Agent 执行失败: {exc}") from exc


@router.post("/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    """流式 SSE 端点（POST 版，后端内部 / curl 测试用）。"""
    return StreamingResponse(
        _stream_rag_agent(req.query),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/stream/get")
async def chat_stream_get(
    q: str = Query(..., min_length=1, max_length=2000, description="用户问题"),
) -> StreamingResponse:
    """流式 SSE 端点（GET 版，浏览器 EventSource 用）。

    为什么有 GET 版: 浏览器 EventSource 只支持 GET。
    """
    return StreamingResponse(
        _stream_rag_agent(q),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# === 调试端点 ===

@router.get("/graph")
async def get_graph_visualization():
    """返回 LangGraph 流程图（Mermaid 格式）。

    用于调试和文档展示。
    """
    from app.agents.rag.graph import visualize_graph
    return {"mermaid": visualize_graph()}