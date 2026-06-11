# AI Agent 技术栈 (2026 版)

## LangChain vs LangGraph

**LangChain** 是 2022 年开源的 LLM 应用框架, 以 Chain (链) 为核心抽象, 适合单轮或多轮顺序调用。

**LangGraph** 是 2024 年 LangChain 团队推出的新框架, 以 **StateGraph (状态图)** 为核心抽象,
引入"节点 (node) + 边 (edge) + 条件路由"概念, 适合**复杂多步 agent 工作流**。

## LangGraph 核心概念

- **StateGraph**: 整个 agent 的状态机, 维护一个共享 state dict
- **Node**: 一个处理函数, 接收 state 返回更新后的 state
- **Edge**: 节点之间的连接, 可以是固定边 (A→B) 或条件边 (A→B 或 C, 根据 state 决定)
- **Checkpoint**: 状态快照, 可持久化到数据库 (Postgres / Redis), 实现"时间旅行"和"断点续跑"

LangGraph 适合需要**循环、条件分支、人在回路 (Human-in-the-loop)** 的复杂场景,
M4 阶段我们会用 LangGraph 重构 RAG agent。

## MCP (Model Context Protocol)

**MCP** 是 **Anthropic** 在 2024 年底提出的开放协议, 目标: 给 LLM 标准化"工具调用"和"上下文注入"。

类比:
- HTTP 是 web 的协议标准
- LSP (Language Server Protocol) 是 IDE 语言服务的协议标准
- **MCP 是 LLM 工具调用的协议标准**

MCP 三大角色:
1. **Host**: LLM 应用本身 (如 Claude Desktop、IDE 插件)
2. **Client**: 跟 Server 通信的中间层
3. **Server**: 提供具体能力 (读文件、查数据库、调 API), 通过 MCP 协议暴露

到 2026 年, MCP 已成为事实标准, OpenAI、Google、Microsoft 都已支持。

## 工具调用 (Tool Calling) 三种范式

### 1. Function Calling (原生)

LLM 厂商直接支持, 主流模型 (GPT-4o、Claude、MiniMax-M3) 都有。

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "查天气",
        "parameters": {...}
    }
}]
response = llm.invoke("北京天气", tools=tools)
```

### 2. ReAct (Reason + Act)

让 LLM 显式"思考→行动→观察→再思考", 适合需要多次推理的场景。

### 3. Plan-and-Execute

先让 LLM 拆解任务, 列出执行计划, 然后逐步执行。适合长任务链。

## RAG vs Fine-tuning 选型

- **数据量小 (< 1000 条) + 需要最新信息** → RAG ✅
- **数据量大 (万级以上) + 风格/能力需要改变** → Fine-tuning ✅
- **两者结合** → 先 RAG 加知识, 再 FT 改风格, 业界主流

## LangSmith 可观测

LangSmith 是 LangChain 官方的 LLM 应用观测平台, 类似 "Datadog for LLM":

- 记录每次 LLM 调用的 prompt、response、token 数、延迟
- 追踪 chain 内每个节点的输入输出
- 标注 bad case, 攒评测集

我们 M7 阶段会接入 LangSmith。
