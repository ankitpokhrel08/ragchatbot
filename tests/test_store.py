import os
import shutil
import numpy as np
import pytest
import ragchatbot.store as store_module

from ragchatbot.store import (
    add_chunks,
    query_chunks,
    delete_file_chunks,
    get_indexed_files,
    is_file_indexed,
    hash_file,
)


@pytest.fixture(autouse=True)
def reset_store_singleton():
    """Reset ChromaDB singleton before each test so tmp_db paths work correctly."""
    store_module._client = None
    store_module._collection = None
    yield
    store_module._client = None
    store_module._collection = None


@pytest.fixture
def tmp_db(tmp_path):
    db_path = str(tmp_path / "test_chroma")
    yield db_path
    shutil.rmtree(db_path, ignore_errors=True)


@pytest.fixture
def sample_embeddings():
    return np.random.rand(3, 384).astype(np.float32)


def test_add_and_query(tmp_db, sample_embeddings):
    chunks = ["refunds take 5 days", "shipping is free", "contact us anytime"]
    add_chunks("policy.md", chunks, sample_embeddings, "hash123", tmp_db)

    query_vec = sample_embeddings[0]
    results = query_chunks(query_vec, n_results=2, db_path=tmp_db)
    assert len(results) == 2
    assert "text" in results[0]
    assert "source" in results[0]
    assert "score" in results[0]


def test_get_indexed_files(tmp_db, sample_embeddings):
    chunks = ["chunk one", "chunk two", "chunk three"]
    add_chunks("faq.md", chunks, sample_embeddings, "hash456", tmp_db)
    files = get_indexed_files(tmp_db)
    assert "faq.md" in files


def test_delete_file_chunks(tmp_db, sample_embeddings):
    chunks = ["to be deleted", "also deleted", "gone too"]
    add_chunks("temp.md", chunks, sample_embeddings, "hash789", tmp_db)
    assert "temp.md" in get_indexed_files(tmp_db)

    delete_file_chunks("temp.md", tmp_db)
    assert "temp.md" not in get_indexed_files(tmp_db)


def test_is_file_indexed(tmp_db, sample_embeddings):
    chunks = ["some content here", "more content", "final content"]
    add_chunks("terms.md", chunks, sample_embeddings, "myhash", tmp_db)
    assert is_file_indexed("terms.md", "myhash", tmp_db) is True
    assert is_file_indexed("terms.md", "wronghash", tmp_db) is False


def test_empty_db_returns_empty(tmp_db):
    assert get_indexed_files(tmp_db) == set()


def test_hash_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello world")
    h1 = hash_file(str(f))
    h2 = hash_file(str(f))
    assert h1 == h2
    assert len(h1) == 32

    f.write_text("changed content")
    h3 = hash_file(str(f))
    assert h1 != h3