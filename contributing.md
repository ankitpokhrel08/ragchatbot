# Contributing to ragchatbot

ragchatbot is a drop-in RAG SDK for website chatbots. Contributions welcome, bug fixes, new LLM adapters, new file parsers, tests, and docs.

---

## Architecture

ragchatbot is built in clean layers, each file has one job:

```text
ragchatbot/
├── parser.py       reads .md/.txt/.pdf/.docx, returns clean plain text
├── chunker.py      splits text into 150-word overlapping chunks (30-word overlap)
├── embedder.py     generates 384-dim vectors via all-MiniLM-L6-v2
├── store.py        all ChromaDB ops — add, query, delete, hash-based skip
├── server.py       FastAPI — POST /ask (auth), POST /chat (open), GET /health, GET /stats
├── cli.py          Typer CLI — setup, init, verify, start, ask, stats, llm
├── __init__.py     RAG class — public interface, wires all layers
└── llm/
    ├── base.py     abstract interface — generate() and generate_stream() required
    ├── gemini.py   Gemini adapter via google-genai
    ├── openai.py   OpenAI adapter via openai SDK (optional dep)
    └── ollama.py   Ollama adapter via local HTTP (localhost:11434)
```

### Request lifecycle

```text
ragchatbot ask "question"
        |
        v
cli.py -> RAG.ask() or RAG.ask_stream()
        |
        v
embedder.embed_query()     # question -> 384-dim vector
        |
        v
store.query_chunks()       # cosine search ChromaDB -> top 3 chunks
        |
        v
llm.generate()             # chunks + question -> prompt -> LLM -> answer
or
llm.generate_stream()      # same but yields tokens one by one
        |
        v
{ answer, sources }  or  (sources, token_generator)
```

### Indexing lifecycle

```text
ragchatbot start  (or ragchatbot setup)
        |
        v
RAG.index()
        |
        v
get_indexed_files()          # what's currently in ChromaDB
current_files in docs/       # what's on disk
        |
        v
stale = indexed - current    # files deleted from docs/
delete_file_chunks(stale)    # remove from ChromaDB
        |
        v
for each file in docs/:
    parser.parse_file()      # clean text (.md/.txt/.pdf/.docx)
    chunker.chunk_text()     # split into chunks
    embedder.embed_chunks()  # generate vectors
    store.hash_file()        # MD5 fingerprint
    store.is_file_indexed()  # skip if unchanged
    store.add_chunks()       # store in ChromaDB
```

---

## Dev Setup

```bash
git clone https://github.com/yourusername/ragchatbot
cd ragchatbot
python3 -m venv myenv
source myenv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

# fill in your API key in .env
ragchatbot verify

# run tests
pytest tests/ -v
```

---

## Adding a New LLM Adapter

Most common contribution. Every LLM must implement both `generate` and `generate_stream`.

### 1. Create `ragchatbot/llm/yourllm.py`

```python
import os
from typing import Generator
from ragchatbot.llm.base import BaseLLM


class YourLLM(BaseLLM):

    def __init__(self, api_key: str = None, model: str = None):
        self.model = model or os.getenv("ragchatbot_MODEL", "default-model-name")
        key = api_key or os.getenv("YOUR_API_KEY")

        if not key:
            raise ValueError(
                "❌ API key not found.\n"
                "   Set YOUR_API_KEY in .env or pass api_key= directly."
            )

        self.client = ...   # init your SDK client
        print(f"YourLLM ready — model: {self.model}")

    def generate(self, question: str, context_chunks: list[dict]) -> dict:
        if not context_chunks:
            return {
                "answer": "I don't have that information in my docs.",
                "sources": []
            }

        prompt = self._build_prompt(question, context_chunks)
        sources = self._extract_sources(context_chunks)

        try:
            response = self.client.complete(prompt)
            answer = response.text.strip()
        except Exception as e:
            answer = f"❌ Error: {str(e)}"

        return {"answer": answer, "sources": sources}

    def generate_stream(self, question: str, context_chunks: list[dict]) -> Generator:
        if not context_chunks:
            yield "I don't have that information in my docs."
            return

        prompt = self._build_prompt(question, context_chunks)

        try:
            for chunk in self.client.stream(prompt):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"❌ Streaming error: {str(e)}"
```

### 2. Register in `ragchatbot/__init__.py`

```python
def _load_llm(self, llm: str, **kwargs):
    ...
    elif llm == "yourllm":
        from ragchatbot.llm.yourllm import YourLLM
        return YourLLM(**kwargs)
```

### 3.1 Add to setup options in `cli.py`

Add to the LLM and model menus in the `setup()` command.

### 3.2 Add to CLI menus in `cli.py`

Add to the LLM and model menus in both `setup()` and `llm()` commands.

### 4. Add dependency to `pyproject.toml`

```toml
[project.optional-dependencies]
yourllm = [
    "your-llm-sdk",
]
```

### 5. Test

```python
from ragchatbot import RAG

rag = RAG(docs="./docs", llm="yourllm")
rag.index()
print(rag.ask("test question"))

# test streaming
sources, stream = rag.ask_stream("test question")
for token in stream:
    print(token, end="", flush=True)
```

---

## Adding a New File Parser

### 1. Add handler in `ragchatbot/parser.py`

```python
def parse_file(filepath: str) -> str:
    if filepath.endswith(".txt"):   ...
    if filepath.endswith(".md"):    ...
    if filepath.endswith(".pdf"):   ...
    if filepath.endswith(".docx"):  ...
    if filepath.endswith(".html"):
        return _parse_html(filepath)

    raise ValueError(f"Unsupported file type: {filepath}")

def _parse_html(filepath: str) -> str:
    # extract and return clean text
    ...
```

### 2. Update file filters in `ragchatbot/__init__.py` and `ragchatbot/cli.py`

```python
# __init__.py — index()
current_files = {
    f for f in os.listdir(self.docs)
    if f.endswith((".md", ".txt", ".pdf", ".docx", ".html"))
}

# cli.py — verify() and setup()
supported = (".md", ".txt", ".pdf", ".docx", ".html")
```

### 3. Add dependency to `pyproject.toml`

### 4. Add a test in `tests/test_parser.py`

---

## Running Tests

```bash
pytest tests/ -v
```

19 tests cover chunker, embedder, parser, store, and RAG end-to-end. All must pass before submitting a PR.

---

## Guidelines

### We welcome

- Bug fixes
- New LLM adapters (Anthropic, Cohere, Mistral)
- New file parsers (HTML, CSV)
- Test coverage improvements
- Documentation improvements

### Backlog — not yet

- Streaming responses ✅ done
- Auth on `/ask` ✅ done
- `ragchatbot llm` command ✅ done
- Remote vector DBs (Qdrant, Pinecone)
- Web UI
- Auto file-watcher
- `reindex` command for specific files

### Code rules

- One job per file — don't mix concerns
- Type hints on all functions
- Docstrings on public methods
- Both `generate()` and `generate_stream()` must be implemented in every LLM adapter
- Don't change `BaseLLM` interface — it's the contract
- No new core dependencies without discussion
- Error messages must be human-readable — no raw tracebacks to the user
- All new features need tests

### Commit format

```text
feat: add Anthropic adapter
fix: handle corrupted PDF during indexing
docs: update contributing guide
refactor: simplify chunker logic
test: add parser tests for docx
```

---

## Submitting a PR

```bash
git checkout -b feat/anthropic-adapter

# make changes
pytest tests/ -v   # all must pass

git commit -m "feat: add Anthropic adapter"
git push origin feat/anthropic-adapter
```

PR must include:

- What it does
- How to test it
- New dependencies (if any)
- Tests added or updated

---

## Questions

Open a GitHub issue with the `question` label.
