"""真正的 AI Agent:LLM 自主决策调哪个工具。

与 app/agents/rag/graph.py 的区别:
    - RAG Graph: 流程写死(分类→检索→生成)
    - 本 Agent: LLM 自己决定要不要检索、要不要计算

实现方式: LangGraph prebuilt 的 create_react_agent
    - ReAct = Reason(推理) + Act(行动)
    - LLM 看到工具列表,自己输出"我要调 rag_search" + 参数
    - 框架执行工具,把结果回传给 LLM
    - LLM 再决定:继续调其他工具 / 直接给最终答案

类比 Java:
    - create_react_agent ≈ Spring AI 的 ChatClient + ToolCallback
    - 但 LangGraph 把多步调用串成可观测的图
"""
from __future__ import annotations

import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from app.agents.tools import ALL_TOOLS
from app.core.config import settings


SYSTEM_PROMPT = """你是企业知识库助手,具备以下能力:
1. 检索知识库回答业务问题(用 rag_search 工具)
2. 计算数学表达式(用 calculator 工具)
3. 闲聊问候(直接回复)

【工作准则】
- 业务/技术问题先检索再回答,不要凭印象答
- 算术/数学问题用 calculator,不要心算
- 引用检索结果时用 [1][2] 标注来源
- 找不到答案就直说,不要编造
- 回答简洁有条理,中文输出"""


def _filter_think_block(text: str) -> str:
    """过滤 MiniMax-M3 的 <think> 块(推理模型特有)。"""
    pattern = r"<think>[\s\S]*?</think>"
    return re.sub(pattern, "", text).strip()


def _get_llm() -> ChatOpenAI:
    """统一 LLM 配置。"""
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=0.0,
    )


def build_agent():
    """构建可执行的 ReAct Agent。

    Returns:
        编译后的图对象,可直接 .ainvoke() 或 .astream()
    """
    llm = _get_llm()
    # create_react_agent 内部会:
    #   1. 把 tools 转成 OpenAI function calling 格式
    #   2. 给 LLM 发 system prompt + 工具列表
    #   3. 解析 LLM 返回的 tool_calls
    #   4. 执行工具,结果回传
    #   5. LLM 看工具结果决定下一步
    return create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        state_modifier=SYSTEM_PROMPT,
    )


# 单例 agent(避免每次请求都重新构建)
_agent = None


def get_agent():
    """获取 agent 单例(惰性初始化)。"""
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent
