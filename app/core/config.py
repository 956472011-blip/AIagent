"""应用配置。

企业级设计:
    - pydantic-settings 读取环境变量
    - 启动时强类型校验,配置错误立即报错
    - 敏感信息通过 .env 管理,不提交到 git
"""
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置单例。

    类比 Java:
        @ConfigurationProperties(prefix = "app")
        + @Validated 启动校验
    """

    # 配置元信息
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === Application ===
    app_name: str = "rag-assistant"
    app_env: Literal["dev", "staging", "prod"] = "dev"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # === Server ===
    host: str = "0.0.0.0"
    port: int = 8000

    # === LLM ===
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    # === Qdrant ===
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_collection: str = "docs"

    # === Embedding ===
    embedding_model: str = "embo-01"
    embedding_dim: int = 1536

    # === Rerank ===
    dashscope_api_key: str | None = None

    # === Database (PostgreSQL) ===
    database_url: str = "postgresql://postgres:password@localhost:5432/aiagent"

    # === JWT Authentication ===
    jwt_secret_key: str = "your-secret-key-change-in-production"  # 生产环境必须修改
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30  # Token 过期时间(分钟)


# 全局单例
settings = Settings()
