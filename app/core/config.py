from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    """

    app_name: str = "NeuroMind"
    app_env: str = "development"
    debug: bool = True

    database_url: str

    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"

    embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 768

    qdrant_path: str = "./data/qdrant"
    qdrant_collection_name: str = "roadmap_chunks"

    rag_top_k: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    The environment file is read only once during the application lifecycle.
    """

    return Settings()


settings = get_settings()