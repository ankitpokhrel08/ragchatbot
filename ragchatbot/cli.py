import os
import typer
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

app = typer.Typer(
    name="ragchatbot",
    help="Drop-in RAG SDK for website chatbots.",
    add_completion=False
)

#Setup Command
# ── SETUP ─────────────────────────────────────────────────────────────────────

@app.command()
def setup():
    """Guided setup — configure LLM, index docs, get started."""

    typer.echo("\n── ragchatbot setup ──\n")

    # ── STEP 1: choose LLM ────────────────────────────────────────────────────
    typer.echo("Step 1: Choose your LLM\n")
    typer.echo("  1. Gemini  (free, recommended)")
    typer.echo("  2. OpenAI")
    typer.echo("  3. Ollama  (local, no API key)\n")

    llm_choice = typer.prompt("Enter number").strip()

    llm_map = {"1": "gemini", "2": "openai", "3": "ollama"}
    if llm_choice not in llm_map:
        typer.echo("❌ Invalid choice. Run setup again.")
        raise typer.Exit(1)

    llm = llm_map[llm_choice]

    # ── STEP 2: choose model ──────────────────────────────────────────────────
    typer.echo(f"\nStep 2: Choose model\n")

    model_options = {
        "gemini": [
            ("gemini-2.0-flash", "recommended"),
            ("gemini-1.5-pro", "more capable, slower"),
        ],
        "openai": [
            ("gpt-4o-mini", "recommended"),
            ("gpt-4o", "more capable, higher cost"),
        ],
        "ollama": [
            ("llama3.2", "recommended"),
            ("mistral", ""),
        ],
    }

    options = model_options[llm]
    for i, (name, note) in enumerate(options, 1):
        label = f"  {i}. {name}"
        if note:
            label += f"  ({note})"
        typer.echo(label)
    typer.echo(f"  {len(options) + 1}. Other (type manually)\n")

    model_choice = typer.prompt("Enter number").strip()

    if model_choice.isdigit() and 1 <= int(model_choice) <= len(options):
        model = options[int(model_choice) - 1][0]
    elif model_choice == str(len(options) + 1):
        model = typer.prompt("Enter model name").strip()
    else:
        typer.echo("❌ Invalid choice. Run setup again.")
        raise typer.Exit(1)

    # ── STEP 3: API key ───────────────────────────────────────────────────────
    api_key = ""
    if llm != "ollama":
        typer.echo(f"\nStep 3: API key\n")

        key_hints = {
            "gemini": "Get a free key at: https://aistudio.google.com",
            "openai": "Get a key at: https://platform.openai.com/api-keys",
        }
        typer.echo(f"  {key_hints[llm]}\n")
        api_key = typer.prompt("Enter API key", hide_input=True).strip()

        if not api_key:
            typer.echo("❌ API key cannot be empty.")
            raise typer.Exit(1)

    # ── STEP 4: write .env fresh ──────────────────────────────────────────────
    typer.echo("\nSaving configuration...\n")

    env_lines = []
    if llm == "gemini":
        env_lines.append(f"GEMINI_API_KEY={api_key}\n")
    elif llm == "openai":
        env_lines.append(f"OPENAI_API_KEY={api_key}\n")

    env_lines.append(f"ragchatbot_DOCS=./docs\n")
    env_lines.append(f"ragchatbot_DB=./chroma_db\n")
    env_lines.append(f"ragchatbot_LLM={llm}\n")
    env_lines.append(f"ragchatbot_MODEL={model}\n")
    env_lines.append(f"HF_HUB_OFFLINE=0\n")

    with open(".env", "w") as f:
        f.writelines(env_lines)

    typer.echo("  ✅ .env written")

    # ── STEP 5: create folders ────────────────────────────────────────────────
    os.makedirs("./docs", exist_ok=True)
    os.makedirs("./chroma_db", exist_ok=True)
    os.makedirs("./model_cache", exist_ok=True)
    typer.echo("  ✅ folders ready")

    # ── STEP 6: verify embedding model + chromadb ─────────────────────────────
    typer.echo("\nRunning checks...\n")

    try:
        from sentence_transformers import SentenceTransformer
        SentenceTransformer("all-MiniLM-L6-v2", cache_folder="./model_cache")
        typer.echo("  ✅ Embedding model loaded")
    except Exception as e:
        typer.echo(f"  ❌ Embedding model failed — {str(e)}")
        raise typer.Exit(1)

    try:
        import chromadb as cdb
        cdb.PersistentClient(path="./chroma_db")
        typer.echo("  ✅ ChromaDB connected")
    except Exception as e:
        typer.echo(f"  ❌ ChromaDB failed — {str(e)}")
        raise typer.Exit(1)

    if llm == "ollama":
        try:
            import requests as req
            req.get("http://localhost:11434/api/tags", timeout=3).raise_for_status()
            typer.echo("  ✅ Ollama server running")
        except Exception:
            typer.echo("  ❌ Ollama not running. Start with: ollama serve")
            raise typer.Exit(1)

    # ── STEP 7: scan docs ─────────────────────────────────────────────────────
    typer.echo("\nScanning docs/ for supported files...\n")

    supported = (".md", ".txt", ".pdf", ".docx")

    def scan_docs():
        return [f for f in os.listdir("./docs") if f.endswith(supported)]

    files = scan_docs()

    if not files:
        typer.echo("  ⚠️  docs/ is empty. Add your .md, .txt, .pdf, or .docx files.\n")
        typer.echo("  Put your files in the docs/ folder, then press Y to continue.\n")
        confirm = typer.prompt("Ready? (y to continue, n to exit)").strip().lower()
        if confirm != "y":
            typer.echo("Setup cancelled. Run ragchatbot setup again when ready.")
            raise typer.Exit(0)

        # re-scan after user confirms
        files = scan_docs()
        if not files:
            typer.echo("❌ Still no files found in docs/. Exiting.")
            raise typer.Exit(1)

    for f in files:
        typer.echo(f"  📄 {f}")

    typer.echo(f"\n  {len(files)} file(s) found. Indexing...\n")

    # ── STEP 8: index ─────────────────────────────────────────────────────────
    from ragchatbot import RAG
    from ragchatbot.parser import parse_file
    from ragchatbot.chunker import chunk_text
    from ragchatbot.embedder import embed_chunks
    from ragchatbot.store import hash_file, is_file_indexed, add_chunks

    for filename in files:
        filepath = os.path.join("./docs", filename)
        try:
            file_hash = hash_file(filepath)
            if is_file_indexed(filepath, file_hash, "./chroma_db"):
                typer.echo(f"  ✅ {filename} — already indexed")
                continue
            text = parse_file(filepath)
            chunks = chunk_text(text)
            embeddings = embed_chunks(chunks)
            add_chunks(filepath, chunks, embeddings, file_hash, "./chroma_db")
            typer.echo(f"  ✅ {filename} indexed")
        except Exception as e:
            typer.echo(f"  ⚠️  {filename} skipped — {str(e)}")

    # ── DONE ──────────────────────────────────────────────────────────────────
    typer.echo(f"""
── Setup complete ──

  Ask a question:   ragchatbot ask "your question"
  Start API server: ragchatbot start
  Re-run checks:    ragchatbot verify
  All commands:     ragchatbot --help
""")


# ── ASK ───────────────────────────────────────────────────────────────────────
@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask."),
    llm: str = typer.Option(None, help="LLM to use: gemini or ollama."),
    n_results: int = typer.Option(3, help="Number of chunks to retrieve.")
):
    """Ask a question directly from terminal."""

    from ragchatbot import RAG

    llm = llm or os.getenv("ragchatbot_LLM", "gemini")
    docs = os.getenv("ragchatbot_DOCS", "./docs")
    db = os.getenv("ragchatbot_DB", "./chroma_db")

    try:
        rag = RAG(docs=docs, db_path=db, llm=llm, n_results=n_results)
        rag.index()
        result = rag.ask(question)
        typer.echo(f"\nAnswer:\n{result['answer']}")
        typer.echo(f"\nSources: {', '.join(result['sources'])}")

    except FileNotFoundError as e:
        typer.echo(str(e))
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(str(e))
        raise typer.Exit(1)
    except ConnectionError as e:
        typer.echo(str(e))
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Unexpected error: {str(e)}")
        raise typer.Exit(1)
    
# ── START ─────────────────────────────────────────────────────────────────────

@app.command()
def start(
    host: str = typer.Option("0.0.0.0", help="Host to bind server to."),
    port: int = typer.Option(8000, help="Port to run server on."),
    llm: str = typer.Option(None, help="LLM to use: gemini or ollama."),
    reload: bool = typer.Option(False, help="Auto-reload on code changes.")
):
    """Index docs and start the ragchatbot API server."""

    if llm:
        os.environ["ragchatbot_LLM"] = llm

    typer.echo(f"Starting ragchatbot server on http://localhost:{port}")
    typer.echo(f"API docs at http://localhost:{port}/docs\n")

    try:
        import uvicorn
        uvicorn.run(
            "ragchatbot.server:app",
            host=host,
            port=port,
            reload=reload
        )
    except Exception as e:
        typer.echo(f"❌ Server failed to start: {str(e)}")
        raise typer.Exit(1)

# ── INIT ──────────────────────────────────────────────────────────────────────

@app.command()
def init():
    """Scaffold folders and .env for manual configuration [For developers]. For guided setup run: ragchatbot setup"""

    typer.echo("Initializing ragchatbot project...")

    # create folders
    folders = ["docs", "chroma_db", "model_cache"]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        typer.echo(f"  created {folder}/")

    # create .env if not exists
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("GEMINI_API_KEY=your-gemini-api-key\n")
            f.write("ragchatbot_DOCS=./docs\n")
            f.write("ragchatbot_DB=./chroma_db\n")
            f.write("ragchatbot_LLM=gemini\n")
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
    typer.echo("  1. Copy .env.example to .env and fill in your keys")
    typer.echo("  2. Add your docs to docs/")
    typer.echo("  3. Run: ragchatbot verify")
    typer.echo("  4. Run: ragchatbot start")


# ── VERIFY ────────────────────────────────────────────────────────────────────

@app.command()
def verify():
    """Check all config, dependencies, and connections are working."""

    typer.echo("Verifying ragchatbot setup...\n")
    all_ok = True

    # check docs folder
    docs = os.getenv("ragchatbot_DOCS", "./docs")
    if os.path.exists(docs):
        files = [f for f in os.listdir(docs) if f.endswith((".md", ".txt", ".pdf", ".docx"))]
        if files:
            typer.echo(f"  ✅ docs folder — {len(files)} file(s) found")
        else:
            typer.echo(f"  ⚠️  docs folder exists but no .md or .txt files found")
            all_ok = False
    else:
        typer.echo(f"  ❌ docs folder not found: {docs}")
        all_ok = False

    # check gemini api key
    llm = os.getenv("ragchatbot_LLM", "gemini")
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
        db_path = os.getenv("ragchatbot_DB", "./chroma_db")
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
        typer.echo("All checks passed. Run: ragchatbot start")
    else:
        typer.echo("Fix the issues above then run verify again.")




# ── ENTRY POINT ───────────────────────────────────────────────────────────────

def main():
    app()


if __name__ == "__main__":
    main()