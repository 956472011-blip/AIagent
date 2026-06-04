"""应用配置。

用 pydantic-settings 读取环境变量,启动时做强类型校验。
设计原则: fail fast —— 配错就启动不起来,绝不带到运行时。
"""
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置单例。

    Java 类比:
        @ConfigurationProperties(prefix = "app")
        + @Validated 启动校验
        + application.yml (这里换成 .env 文件)
    """

    # model_config ≈ Spring 的 @ConfigurationProperties 元配置
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # APP_NAME 和 app_name 都能匹配
        extra="ignore",        # .env 里多余的字段不报错(M3+ 阶段会改成 "forbid")
    )

    # === Application ===
    app_name: str = "rag-assistant"
    app_env: Literal["dev", "staging", "prod"] = "dev"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # === Server ===
    host: str = "0.0.0.0"
    port: int = 8000

    # === LLM (M1+ 启用,M0 阶段可为空) ===
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    # === Qdrant (M2+ 启用,M0 阶段可为空) ===
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_collection: str = "docs"

    # === Embedding (M2+ 启用) ===
    embedding_model: str = "embo-01"
    embedding_dim: int = 1536


# 模块级单例:整个进程共享一份配置
# Java 类比: @Configuration class AppConfig { @Bean Settings settings() {...} }
# 用法: from app.core.config import settings
settings = Settings()
