"""Shared retry/backoff policy for all LLM calls (built on tenacity)."""

from openai import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.core.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class LLMValidationError(Exception):
    """Raised when an LLM response fails JSON parsing or schema validation.

    Raising this triggers a retry via the shared policy below.
    """


# Retry on transient API problems AND on our own validation failures.
_RETRYABLE = (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
    LLMValidationError,
)


def with_llm_retry(func):
    """Wrap an LLM call with exponential backoff + validation retries.

    All timing/attempt values come from settings, so behaviour is tunable
    from .env without touching code.
    """
    return retry(
        reraise=True,
        stop=stop_after_attempt(settings.retry_max_attempts),
        wait=wait_exponential(
            multiplier=settings.retry_initial_wait,
            max=settings.retry_max_wait,
        ),
        retry=retry_if_exception_type(_RETRYABLE),
        before_sleep=lambda state: logger.warning(
            "Retrying LLM call (attempt %d): %s",
            state.attempt_number,
            state.outcome.exception(),
        ),
    )(func)
