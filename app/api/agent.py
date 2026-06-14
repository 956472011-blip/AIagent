"""AI Agent 端点 —— LLM 自主决策调工具。

与 /chat (固定 RAG 流程) 的区别:
    /chat:  分类 → 改写 → 检索 → 生成 → 自检  (流程写死)
    /agent: LLM 自己决定要不要检索、要不要计算    (ReAct 推理)

企业级特性:
    - JWT 鉴权(复用现有中间件)
    - SSE 流式输出(实时看到 LLM 思考和工具调用)
    - 工具调用可观测(前端能看到"我调用了 rag_search"事件)
"""
from __future__ import annotations

import json
import re
from typing import AsyncIterator

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import BaseModel, Field

from app.agents.agent import _filter_think_block, get_agent
from app.middlewares.auth_middleware import CurrentUser, CurrentUserFromQuery


router = APIRouter(prefix="/agent", tags=["agent"])


# === 请求/响应模型 ===

class AgentRequest(BaseModel):
    """Agent 请求体。"""
    query: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    thread_id: str | None = Field(default=None, description="会话 ID(预留,目前未持久化)")


class AgentResponse(BaseModel):
    """非流式响应。"""
    answer: str
    tool_calls: list[dict] = Field(default_factory=list, description="调用的工具列表")


# === SSE 事件格式 ===

def _format_sse(event: str, data) -> str:
    """SSE 事件格式: event: <name>\ndata: <json>\n\n"""
    if not isinstance(data, str):
        data = json.dumps(data, ensure_ascii=False, default=str)
    return f"event: {event}\ndata: {data}\n\n"


def _extract_tool_calls(messages: list) -> list[dict]:
    """从消息历史里抽 tool_calls(给前端展示用了哪些工具)。"""
    calls = []
    for msg in messages:
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                calls.append({
                    "name": tc.get("name"),
                    "args": tc.get("args"),
                })
    return calls


# === Agent 流式执行 ===

async def _stream_agent(query: str) -> AsyncIterator[str]:
    """流式执行 ReAct Agent。

    事件流:
        - thinking: LLM 思考过程(过滤掉 <think> 后)
        - tool_call: 决定调用某个工具
        - tool_result: 工具执行结果
        - answer: 最终答案片段
        - done: 完成
        - error: 出错
    """
    try:
        agent = get_agent()
        # 初始消息
        input_msg = {"messages": [HumanMessage(content=query)]}

        all_messages = []
        final_answer = ""

        # stream_mode="messages" 拿到每个 LLM 的输出 token / tool 消息
        async for event in agent.astream(input_msg, stream_mode="values"):
            # event 是当前完整的 messages 列表
            messages = event.get("messages", [])
            if not messages:
                continue

            latest = messages[-1]
            all_messages = messages

            # 1. AI 消息(可能是普通回复,也可能是带 tool_calls)
            if isinstance(latest, AIMessage):
                # 检查工具调用
                tool_calls = getattr(latest, "tool_calls", None) or []
                if tool_calls:
                    for tc in tool_calls:
                        yield _format_sse("tool_call", {
                            "name": tc.get("name"),
                            "args": tc.get("args"),
                        })

                # 普通文本输出(过滤 <think>)
                content = latest.content
                if isinstance(content, str) and content.strip():
                    cleaned = _filter_think_block(content)
                    if cleaned and cleaned != final_answer:
                        # 增量输出
                        delta = cleaned[len(final_answer):] if cleaned.startswith(final_answer) else cleaned
                        final_answer = cleaned
                        if delta:
                            yield _format_sse("answer", delta)

            # 2. 工具结果消息
            elif isinstance(latest, ToolMessage):
                tool_name = latest.name or "tool"
                content_str = str(latest.content)[:500]  # 截断防爆
                yield _format_sse("tool_result", {
                    "name": tool_name,
                    "content": content_str,
                })

        # 总结工具调用
        yield _format_sse("summary", {
            "tool_calls": _extract_tool_calls(all_messages),
            "answer": _filter_think_block(final_answer),
        })

        yield _format_sse("done", "ok")

    except Exception as exc:
        import traceback
        traceback.print_exc()
        yield _format_sse("error", f"{type(exc).__name__}: {exc}")


# === 端点 ===

@router.post("", response_model=AgentResponse)
async def agent_chat(
    req: AgentRequest,
    current_user: CurrentUser,
) -> AgentResponse:
    """非流式 Agent 调用(简单测试用)。

    Returns:
        完整答案 + 工具调用列表
    """
    agent = get_agent()
    result = await agent.ainvoke({"messages": [HumanMessage(content=req.query)]})
    messages = result.get("messages", [])

    # 提取最后的 AI 答案
    answer = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            answer = _filter_think_block(msg.content)
            break

    return AgentResponse(
        answer=answer,
        tool_calls=_extract_tool_calls(messages),
    )


@router.post("/stream")
async def agent_chat_stream(
    req: AgentRequest,
    current_user: CurrentUser,
) -> StreamingResponse:
    """流式 SSE 端点(POST 版,带 JWT 鉴权)。"""
    return StreamingResponse(
        _stream_agent(req.query),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/stream/get")
async def agent_chat_stream_get(
    q: str = Query(..., min_length=1, max_length=2000, description="用户问题"),
    current_user: CurrentUserFromQuery = None,
) -> StreamingResponse:
    """流式 SSE 端点(GET 版,浏览器 EventSource 用)。

    鉴权说明:
        EventSource 不支持自定义 Header,所以 Token 通过 Query 传: ?token=xxx
        这里走 Depends(get_current_user) 校验,失败会返回 401

    注意: Query 里的 token 会进 access log,生产环境建议加额外保护
    """
    return StreamingResponse(
        _stream_agent(q),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/tools")
async def list_tools(current_user: CurrentUser) -> dict:
    """返回当前 Agent 可用工具列表(给前端展示)。"""
    from app.agents.tools import ALL_TOOLS
    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
            }
            for t in ALL_TOOLS
        ]
    }
