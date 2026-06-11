# 三大向量库对比 (Qdrant / Milvus / Weaviate)

## 概览

Qdrant、Milvus、Weaviate 是 2026 年最主流的三个开源向量数据库。本文从架构、性能、生态、学习成本四个维度做对比。

## Qdrant

**核心特点**: 用 Rust 写的高性能向量库, 单文件部署友好, REST + gRPC 双协议。

- **默认端口**: 6333 (REST), 6334 (gRPC)
- **距离算法**: Cosine (默认)、Euclidean、Dot Product
- **向量维度**: 灵活, 推荐 384 / 768 / 1024 / 1536
- **过滤能力**: 支持 payload 过滤, 适合"召回+元数据过滤"组合
- **部署**: 单二进制 < 100MB, 适合中小规模 (< 千万级)
- **学习成本**: 低, 文档友好, API 简洁

## Milvus

**核心特点**: Go + C++ 写的分布式向量库, 专攻超大规模场景。

- **默认端口**: 19530 (gRPC), 9091 (健康检查)
- **距离算法**: Cosine、Euclidean、内积 (IP)
- **架构**: 存储计算分离 (MinIO + etcd + Pulsar), 集群复杂
- **部署**: 至少 3 节点起步, 适合千万-百亿级
- **学习成本**: 中, 集群概念多 (proxy / querynode / datanode)
- **优势场景**: 互联网大厂、超大规模、人脸识别 / 推荐系统

## Weaviate

**核心特点**: GraphQL 优先, 内置向量化模块, 模块化强。

- **默认端口**: 8080 (REST), 50051 (gRPC)
- **距离算法**: Cosine 为主
- **特色功能**: 内置多个 vectorizer 模块 (OpenAI、Cohere、HuggingFace), 可零代码向量化
- **存储**: 支持向量 + 原始对象 + 跨引用 (GraphQL 关系查询)
- **学习成本**: 中, GraphQL 友好者上手快, 但生态偏小众

## 选型决策树

```
Q: 数据规模如何?
  ├─ < 100 万条 → Qdrant (单文件部署, 简单稳)
  ├─ 100 万 ~ 1 亿 → Qdrant (集群) 或 Milvus
  └─ > 1 亿 → Milvus (分布式成熟)

Q: 需要 GraphQL 关系查询?
  └─ 是 → Weaviate

Q: 团队熟悉 Rust 不熟悉 Go?
  └─ 选 Qdrant
```

## 我们的选择

本 RAG 知识助手项目选 **Qdrant**, 理由:

1. 学习曲线平缓, 适合个人/小团队
2. 单文件部署方便, 上云服务器 (118.25.107.222) 跑得动
3. Rust 性能足够, 千万级以下不输 Milvus
4. 跟 LangChain 集成 (`langchain-qdrant`) 成熟
