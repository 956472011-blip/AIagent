"""单轮 LLM 流式对话端点。

SSE (Server-Sent Events) 协议:
- Content-Type: text/event-stream
- 每个事件格式: data: <内容>\\n\\n  (注意两个换行)
- 浏览器/curl 原生支持,前端用 EventSource 接收
- 比 WebSocket 简单:单向、服务端推、HTTP 长连接
"""
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field

from app.core.llm import get_llm


router = APIRouter(prefix="/chat", tags=["chat"])


# === 请求/响应模型(Pydantic BaseModel,自动校验+生成 Schema) ===

class ChatRequest(BaseModel):
    """聊天请求体。"""
    query: str = Field(..., min_length=1, max_length=2000, description="用户问题")


class ChatResponse(BaseModel):
    """非流式响应体(供测试用)。"""
    answer: str


# === LCEL Chain: prompt | llm | parser ===
# 这就是 LangChain 1.x 的核心抽象:用 | 把组件串成链,像 Unix pipe
#
#   输入 query
#      ↓
#   ChatPromptTemplate:把 query 包成 [{"role": "user", "content": query}]
#      ↓
#   llm:调 OpenAI 协议 API,逐 token 返回 AIMessageChunk
#      ↓
#   StrOutputParser:从 AIMessageChunk 提取 .content 字符串
#      ↓
#   输出纯文本流

_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个简洁有用的助手,用中文回答,控制在 100 字以内。"),
    ("user", "{query}"),
])

_chain = _prompt | get_llm() | StrOutputParser()


# === 端点 ===

@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """非流式端点(用于测试/简单场景)。"""
    try:
        answer = await _chain.ainvoke({"query": req.query})
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM 调用失败: {exc}") from exc
    return ChatResponse(answer=answer)


@router.post("/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    """流式 SSE 端点:逐 token 推送,前端体验是"打字机效果"。

    关键点:返回的是 StreamingResponse,内容是 async generator。
    每个 yield 出来一个 chunk,FastAPI 自动加 data: 前缀和 \\n\\n。
    """
    async def event_source() -> AsyncIterator[str]:
        try:
            async for chunk in _chain.astream({"query": req.query}):
                # SSE 协议格式: data: <内容>\\n\\n
                # FastAPI 的 StreamingResponse 会按 media_type 渲染,
                # 但 SSE 需要我们手动拼 data: 前缀
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:
            # 流已经开始,不能用 HTTPException;只能 yield 错误事件
            yield f"data: [ERROR] {exc}\n\n"

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲,确保真流式
        },
    )
