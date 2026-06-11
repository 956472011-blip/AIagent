# RAG 知识助手简介

## 什么是 RAG

RAG (Retrieval-Augmented Generation,检索增强生成) 是一种将外部知识库与大语言模型结合的技术。
它通过在生成答案前先检索相关文档,让 LLM 的回答基于真实资料,减少幻觉。

## RAG 的核心流程

1. **文档加载**:从 PDF、Word、网页等来源加载原始内容
2. **文本切片**:把长文档切成几百字的小块(chunk)
3. **向量化**:用 Embedding 模型把每块转成数字向量
4. **入库存储**:把向量和原文一起存到向量数据库(如 Qdrant)
5. **检索**:用户提问时,把问题也转成向量,在库里找最相似的几个 chunk
6. **生成**:把检索到的 chunk 作为上下文,连同问题一起交给 LLM 生成答案

## 为什么需要 RAG

- 减少 LLM 的"幻觉",让回答有据可查
- 知识可更新,不用重新训练模型
- 可以引用具体文档,方便用户溯源
- 适合企业内部知识库、客服机器人、文档问答等场景

## 我们的项目栈

- 后端: Python 3.12 + FastAPI + LangChain + LangGraph
- 向量库: Qdrant (跑在云服务器 118.25.107.222:6333)
- Embedding: MiniMax embo-01 (OpenAI 协议兼容)
- LLM: MiniMax-M3
- 前端: Vite + React + TypeScript + Tailwind v4
