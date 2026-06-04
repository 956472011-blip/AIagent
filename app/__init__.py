"""RAG Assistant - 企业级 RAG 知识助手。

包入口。后续模块按以下约定组织:
- app.api:    FastAPI 路由层 (REST/SSE 端点)
- app.core:   跨切关注点 (config, logging, llm factory)
- app.rag:    检索增强生成 (loader, splitter, embedder, retriever)
- app.agent:  LangGraph 智能体 (state, nodes, graph, tools)
"""
__version__ = "0.1.0"
