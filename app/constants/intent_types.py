"""意图类型常量。

企业级设计:
    - 统一的常量定义
    - 避免魔法字符串
    - 便于维护和扩展
"""
from __future__ import annotations


class IntentType:
    """意图类型常量。"""

    GREETING = "greeting"
    QUESTION = "question"
    CHITCHAT = "chitchat"  # 闲聊(未来扩展)
    COMMAND = "command"  # 命令(未来扩展)

    @classmethod
    def all(cls) -> list[str]:
        """获取所有意图类型。"""
        return [cls.GREETING, cls.QUESTION, cls.CHITCHAT, cls.COMMAND]
