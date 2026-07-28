"""Split feedback text into embedding-sized chunks.

Short feedback stays a single chunk; long feedback is split into overlapping
word windows so each passage embeds well and stays under the model's token
limit. The overlap keeps ideas that straddle a boundary retrievable.
"""

# ~200 words ≈ 260 tokens — comfortably under the embedding model's limit,
# while keeping each chunk topically focused.
MAX_WORDS = 200
OVERLAP_WORDS = 30


def chunk_text(
    text: str,
    max_words: int = MAX_WORDS,
    overlap_words: int = OVERLAP_WORDS,
) -> list[str]:
    """Split `text` into overlapping word windows.

    Returns a single chunk for short text, several for long text, and an
    empty list for blank input.
    """
    words = text.split()
    if not words:
        return []
    if len(words) <= max_words:
        return [" ".join(words)]

    step = max(1, max_words - overlap_words)
    chunks = []
    for start in range(0, len(words), step):
        window = words[start:start + max_words]
        chunks.append(" ".join(window))
        if start + max_words >= len(words):
            break
    return chunks
