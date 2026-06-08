import pytest
from ragchatbot.chunker import chunk_text


def test_empty_string():
    assert chunk_text("") == []


def test_short_text_single_chunk():
    text = "This is a short text."
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == "This is a short text."


def test_chunk_count():
    # 300 words should produce multiple chunks with default size 150, overlap 30
    words = ["word"] * 300
    text = " ".join(words)
    chunks = chunk_text(text)
    assert len(chunks) > 1


def test_overlap():
    # with chunk_size=10, overlap=3 — last 3 words of chunk N == first 3 words of chunk N+1
    words = [f"w{i}" for i in range(30)]
    text = " ".join(words)
    chunks = chunk_text(text, chunk_size=10, overlap=3)
    assert len(chunks) > 1
    end_of_first = chunks[0].split()[-3:]
    start_of_second = chunks[1].split()[:3]
    assert end_of_first == start_of_second


def test_chunk_size_respected():
    words = ["word"] * 500
    text = " ".join(words)
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    # no chunk should exceed chunk_size words
    for chunk in chunks:
        assert len(chunk.split()) <= 100


def test_no_empty_chunks():
    words = ["word"] * 200
    text = " ".join(words)
    chunks = chunk_text(text)
    for chunk in chunks:
        assert chunk.strip() != ""