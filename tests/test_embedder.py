import numpy as np
import pytest
from ragchatbot.embedder import embed_chunks, embed_query


def test_embed_query_shape():
    vector = embed_query("what is the refund policy?")
    assert isinstance(vector, np.ndarray)
    assert vector.shape == (384,)


def test_embed_chunks_shape():
    chunks = ["first chunk text", "second chunk text", "third chunk text"]
    vectors = embed_chunks(chunks)
    assert isinstance(vectors, np.ndarray)
    assert vectors.shape == (3, 384)


def test_embed_single_chunk():
    vectors = embed_chunks(["only one chunk"])
    assert vectors.shape == (1, 384)


def test_embed_query_is_normalized():
    vector = embed_query("test query")
    norm = np.linalg.norm(vector)
    assert 0.9 < norm < 1.1  # roughly unit norm


def test_different_queries_different_vectors():
    v1 = embed_query("refund policy")
    v2 = embed_query("shipping times")
    assert not np.allclose(v1, v2)