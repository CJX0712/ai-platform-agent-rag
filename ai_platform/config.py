"""配置中心：env 驱动，单一职责。

通过 pydantic-settings 加载环境变量（前缀 APP_），所有模块共享同一 Settings 单例。
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置。所有取值均可通过 APP_<NAME> 环境变量覆盖。"""

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    # 基础
    app_name: str = "AI Platform Agent-RAG"
    env: str = "dev"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    cors_origins: list[str] = ["*"]

    # 鉴权（默认关闭，便于离线演示；生产建议开启）
    auth_enabled: bool = False
    jwt_secret: str = "dev-secret-change-me"
    jwt_alg: str = "HS256"
    access_token_expire_min: int = 60
    demo_username: str = "demo"
    demo_password: str = "demo1234"

    # 限流
    rate_limit_per_min: int = 60

    # 模型供给（mock / ollama / openai 兼容）
    llm_provider: str = "mock"
    llm_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:3b"
    llm_api_key: str = ""
    llm_temperature: float = 0.2

    # 向量化（hash 免下载 / sentence-transformers 真实模型）
    embedding_provider: str = "hash"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 256

    # 存储
    chroma_path: str = "./data/chroma"
    chroma_collection: str = "docs"
    database_url: str = "sqlite:///./data/app.db"


@lru_cache
def get_settings() -> Settings:
    """返回进程内唯一的 Settings 单例。"""
    return Settings()
