"""M3 RAGAS 评测 runner。

跑 3 套实验, 对比效果:
  1. vector     — 纯向量检索
  2. hybrid     — BM25 + 向量 RRF 融合
  3. hybrid+rr  — hybrid 召回 + DashScope rerank 精排

每套: 跑 20 条评测 -> 收集 contexts + answer -> RAGAS 打 4 个指标
出 report.md 横向对比。
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

# 让脚本能 import app/
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# === Monkey patch: 让 langchain ChatOpenAI 不发 n>1 (MiniMax 不支持) ===
import langchain_openai.chat_models.base as _lc_base

_original_create = _lc_base.ChatCompletion.create if hasattr(_lc_base, "ChatCompletion") else None


def _patched_chat_create(*args, **kwargs):
    """把 kwargs['n'] 强制设成 1 (MiniMax-M3 不支持多候选)。"""
    if "n" in kwargs and kwargs["n"] is not None and kwargs["n"] > 1:
        kwargs["n"] = 1
    return _original_create(*args, **kwargs)


if _original_create is not None:
    _lc_base.ChatCompletion.create = _patched_chat_create

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from ragas import EvaluationDataset, evaluate
from ragas.llms import LangchainLLMWrapper

from app.core.config import settings
from app.rag.hybrid_retriever import get_hybrid_retriever
from app.rag.reranker import get_reranker
from app.rag.vectorstore import get_vectorstore


DATASET_PATH = ROOT / "eval" / "dataset.jsonl"
REPORT_PATH = ROOT / "eval" / "report.md"

# RAGAS judge 用的 LLM 模型名 (阿里 DashScope 兼容模式, 支持 n=4)
JUDGE_MODEL = "qwen-plus"


def load_dataset() -> list[dict]:
    with DATASET_PATH.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def get_llm() -> ChatOpenAI:
    """RAGAS 的 judge LLM: 走阿里 DashScope qwen-plus。

    为什么不用 MiniMax-M3?
      RAGAS 内部用 n=4 采多候选算一致性, MiniMax-M3 不支持 n>1。
    qwen-plus 是阿里同家, OpenAI 协议兼容, 走 DashScope base_url 即可。
    """
    return ChatOpenAI(
        model=JUDGE_MODEL,
        api_key=settings.dashscope_api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=0.0,
    )


async def generate_answer(question: str, context_chunks: list[Document]) -> str:
    """用 LLM 根据召回的 context 生成答案 (跟生产 chat.py 一样的 prompt)。"""
    context_text = "\n\n---\n\n".join(c.page_content for c in context_chunks)
    system = (
        "你是 RAG 知识助手。基于下面【参考资料】回答用户问题。\n"
        "如果参考资料里没有答案, 直接说'文档未提供'。\n"
        "回答控制在 200 字内。\n\n"
        f"【参考资料】\n{context_text}"
    )
    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        streaming=False,
    )
    resp = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=question)])
    return resp.content


async def run_vector_experiment(items: list[dict]) -> EvaluationDataset:
    """实验 1: 纯向量检索。"""
    store = get_vectorstore()
    samples = []
    for item in items:
        docs = await store.similarity_search(item["question"], k=4)
        answer = await generate_answer(item["question"], docs)
        samples.append({
            "user_input": item["question"],
            "retrieved_contexts": [d.page_content for d in docs],
            "response": answer,
            "reference": item["ground_truth"],
        })
        print(f"  [vec] {item['id']:2d} done")
    return EvaluationDataset.from_list(samples)


async def run_hybrid_experiment(items: list[dict]) -> EvaluationDataset:
    """实验 2: hybrid 检索 (BM25 + 向量 RRF)。"""
    hr = get_hybrid_retriever()
    await hr.warmup()
    samples = []
    for item in items:
        docs = await hr.retrieve(item["question"])
        answer = await generate_answer(item["question"], docs)
        samples.append({
            "user_input": item["question"],
            "retrieved_contexts": [d.page_content for d in docs],
            "response": answer,
            "reference": item["ground_truth"],
        })
        print(f"  [hyb] {item['id']:2d} done")
    return EvaluationDataset.from_list(samples)


async def run_hybrid_rerank_experiment(items: list[dict]) -> EvaluationDataset:
    """实验 3: hybrid 召回 top-20 + DashScope rerank 选 top-4。"""
    hr = get_hybrid_retriever()
    await hr.warmup()
    rr = get_reranker()
    samples = []
    for item in items:
        # 扩大候选数给 rerank 精排
        hr.top_n = 20
        hr.k = 20
        candidates = await hr.retrieve(item["question"])
        top_docs = await rr.rerank(item["question"], candidates, top_k=4)
        answer = await generate_answer(item["question"], top_docs)
        samples.append({
            "user_input": item["question"],
            "retrieved_contexts": [d.page_content for d in top_docs],
            "response": answer,
            "reference": item["ground_truth"],
        })
        print(f"  [hrr] {item['id']:2d} done")
    return EvaluationDataset.from_list(samples)


def score(dataset: EvaluationDataset, name: str) -> dict:
    """RAGAS 打分 4 个核心指标。

    注意: RAGAS 内部用 embedding 算 answer_relevancy 指标,
    我们用 MiniMax embo-01 替代 (OpenAI 协议, 自定义 base_url)。
    """
    print(f"  [ragas:{name}] scoring...")
    judge = LangchainLLMWrapper(get_llm())

    # 给 RAGAS 一个走 DashScope text-embedding-v4 的客户端
    # 关键: 用 LangchainEmbeddingsWrapper 把 LangChain 协议的 OpenAIEmbeddings 包成 RAGAS 能用的形式
    from langchain_openai import OpenAIEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper

    embeddings_lc = OpenAIEmbeddings(
        model=settings.embedding_model,  # text-embedding-v4
        api_key=settings.dashscope_api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        dimensions=settings.embedding_dim,
        check_embedding_ctx_length=False,  # DashScope 兼容模式需要
    )
    embeddings = LangchainEmbeddingsWrapper(embeddings_lc)

    result = evaluate(
        dataset,
        metrics=[
            __import__("ragas.metrics", fromlist=["context_precision"]).context_precision,
            __import__("ragas.metrics", fromlist=["context_recall"]).context_recall,
            __import__("ragas.metrics", fromlist=["faithfulness"]).faithfulness,
            __import__("ragas.metrics", fromlist=["answer_relevancy"]).answer_relevancy,
        ],
        llm=judge,
        embeddings=embeddings,
    )
    return {k: float(v) for k, v in result.scores[0].items()}


def render_report(scores: dict[str, dict]) -> str:
    """生成对比 markdown 报告。"""
    lines = [
        "# M3 RAGAS 评测报告",
        "",
        "## 实验对比",
        "",
        "| 实验 | context_precision | context_recall | faithfulness | answer_relevancy |",
        "|---|---|---|---|---|",
    ]
    for name, m in scores.items():
        lines.append(
            f"| {name} "
            f"| {m.get('context_precision', 0):.3f} "
            f"| {m.get('context_recall', 0):.3f} "
            f"| {m.get('faithfulness', 0):.3f} "
            f"| {m.get('answer_relevancy', 0):.3f} |"
        )
    lines += [
        "",
        "## 指标说明",
        "",
        "- **context_precision**: 召回到的 chunk 里相关的比例 (越高越好)",
        "- **context_recall**: 标答相关的内容召回了多少 (越高越好)",
        "- **faithfulness**: 答案是否忠于上下文, 无幻觉 (越高越好)",
        "- **answer_relevancy**: 答案是否切题 (越高越好)",
        "",
        "## 实验配置",
        "",
        "- 文档: 3 篇 (rag-fundamentals / vector-db-comparison / agent-stack)",
        "- 评测集: 20 条 (见 dataset.jsonl)",
        "- 检索 top_k: 4",
        "- Hybrid 召回: BM25 + 向量, RRF (k=60) 融合",
        "- Rerank: DashScope qwen3-rerank",
        "- LLM: MiniMax-M3 (OpenAI 协议)",
        "- Embedding: MiniMax embo-01 (1536 dim)",
    ]
    return "\n".join(lines) + "\n"


async def main() -> None:
    items = load_dataset()
    print(f"=== loaded {len(items)} eval items ===\n")

    all_scores: dict[str, dict] = {}

    print(">>> [1/3] vector only")
    ds_vec = await run_vector_experiment(items)
    all_scores["vector"] = score(ds_vec, "vector")

    print("\n>>> [2/3] hybrid (BM25 + vec RRF)")
    ds_hyb = await run_hybrid_experiment(items)
    all_scores["hybrid"] = score(ds_hyb, "hybrid")

    print("\n>>> [3/3] hybrid + rerank")
    ds_hrr = await run_hybrid_rerank_experiment(items)
    all_scores["hybrid+rerank"] = score(ds_hrr, "hybrid+rerank")

    report = render_report(all_scores)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"\n=== report written to {REPORT_PATH} ===")
    print(report)


if __name__ == "__main__":
    # ragas 内部依赖 instructor, 设置环境避免 pydantic 警告刷屏
    os.environ.setdefault("PYTHONWARNINGS", "ignore")
    asyncio.run(main())
