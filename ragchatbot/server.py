import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from ragchatbot import RAG
from ragchatbot.store import collection_stats
import json
from fastapi.responses import StreamingResponse

load_dotenv()


# ── REQUEST / RESPONSE MODELS ─────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str
    llm: str = None
    n_results: int = 3
    stream: bool = False


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    question: str


# ── AUTH ──────────────────────────────────────────────────────────────────────

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    """
    Check X-API-Key header if RAGCHATBOT_API_KEY is set in .env.
    If RAGCHATBOT_API_KEY is not set — auth is disabled, all requests pass.
    """
    expected = os.getenv("RAGCHATBOT_API_KEY", "")

    if not expected:
        # auth not configured — open access
        return

    if api_key != expected:
        raise HTTPException(
            status_code=401,
            detail="❌ Invalid or missing API key. Pass it as X-API-Key header."
        )


# ── APP STATE ─────────────────────────────────────────────────────────────────

_rag_instances: dict = {}

def get_rag(llm: str, n_results: int) -> RAG:
    """Get or create RAG instance for given LLM."""
    if llm not in _rag_instances:
        _rag_instances[llm] = RAG(
            docs=os.getenv("ragchatbot_DOCS", "./docs"),
            db_path=os.getenv("ragchatbot_DB", "./chroma_db"),
            llm=llm,
            n_results=n_results
        )
    return _rag_instances[llm]


# ── LIFESPAN ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Index docs when server starts."""
    print("ragchatbot server starting...")
    docs = os.getenv("ragchatbot_DOCS", "./docs")
    db = os.getenv("ragchatbot_DB", "./chroma_db")
    default_llm = os.getenv("ragchatbot_LLM", "gemini")

    rag = RAG(docs=docs, db_path=db, llm=default_llm)
    rag.index()
    _rag_instances[default_llm] = rag

    if os.getenv("RAGCHATBOT_API_KEY"):
        print("Auth enabled — X-API-Key header required on /ask")
    else:
        print("Auth disabled — set RAGCHATBOT_API_KEY in .env to enable")

    print("ragchatbot server ready.")
    yield
    print("ragchatbot server shutting down.")


# ── FASTAPI APP ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="ragchatbot",
    description="Drop-in RAG API for your website",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Check server is running."""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/stats")
def stats():
    """Return indexing stats."""
    db = os.getenv("ragchatbot_DB", "./chroma_db")
    collection_stats(db)
    return {"status": "ok"}

@app.post("/ask", dependencies=[Depends(verify_api_key)])
def ask(request: AskRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        llm = request.llm or os.getenv("ragchatbot_LLM", "gemini")
        rag = get_rag(llm, request.n_results)

        if request.stream:
            sources, token_stream = rag.ask_stream(request.question)

            def event_stream():
                for token in token_stream:
                    yield token
                yield f"\n\n__sources__:{json.dumps(sources)}"

            return StreamingResponse(event_stream(), media_type="text/plain")

        else:
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