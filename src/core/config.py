"""Application settings loaded from environment / .env via pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str
    openai_classifier_model: str = "gpt-4o-mini"
    openai_summary_model: str = "gpt-4o-mini"
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # Databases (file-based, no server)
    database_url: str = "sqlite:///./feedback.db"
    chroma_persist_dir: str = "./chroma_store"

    # Theme aggregation: below this cosine distance, join an existing theme.
    theme_similarity_threshold: float = 0.35

    # Classifications below this confidence get flagged for review.
    low_confidence_threshold: float = 0.6

    # Retry / backoff
    retry_max_attempts: int = 4
    retry_initial_wait: float = 1.0
    retry_max_wait: float = 20.0

    # App
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (read the .env only once)."""
    return Settings()
