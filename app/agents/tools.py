"""Agent 工具集。

企业级设计:
    - 用 @tool 装饰器定义工具,自动生成 JSON Schema
    - 每个工具是单一职责,易于测试和维护
    - 工具名/描述清晰,LLM 才能选对

类比 Java:
    Tool ≈ Spring 的 Bean,但 LLM 知道它的存在并能调用
    @tool 装饰器 ≈ 自动生成 Swagger 接口文档
"""
from __future__ import annotations

import ast
import operator
import re

from langchain_core.documents import Document
from langchain_core.tools import tool

from app.rag.hybrid_retriever import get_hybrid_retriever
from app.rag.reranker import get_reranker


# ===== 工具 1: 知识库检索 =====

@tool
async def rag_search(query: str, top_k: int = 4) -> str:
    """在企业知识库中检索相关内容。

    使用场景: 用户问业务相关问题(产品、流程、政策、技术文档)时调用。
    检索过程: BM25 + 向量混合召回 + DashScope Rerank 精排。

    Args:
        query: 用户问题(支持中文)
        top_k: 返回的文档条数,默认 4

    Returns:
        格式化的检索结果,每条包含来源和内容预览
    """
    try:
        retriever = get_hybrid_retriever()
        await retriever.warmup()
        retriever.top_n = 20
        retriever.k = 20

        candidates: list[Document] = await retriever.retrieve(query)

        if not candidates:
            return "知识库中未找到相关内容。"

        if len(candidates) > top_k:
            reranker = get_reranker()
            chunks = await reranker.rerank(query, candidates, top_k=top_k)
        else:
            chunks = candidates[:top_k]

        # 格式化输出,LLM 看到的就是 Markdown 文本
        lines = [f"找到 {len(chunks)} 条相关文档:\n"]
        for i, chunk in enumerate(chunks, start=1):
            source = chunk.metadata.get("source", "未知来源")
            content = chunk.page_content.strip()[:300]
            lines.append(f"[{i}] 来源: {source}\n{content}\n")

        return "\n".join(lines)
    except Exception as exc:
        return f"检索出错: {exc}"


# ===== 工具 2: 计算器 =====

# AST 安全求值,避免 eval 注入
_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _safe_eval(expr: str) -> float:
    """安全地计算数学表达式(白名单 AST 解析,不允许函数/变量)。"""
    tree = ast.parse(expr, mode="eval")
    return _eval_node(tree.body)


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        op_func = _BIN_OPS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"不支持的运算符: {type(node.op).__name__}")
        return op_func(_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp):
        op_func = _UNARY_OPS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"不支持的一元运算符: {type(node.op).__name__}")
        return op_func(_eval_node(node.operand))
    raise ValueError(f"不支持的表达式: {ast.dump(node)}")


@tool
def calculator(expression: str) -> str:
    """计算数学表达式。

    使用场景: 用户问算术题、百分比、单位换算等纯数学问题时调用。
    支持 + - * / // % ** 运算符和括号。

    Args:
        expression: 数学表达式,如 "(25 + 17) * 3" 或 "2 ** 10"

    Returns:
        计算结果字符串

    示例:
        calculator("2 + 3 * 4") → "14"
    """
    try:
        # 简单清理,只保留数字和运算符
        cleaned = re.sub(r"\s+", "", expression)
        result = _safe_eval(cleaned)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return f"{expression} = {result}"
    except Exception as exc:
        return f"计算失败: {exc}"


# ===== 导出 =====

ALL_TOOLS = [rag_search, calculator]
"""Agent 可用的所有工具列表。"""
