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

    # Database (Postgres + pgvector — structured data AND vectors in one DB).
    database_url: str = (
        "postgresql+psycopg://feedback:feedback@localhost:5432/feedback"
    )
    # Dimension of the OpenAI embedding model (text-embedding-3-small = 1536).
    embedding_dim: int = 1536

    # Theme aggregation: below this cosine distance, join an existing theme.
    # Tuned for OpenAI embeddings vs theme-keyword vectors (median ~0.58).
    theme_similarity_threshold: float = 0.58

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
