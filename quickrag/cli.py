import os
import typer
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

app = typer.Typer(
    name="quickrag",
    help="Drop-in RAG SDK for website chatbots.",
    add_completion=False
)


# ── INIT ──────────────────────────────────────────────────────────────────────

@app.command()
def init():
    """Scaffold a new quickrag project in current directory."""

    typer.echo("Initializing quickrag project...")

    # create folders
    folders = ["docs", "chroma_db", "model_cache"]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        typer.echo(f"  created {folder}/")

    # create .env if not exists
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("GEMINI_API_KEY=your-gemini-api-key\n")
            f.write("quickrag_DOCS=./docs\n")
            f.write("quickrag_DB=./chroma_db\n")
            f.write("quickrag_LLM=gemini\n")
            f.write("HF_HUB_OFFLINE=0\n")
        typer.echo("  created .env")
    else:
        typer.echo("  .env already exists — skipping")

    # create .gitignore if not exists
    if not os.path.exists(".gitignore"):
        with open(".gitignore", "w") as f:
            f.write("myenv/\n")
            f.write("chroma_db/\n")
            f.write("model_cache/\n")
            f.write("__pycache__/\n")
            f.write("*.pyc\n")
            f.write(".env\n")
            f.write("*.egg-info/\n")
        typer.echo("  created .gitignore")
    else:
        typer.echo("  .gitignore already exists — skipping")

    typer.echo("\nDone. Next steps:")
    typer.echo("  1. Add your docs to docs/")
    typer.echo("  2. Set GEMINI_API_KEY in .env")
    typer.echo("  3. Run: quickrag verify")
    typer.echo("  4. Run: quickrag start")


# ── VERIFY ────────────────────────────────────────────────────────────────────

@app.command()
def verify():
    """Check all config, dependencies, and connections are working."""

    typer.echo("Verifying quickrag setup...\n")
    all_ok = True

    # check docs folder
    docs = os.getenv("quickrag_DOCS", "./docs")
    if os.path.exists(docs):
        files = [f for f in os.listdir(docs) if f.endswith((".md", ".txt"))]
        if files:
            typer.echo(f"  ✅ docs folder — {len(files)} file(s) found")
        else:
            typer.echo(f"  ⚠️  docs folder exists but no .md or .txt files found")
            all_ok = False
    else:
        typer.echo(f"  ❌ docs folder not found: {docs}")
        all_ok = False

    # check gemini api key
    llm = os.getenv("quickrag_LLM", "gemini")
    if llm == "gemini":
        key = os.getenv("GEMINI_API_KEY", "")
        if key and key != "your-gemini-api-key":
            typer.echo(f"  ✅ GEMINI_API_KEY — set")
        else:
            typer.echo(f"  ❌ GEMINI_API_KEY — not set in .env")
            all_ok = False

    # check ollama connection
    if llm == "ollama":
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            response.raise_for_status()
            typer.echo(f"  ✅ Ollama server — running")
        except Exception:
            typer.echo(f"  ❌ Ollama server — not running. Start with: ollama serve")
            all_ok = False

    # check chromadb
    try:
        import chromadb
        db_path = os.getenv("quickrag_DB", "./chroma_db")
        client = chromadb.PersistentClient(path=db_path)
        typer.echo(f"  ✅ ChromaDB — connected")
    except Exception as e:
        typer.echo(f"  ❌ ChromaDB — {str(e)}")
        all_ok = False

    # check embedding model
    try:
        from sentence_transformers import SentenceTransformer
        SentenceTransformer("all-MiniLM-L6-v2", cache_folder="./model_cache")
        typer.echo(f"  ✅ Embedding model — loaded")
    except Exception as e:
        typer.echo(f"  ❌ Embedding model — {str(e)}")
        all_ok = False

    # final verdict
    typer.echo("")
    if all_ok:
        typer.echo("All checks passed. Run: quickrag start")
    else:
        typer.echo("Fix the issues above then run verify again.")


# ── START ─────────────────────────────────────────────────────────────────────

@app.command()
def start(
    host: str = typer.Option("0.0.0.0", help="Host to bind server to."),
    port: int = typer.Option(8000, help="Port to run server on."),
    llm: str = typer.Option(None, help="LLM to use: gemini or ollama."),
    reload: bool = typer.Option(False, help="Auto-reload on code changes.")
):
    """Index docs and start the quickrag API server."""

    # override LLM from flag or fall back to .env
    if llm:
        os.environ["quickrag_LLM"] = llm

    typer.echo(f"Starting quickrag server on http://localhost:{port}")
    typer.echo(f"API docs at http://localhost:{port}/docs\n")

    import uvicorn
    uvicorn.run(
        "quickrag.server:app",
        host=host,
        port=port,
        reload=reload
    )


# ── ASK ───────────────────────────────────────────────────────────────────────

@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask."),
    llm: str = typer.Option(None, help="LLM to use: gemini or ollama."),
    n_results: int = typer.Option(3, help="Number of chunks to retrieve.")
):
    """Ask a question directly from terminal."""

    from quickrag import RAG

    llm = llm or os.getenv("quickrag_LLM", "gemini")
    docs = os.getenv("quickrag_DOCS", "./docs")
    db = os.getenv("quickrag_DB", "./chroma_db")

    rag = RAG(docs=docs, db_path=db, llm=llm, n_results=n_results)
    rag.index()

    result = rag.ask(question)

    typer.echo(f"\nAnswer:\n{result['answer']}")
    typer.echo(f"\nSources: {', '.join(result['sources'])}")


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

def main():
    app()


if __name__ == "__main__":
    main()