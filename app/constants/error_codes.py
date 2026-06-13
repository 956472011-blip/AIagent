"""错误码定义。

企业级设计:
    - 统一的错误码定义
    - 错误信息标准化
    - 便于前端处理
"""
from __future__ import annotations


class ErrorCode:
    """错误码常量。"""

    # 认证相关 (1000-1999)
    INVALID_TOKEN = 1000
    TOKEN_EXPIRED = 1001
    INVALID_CREDENTIALS = 1002
    USER_NOT_FOUND = 1003
    USER_ALREADY_EXISTS = 1004

    # RAG 相关 (2000-2999)
    RETRIEVAL_FAILED = 2000
    GENERATION_FAILED = 2001
    NO_DOCUMENTS_FOUND = 2002

    # Agent 相关 (3000-3999)
    AGENT_EXECUTION_FAILED = 3000
    INTENT_CLASSIFICATION_FAILED = 3001
    FAITHFULNESS_CHECK_FAILED = 3002

    # 通用错误 (9000-9999)
    INTERNAL_ERROR = 9000
    INVALID_REQUEST = 9001
    SERVICE_UNAVAILABLE = 9002


ERROR_MESSAGES = {
    ErrorCode.INVALID_TOKEN: "Token 无效",
    ErrorCode.TOKEN_EXPIRED: "Token 已过期",
    ErrorCode.INVALID_CREDENTIALS: "用户名或密码错误",
    ErrorCode.USER_NOT_FOUND: "用户不存在",
    ErrorCode.USER_ALREADY_EXISTS: "用户名已存在",
    ErrorCode.RETRIEVAL_FAILED: "检索失败",
    ErrorCode.GENERATION_FAILED: "生成失败",
    ErrorCode.NO_DOCUMENTS_FOUND: "未找到相关文档",
    ErrorCode.AGENT_EXECUTION_FAILED: "Agent 执行失败",
    ErrorCode.INTENT_CLASSIFICATION_FAILED: "意图分类失败",
    ErrorCode.FAITHFULNESS_CHECK_FAILED: "忠实度检查失败",
    ErrorCode.INTERNAL_ERROR: "内部错误",
    ErrorCode.INVALID_REQUEST: "请求参数无效",
    ErrorCode.SERVICE_UNAVAILABLE: "服务暂不可用",
}
