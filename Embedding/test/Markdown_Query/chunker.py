def chunk_text(text: str, chunk_size: int = 150, overlap: int = 30) -> list[str]:
    """
    Split text into overlapping chunks by word count.

    chunk_size: target words per chunk
    overlap:    words repeated between consecutive chunks
    """

    words = text.split()
    total_words = len(words)

    if total_words == 0:
        return []

    # If text is shorter than one chunk — return as single chunk
    if total_words <= chunk_size:
        return [" ".join(words)]

    chunks = []
    start = 0

    while start < total_words:
        end = start + chunk_size

        chunk_words = words[start:end]
        chunk = " ".join(chunk_words)
        chunks.append(chunk)

        # Move start forward by (chunk_size - overlap)
        # This creates the overlap on next iteration
        step = chunk_size - overlap
        start += step

        # Avoid tiny leftover chunks at the end
        # If remaining words < half chunk size, fold into last chunk
        remaining = total_words - start
        if 0 < remaining < chunk_size // 2:
            final_chunk = " ".join(words[start:])
            chunks.append(final_chunk)
            break

    return chunks