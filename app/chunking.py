def chunk_text(text: str, chunk_size: int = 4000, overlap: int = 600):
    """
    Split text into overlapping chunks by character count.
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]

        # Try not to cut mid-sentence
        if end < text_length:
            last_period = chunk.rfind(".")
            if last_period != -1:
                chunk = chunk[: last_period + 1]
                end = start + len(chunk)

        chunks.append(chunk)
        start = end - overlap

        if start < 0:
            start = 0

    return chunks
