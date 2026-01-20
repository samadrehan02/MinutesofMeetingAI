def chunk_text(text: str, max_chars: int = 3000) -> list[str]:
    chunks = []
    current = ""

    for line in text.split(". "):
        if len(current) + len(line) < max_chars:
            current += line + ". "
        else:
            chunks.append(current.strip())
            current = line + ". "

    if current.strip():
        chunks.append(current.strip())

    return chunks
