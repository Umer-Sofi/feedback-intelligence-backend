"""Single entry point for all OpenAI calls.

Every LLM/embedding call in the app goes through here, so retry/backoff and
JSON validation live in exactly one place (see utils/retry.py).
"""

import json
from typing import Optional, Type, TypeVar

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from src.core.config import get_settings
from src.utils.logger import get_logger
from src.utils.retry import LLMValidationError, with_llm_retry

logger = get_logger(__name__)
settings = get_settings()

_client = OpenAI(api_key=settings.openai_api_key)

T = TypeVar("T", bound=BaseModel)


@with_llm_retry
def chat(
    messages: list[dict],
    model: Optional[str] = None,
    temperature: float = 0.0,
) -> str:
    """Return the assistant's plain-text reply for a chat completion."""
    response = _client.chat.completions.create(
        model=model or settings.openai_chat_model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


@with_llm_retry
def chat_json(
    messages: list[dict],
    schema: Type[T],
    model: Optional[str] = None,
    temperature: float = 0.0,
) -> T:
    """Return a schema-validated object from a JSON-mode completion.

    Raises LLMValidationError (caught by the retry policy) when the model
    returns malformed JSON or data that fails schema validation.
    """
    response = _client.chat.completions.create(
        model=model or settings.openai_classifier_model,
        messages=messages,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or ""
    try:
        return schema.model_validate(json.loads(content))
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.warning("LLM returned invalid JSON/schema: %s", exc)
        raise LLMValidationError(str(exc)) from exc


@with_llm_retry
def embed(
    texts: list[str], model: Optional[str] = None
) -> list[list[float]]:
    """Return one embedding vector per input text."""
    response = _client.embeddings.create(
        model=model or settings.openai_embedding_model,
        input=texts,
    )
    return [item.embedding for item in response.data]
