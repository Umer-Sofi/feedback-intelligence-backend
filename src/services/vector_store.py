"""Vector storage + similarity search backed by Postgres + pgvector.

Embeddings live in dedicated tables, kept separate from the structured data:
  - feedback_chunks.embedding -> one vector PER PASSAGE of a feedback item
    (a long feedback is split into several chunks; powers RAG retrieval)
  - themes.embedding          -> one vector per named theme (theme matching)

Embeddings come from OpenAI (via openai_client.embed); pgvector does the
cosine-distance nearest-neighbor search. No clustering — grouping is
nearest-neighbor lookup. The public API is stable, so callers
(theme_aggregator, retrieval, pipeline, load_dataset) need no changes.
"""

from typing import Optional

from sqlalchemy import delete, select

from src.database.database import SessionLocal
from src.models.feedback import Feedback, FeedbackChunk, Theme
from src.services.chunking import chunk_text
from src.services.openai_client import embed


def add_feedback(feedback_id: int, text: str) -> None:
    """Chunk a feedback item, embed each chunk, and store the chunk rows."""
    chunks = chunk_text(text)
    if not chunks:
        return
    vectors = embed(chunks)
    db = SessionLocal()
    try:
        # Replace any existing chunks (e.g. if the item is re-processed).
        db.execute(
            delete(FeedbackChunk).where(
                FeedbackChunk.feedback_id == feedback_id
            )
        )
        for index, (chunk, vector) in enumerate(zip(chunks, vectors)):
            db.add(
                FeedbackChunk(
                    feedback_id=feedback_id,
                    chunk_index=index,
                    chunk_text=chunk,
                    embedding=vector,
                )
            )
        db.commit()
    finally:
        db.close()


def add_theme(theme_id: int, label: str, keywords: str) -> None:
    """Embed a theme's keywords and store the vector on its row."""
    vector = embed([keywords])[0]
    db = SessionLocal()
    try:
        theme = db.get(Theme, theme_id)
        if theme is not None:
            theme.keywords = keywords
            theme.embedding = vector
            db.commit()
    finally:
        db.close()


def nearest_theme(text: str) -> Optional[dict]:
    """Return the closest existing theme to `text`, or None if none exist.

    Returns {"theme_id", "label", "distance"}; distance is cosine distance
    (0.0 = identical, 2.0 = opposite).
    """
    vector = embed([text])[0]
    db = SessionLocal()
    try:
        distance = Theme.embedding.cosine_distance(vector)
        row = db.execute(
            select(Theme, distance.label("distance"))
            .where(Theme.embedding.is_not(None))
            .order_by(distance)
            .limit(1)
        ).first()
        if row is None:
            return None
        theme, dist = row
        return {
            "theme_id": theme.id,
            "label": theme.label,
            "distance": dist,
        }
    finally:
        db.close()


def search_feedback(
    query: str,
    n_results: int = 5,
    user_id: Optional[int] = None,
) -> list[dict]:
    """Return the feedback items most similar to `query` (for RAG).

    Searches at the chunk level, then collapses chunks back to their parent
    feedback so each item appears once, represented by its closest passage.
    When `user_id` is given, only that user's feedback is searched (this is
    what scopes a customer's bot to their own feedback; admins pass None).
    """
    vector = embed([query])[0]
    db = SessionLocal()
    try:
        distance = FeedbackChunk.embedding.cosine_distance(vector)
        stmt = select(FeedbackChunk, distance.label("distance")).where(
            FeedbackChunk.embedding.is_not(None)
        )
        if user_id is not None:
            stmt = stmt.join(
                Feedback, Feedback.id == FeedbackChunk.feedback_id
            ).where(Feedback.user_id == user_id)
        # Over-fetch: several top chunks may share a parent, so we need extra
        # rows to still end up with `n_results` distinct feedback items.
        rows = db.execute(
            stmt.order_by(distance).limit(n_results * 4)
        ).all()
        best: dict[int, dict] = {}
        for chunk, dist in rows:
            # Rows are distance-ordered, so the first chunk seen for a
            # feedback is its closest one — keep that, skip the rest.
            if chunk.feedback_id in best:
                continue
            best[chunk.feedback_id] = {
                "feedback_id": chunk.feedback_id,
                "text": chunk.chunk_text,
                "distance": dist,
            }
            if len(best) >= n_results:
                break
        return list(best.values())
    finally:
        db.close()
