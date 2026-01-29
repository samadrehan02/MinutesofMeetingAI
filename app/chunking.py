def estimate_tokens(text: str) -> int:
    # Conservative heuristic: ~4 chars per token
    return max(1, len(text) // 4)


def chunk_text(
    text: str,
    chunk_size_chars: int = 4000,
    overlap_chars: int = 600,
    max_chunk_tokens: int = 1200,
    max_chunks: int = 50,
):
    """
    Split text into overlapping chunks with token-aware safety caps.

    Behavior notes:
    - Uses character-based chunking (same as before)
    - Adds token estimation to prevent pathological cases
    - Preserves sentence boundaries where possible
    - Caps total chunks defensively
    """

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length and len(chunks) < max_chunks:
        end = min(start + chunk_size_chars, text_length)
        chunk = text[start:end]

        # Try not to cut mid-sentence
        if end < text_length:
            last_period = chunk.rfind(".")
            if last_period != -1:
                chunk = chunk[: last_period + 1]
                end = start + len(chunk)

        # Token safety check
        if estimate_tokens(chunk) > max_chunk_tokens:
            # Hard truncate to stay within token cap
            approx_chars = max_chunk_tokens * 4
            chunk = chunk[:approx_chars]
            end = start + len(chunk)

        chunks.append(chunk)

        # Advance with overlap
        start = end - overlap_chars
        if start < 0:
            start = 0

    return chunks
