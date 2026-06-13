"""聊天会话模型。

企业级设计:
    - 支持多轮对话历史记录
    - 会话管理(Session)
    - 消息存储(Message)
"""
from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel


class ChatSession(SQLModel, table=True):
    """聊天会话。"""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    title: str | None = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 关系: 一个会话包含多条消息
    messages: list["ChatMessage"] = Relationship(back_populates="session")

    class Config:
        from_attributes = True


class ChatMessage(SQLModel, table=True):
    """聊天消息。"""

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chatsession.id", index=True)
    role: str = Field(max_length=10)  # "user" 或 "assistant"
    content: str
    faithfulness_score: float | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)

    # 关系: 一条消息属于一个会话
    session: ChatSession = Relationship(back_populates="messages")

    class Config:
        from_attributes = True