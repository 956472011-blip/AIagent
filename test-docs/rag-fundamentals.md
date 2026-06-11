# RAG 基础原理

## 什么是 RAG

RAG (Retrieval-Augmented Generation, 检索增强生成) 是一种将外部知识库与大语言模型结合的技术范式。
其核心思想是: 在 LLM 生成答案前, 先从知识库中检索与问题相关的文档片段 (chunks), 将这些片段作为上下文
拼接到 prompt 里, 再交给 LLM 生成答案。

## RAG 的核心流程

完整的 RAG 流程包含 6 个步骤:

1. **文档加载 (Loading)**: 从 PDF、Word、Markdown、网页等来源加载原始文本内容, 转成 LangChain Document 对象。
2. **文本切片 (Splitting)**: 把长文档切成 200-800 字的小块 (chunk), 块之间保留 10-20% 的重叠以避免语义断裂。
3. **向量化 (Embedding)**: 用 Embedding 模型把每块文本转成 1536 维或 1024 维的密集向量。
4. **入库存储 (Indexing)**: 把向量和原文一起写入向量数据库, 如 Qdrant、Milvus、Chroma 等。
5. **检索 (Retrieval)**: 用户提问时, 把问题也转成向量, 在库里做相似度搜索, 召回到 top-k 个相关 chunk。
6. **生成 (Generation)**: 把检索到的 chunk 作为 context 拼到 system prompt, 交给 LLM 生成最终答案。

## RAG 的三大痛点

朴素 RAG 在生产环境会遇到三个核心痛点:

1. **检索质量差**: 纯向量检索对"专有名词"、"数字"、"型号"等关键词不敏感。例如问"Qdrant 用什么距离算法", 向量检索可能召回到无关段落。
2. **召回不全**: 单路检索 (只用向量或只用 BM25) 召回率有限, 容易漏掉相关但用词不同的段落。
3. **上下文窗口有限**: LLM 的 context window 有限 (4k-128k tokens), 不可能把全库塞进去, 必须靠检索挑出最相关的几条。

## 解决痛点的主流方案

- **Hybrid 检索**: BM25 关键词召回 + 向量语义召回, 用 RRF (Reciprocal Rank Fusion) 融合, 取长补短。
- **Rerank 精排**: 用 Cross-Encoder (如 BGE-reranker、gte-rerank) 对粗排的 top-20 候选做精排, 选最相关的 3-5 条喂给 LLM。
- **Query 改写**: 用 LLM 把用户的口语化问题改写成更适合检索的查询。
- **HyDE (Hypothetical Document Embeddings)**: 让 LLM 先生成一个"假想答案", 用假想答案去做检索。

## 评价 RAG 质量

业界主要用 RAGAS 框架做 RAG 质量评测, 4 个核心指标:

- **Context Precision**: 召回到的 chunk 里"相关"的比例 (越高越好, 0~1)
- **Context Recall**: 标答相关的内容召回了多少 (越高越好, 0~1)
- **Faithfulness**: 答案是否忠于上下文, 没有幻觉 (越高越好, 0~1)
- **Answer Relevancy**: 答案是否切题, 没跑偏 (越高越好, 0~1)
