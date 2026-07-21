"""ChromaDB wrapper: persistent vector storage + similarity search.

Two collections back the app:
  - feedback_embeddings: one vector per feedback item (powers RAG retrieval)
  - feedback_themes:     one vector per named theme (powers theme matching)

Embeddings come from OpenAI (via openai_client.embed); Chroma only stores
and searches them. No clustering — grouping is nearest-neighbor lookup.
"""

import logging
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.core.config import get_settings
from src.services.openai_client import embed
from src.utils.logger import get_logger

# ChromaDB 0.5.3 emits noisy, harmless telemetry errors; silence that logger.
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(
    logging.CRITICAL
)

logger = get_logger(__name__)
settings = get_settings()

FEEDBACK_COLLECTION = "feedback_embeddings"
THEME_COLLECTION = "feedback_themes"

_client = chromadb.PersistentClient(
    path=settings.chroma_persist_dir,
    settings=ChromaSettings(anonymized_telemetry=False),
)


def _get_collection(name: str):
    """Get or create a collection configured for cosine distance."""
    return _client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def add_feedback(feedback_id: int, text: str) -> None:
    """Embed and store a single feedback item."""
    vector = embed([text])[0]
    _get_collection(FEEDBACK_COLLECTION).upsert(
        ids=[str(feedback_id)],
        embeddings=[vector],
        documents=[text],
        metadatas=[{"feedback_id": feedback_id}],
    )


def add_theme(theme_id: int, label: str, keywords: str) -> None:
    """Embed and store a theme's representative text."""
    vector = embed([keywords])[0]
    _get_collection(THEME_COLLECTION).upsert(
        ids=[str(theme_id)],
        embeddings=[vector],
        documents=[keywords],
        metadatas=[{"theme_id": theme_id, "label": label}],
    )


def nearest_theme(text: str) -> Optional[dict]:
    """Return the closest existing theme to `text`, or None if none exist.

    Returns {"theme_id", "label", "distance"}; distance is cosine distance
    (0.0 = identical, 2.0 = opposite).
    """
    collection = _get_collection(THEME_COLLECTION)
    if collection.count() == 0:
        return None
    vector = embed([text])[0]
    res = collection.query(query_embeddings=[vector], n_results=1)
    if not res["ids"] or not res["ids"][0]:
        return None
    meta = res["metadatas"][0][0]
    return {
        "theme_id": meta["theme_id"],
        "label": meta["label"],
        "distance": res["distances"][0][0],
    }


def search_feedback(query: str, n_results: int = 5) -> list[dict]:
    """Return the feedback items most similar to `query` (for RAG)."""
    collection = _get_collection(FEEDBACK_COLLECTION)
    if collection.count() == 0:
        return []
    vector = embed([query])[0]
    res = collection.query(query_embeddings=[vector], n_results=n_results)
    items = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        items.append(
            {"feedback_id": meta["feedback_id"], "text": doc, "distance": dist}
        )
    return items
