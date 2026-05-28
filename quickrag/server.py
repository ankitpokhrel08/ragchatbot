import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from quickrag import RAG
from quickrag.store import collection_stats

load_dotenv()


# ── REQUEST / RESPONSE MODELS ─────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str
    llm: str = "gemini"        # "gemini" or "ollama"
    n_results: int = 3


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    question: str


# ── APP STATE ─────────────────────────────────────────────────────────────────

# rag instances cached per llm type — don't recreate on every request
_rag_instances: dict = {}

def get_rag(llm: str, n_results: int) -> RAG:
    """Get or create RAG instance for given LLM."""
    if llm not in _rag_instances:
        _rag_instances[llm] = RAG(
            docs=os.getenv("quickrag_DOCS", "./docs"),
            db_path=os.getenv("quickrag_DB", "./chroma_db"),
            llm=llm,
            n_results=n_results
        )
    return _rag_instances[llm]


# ── LIFESPAN — index on startup ───────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Index docs when server starts."""
    print("quickrag server starting...")
    docs = os.getenv("quickrag_DOCS", "./docs")
    db = os.getenv("quickrag_DB", "./chroma_db")
    default_llm = os.getenv("quickrag_LLM", "gemini")

    rag = RAG(docs=docs, db_path=db, llm=default_llm)
    rag.index()
    _rag_instances[default_llm] = rag

    print("quickrag server ready.")
    yield
    print("quickrag server shutting down.")


# ── FASTAPI APP ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="quickrag",
    description="Drop-in RAG API for your website",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # restrict to your domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Check server is running."""
    return {"status": "ok", "version": "0.1.0"}


@app.get("/stats")
def stats():
    """Return indexing stats."""
    db = os.getenv("quickrag_DB", "./chroma_db")
    collection_stats(db)
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """
    Ask a question against indexed docs.

    Body:
        question:  user's question string
        llm:       "gemini" or "ollama" (default: "gemini")
        n_results: number of chunks to retrieve (default: 3)

    Returns:
        answer:   LLM generated answer
        sources:  list of source filenames
        question: echo of original question
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        rag = get_rag(request.llm, request.n_results)
        result = rag.ask(request.question)
        return AskResponse(
            answer=result["answer"],
            sources=result["sources"],
            question=request.question
        )
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))