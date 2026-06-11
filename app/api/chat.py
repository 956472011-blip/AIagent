"""单轮 LLM 流式对话端点。

SSE (Server-Sent Events) 协议:
- Content-Type: text/event-stream
- 每个事件格式: data: <内容>\\n\\n  (注意两个换行)
- 浏览器/curl 原生支持,前端用 EventSource 接收
- 比 WebSocket 简单:单向、服务端推、HTTP 长连接
"""
import json
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field

from app.core.llm import get_llm
from app.rag.retriever import get_retriever


router = APIRouter(prefix="/chat", tags=["chat"])


# === 请求/响应模型(Pydantic BaseModel,自动校验+生成 Schema) ===

class ChatRequest(BaseModel):
    """聊天请求体。"""
    query: str = Field(..., min_length=1, max_length=2000, description="用户问题")


class ChatResponse(BaseModel):
    """非流式响应体(供测试用)。"""
    answer: str
    citations: list[dict[str, object]] = Field(default_factory=list)


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
    (
        "system",
        "你是企业知识库助手。只能基于给定资料回答;如果资料不足,就直接说明知识库中没有足够信息。用中文回答,控制在 200 字以内。",
    ),
    ("user", "问题:\n{query}\n\n资料:\n{context}"),
])

_chain = _prompt | get_llm() | StrOutputParser()


# === 端点 ===


def _format_context(documents: list[Document]) -> str:
    if not documents:
        return "知识库没有检索到相关资料。"

    return "\n\n".join(
        f"[资料{index}]\n{document.page_content}"
        for index, document in enumerate(documents, start=1)
    )


def _format_citations(documents: list[Document]) -> list[dict[str, object]]:
    citations: list[dict[str, object]] = []
    for index, document in enumerate(documents, start=1):
        citations.append({
            "index": index,
            "source": document.metadata.get("source", "unknown"),
            "chunk_id": document.metadata.get("chunk_id"),
        })
    return citations


async def _retrieve_context(query: str) -> tuple[str, list[dict[str, object]]]:
    documents = await get_retriever().retrieve(query)
    return _format_context(documents), _format_citations(documents)


async def _sse_generator(query: str) -> AsyncIterator[str]:
    """SSE 事件流生成器:POST 和 GET 端点共用。

    Java 类比:private helper method,被两个 controller 入口复用。
    """
    try:
        context, citations = await _retrieve_context(query)
        async for chunk in _chain.astream({"query": query, "context": context}):
            yield f"data: {chunk}\n\n"
        yield f"event: citations\ndata: {json.dumps(citations, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as exc:
        # 流已经开始,不能用 HTTPException;只能 yield 错误事件
        yield f"data: [ERROR] {exc}\n\n"


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """非流式端点(用于测试/简单场景)。"""
    try:
        context, citations = await _retrieve_context(req.query)
        answer = await _chain.ainvoke({"query": req.query, "context": context})
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM 调用失败: {exc}") from exc
    return ChatResponse(answer=answer, citations=citations)


@router.post("/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    """流式 SSE 端点(POST 版,后端内部 / curl 测试用)。"""
    return StreamingResponse(
        _sse_generator(req.query),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",    
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲,确保真流式
        },
    )


@router.get("/stream/get")
async def chat_stream_get(
    q: str = Query(..., min_length=1, max_length=2000, description="用户问题"),
) -> StreamingResponse:
    """流式 SSE 端点(GET 版,浏览器 EventSource 用)。

    为什么有 GET 版:浏览器 EventSource 只能 GET,POST 必须 fetch 手撕流解析。
    为了前端体验干净,后端让步加这个端点。M2 阶段只给前端用。
    """
    return StreamingResponse(
        _sse_generator(q),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
