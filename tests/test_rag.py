import os
import shutil
import tempfile
import pytest


@pytest.fixture
def rag_setup(tmp_path):
    """Create a temp docs folder with a txt file and a temp db."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "policy.txt").write_text(
        "Our refund policy allows returns within 30 days of purchase. "
        "Contact support@example.com to initiate a refund."
    )
    db = str(tmp_path / "chroma")
    yield str(docs), db
    shutil.rmtree(db, ignore_errors=True)


def test_index_and_ask(rag_setup):
    from ragchatbot import RAG

    docs, db = rag_setup
    rag = RAG(docs=docs, db_path=db, llm="gemini")

    # patch LLM so we don't make real API calls
    class MockLLM:
        def generate(self, question, chunks):
            return {
                "answer": f"mock answer using {len(chunks)} chunks",
                "sources": [c["source"] for c in chunks]
            }
        def _extract_sources(self, chunks):
            return list({c["source"] for c in chunks})
        def generate_stream(self, question, chunks):
            yield "mock"
            yield " stream"

    rag.llm = MockLLM()
    rag.index()

    result = rag.ask("what is the refund policy?")
    assert "answer" in result
    assert "sources" in result
    assert isinstance(result["sources"], list)


def test_index_missing_docs_raises():
    from ragchatbot import RAG
    rag = RAG(docs="./nonexistent_folder_xyz", db_path="./tmp_db")
    with pytest.raises(FileNotFoundError):
        rag.index()


def test_ask_stream(rag_setup):
    from ragchatbot import RAG

    docs, db = rag_setup
    rag = RAG(docs=docs, db_path=db, llm="gemini")

    class MockLLM:
        def generate(self, question, chunks):
            return {"answer": "mock", "sources": []}
        def _extract_sources(self, chunks):
            return []
        def generate_stream(self, question, chunks):
            yield "token1"
            yield " token2"

    rag.llm = MockLLM()
    rag.index()

    sources, stream = rag.ask_stream("test question")
    tokens = list(stream)
    assert "token1" in tokens
    assert isinstance(sources, list)