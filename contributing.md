# Contributing to quickrag

quickrag is a drop-in RAG SDK that lets developers add semantic search chatbots to their websites with minimal setup. Contributions are welcome — bug fixes, new features, documentation improvements, and new LLM adapters.

---

## How quickrag Works — Architecture Overview

Understanding the architecture before contributing is important. quickrag is built in clean layers — each with one job.

```
quickrag/
├── parser.py       reads .md and .txt files, strips formatting, returns clean text
├── chunker.py      splits text into overlapping word chunks (150 words, 30 overlap)
├── embedder.py     generates 384-dim vectors using all-MiniLM-L6-v2 (sentence-transformers)
├── store.py        all ChromaDB operations — add, query, delete, hash detection
├── server.py       FastAPI server — POST /ask, GET /health, GET /stats
├── cli.py          Typer CLI — init, verify, start, ask commands
├── __init__.py     RAG class — public interface, wires all layers together
└── llm/
    ├── base.py     abstract LLM interface — all adapters must implement this
    ├── gemini.py   Gemini adapter (google-genai)
    └── ollama.py   Ollama adapter (local HTTP to localhost:11434)
```

### Request lifecycle

```
quickrag ask "question"
      |
cli.py -> RAG.ask()
      |
embedder.embed_query()        # embed question -> 384-dim vector
      |
store.query_chunks()          # cosine search ChromaDB -> top 3 chunks
      |
llm.generate()                # chunks + question -> prompt -> LLM -> answer
      |
{ answer, sources }           # returned to user
```

### Indexing lifecycle

```
quickrag start
      |
server.py lifespan -> RAG.index()
      |
for each file in docs/:
    parser.parse_file()       # clean text
    chunker.chunk_text()      # split into chunks
    embedder.embed_chunks()   # generate vectors
    store.hash_file()         # MD5 hash of file
    store.is_file_indexed()   # skip if hash unchanged
    store.add_chunks()        # store in ChromaDB
```

---

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- Ollama (optional, for local LLM testing)

### Clone and install

```bash
git clone https://github.com/yourusername/quickrag
cd quickrag
python -m venv myenv
source myenv/bin/activate      # mac/linux
pip install -e ".[dev]"
```

### Configure

```bash
cp .env.example .env
# edit .env — add your GEMINI_API_KEY
```

### Verify setup

```bash
quickrag verify
```

### Run tests

```bash
pytest tests/
```

---

## Project Structure

```
quickrag/                     # project root
├── quickrag/                 # Python package
│   ├── __init__.py          # RAG class — public interface
│   ├── parser.py
│   ├── chunker.py
│   ├── embedder.py
│   ├── store.py
│   ├── server.py
│   ├── cli.py
│   └── llm/
│       ├── __init__.py
│       ├── base.py
│       ├── gemini.py
│       └── ollama.py
├── tests/
│   └── test_pipeline.py
├── docs/                    # sample docs for testing
├── .env                     # your local config (gitignored)
├── .env.example             # template for contributors
├── .gitignore
└── pyproject.toml
```

---

## Adding a New LLM Adapter

This is the most common contribution. quickrag uses an adapter pattern — every LLM implements the same interface.

### Step 1 — create `quickrag/llm/your_llm.py`

```python
from quickrag.llm.base import BaseLLM


class YourLLM(BaseLLM):

    def __init__(self, api_key: str = None, model: str = "default-model"):
        # initialize your LLM client here
        self.client = ...
        self.model = model

    def generate(self, question: str, context_chunks: list[dict]) -> dict:
        """
        Required. Must return:
        {
            "answer":  str,
            "sources": list[str]
        }
        """
        if not context_chunks:
            return {
                "answer": "I don't have that information in my docs.",
                "sources": []
            }

        # use base class helpers
        prompt = self._build_prompt(question, context_chunks)
        sources = self._extract_sources(context_chunks)

        # call your LLM
        response = self.client.complete(prompt)

        return {
            "answer": response.text.strip(),
            "sources": sources
        }
```

### Step 2 — register in `quickrag/__init__.py`

```python
def _load_llm(self, llm: str, **kwargs):
    if llm == "gemini":
        from quickrag.llm.gemini import GeminiLLM
        return GeminiLLM(**kwargs)
    elif llm == "ollama":
        from quickrag.llm.ollama import OllamaLLM
        return OllamaLLM(**kwargs)
    elif llm == "your_llm":                    # add this
        from quickrag.llm.your_llm import YourLLM
        return YourLLM(**kwargs)
```

### Step 3 — add dependency to `pyproject.toml`

```toml
dependencies = [
    ...
    "your-llm-package",
]
```

### Step 4 — test it

```python
from quickrag import RAG
rag = RAG(docs="./docs", llm="your_llm")
rag.index()
result = rag.ask("test question")
print(result)
```

---

## Adding a New File Parser

Currently quickrag supports `.md` and `.txt`. To add PDF, DOCX, etc:

### Step 1 — add handler in `quickrag/parser.py`

```python
def parse_file(filepath: str, strip_math: bool = False, strip_code: bool = True) -> str:

    if filepath.endswith(".txt"):
        ...

    if filepath.endswith(".md"):
        ...

    if filepath.endswith(".pdf"):       # add new type here
        return parse_pdf(filepath)

    raise ValueError(f"Unsupported file type: {filepath}")


def parse_pdf(filepath: str) -> str:
    """Extract clean text from PDF."""
    # your implementation
    ...
```

### Step 2 — update `quickrag/__init__.py` index method

```python
# update this line
if not filename.endswith((".md", ".txt")):

# to include new type
if not filename.endswith((".md", ".txt", ".pdf")):
```

### Step 3 — add required dependency to `pyproject.toml`

---

## Contribution Guidelines

### What we welcome

- Bug fixes
- New LLM adapters (OpenAI, Anthropic, Cohere, etc.)
- New file type parsers (PDF, DOCX, HTML)
- Performance improvements
- Documentation improvements
- Test coverage

### What belongs in v0.2+ (don't submit for v0.1)

- Streaming responses
- Remote vector DB support
- Web UI
- Auth on `/ask` endpoint
- Auto file-watcher

### Code style

- Follow existing patterns — one job per file
- Type hints on all functions
- Docstrings on public methods
- No external dependencies without discussion first
- Keep `BaseLLM` interface unchanged — it's the contract all adapters rely on

### Commit messages

```
feat: add OpenAI LLM adapter
fix: handle empty docs folder in verify command
docs: add PDF parser contribution guide
refactor: simplify chunker overlap logic
```

---

## Submitting a PR

```bash
# fork and clone
git clone https://github.com/yourusername/quickrag
cd quickrag

# create branch
git checkout -b feat/openai-adapter

# make changes
# write tests
# run tests
pytest tests/

# commit
git add .
git commit -m "feat: add OpenAI LLM adapter"

# push and open PR
git push origin feat/openai-adapter
```

PR description should include:

- What it does
- How to test it
- Any new dependencies added
- Which LLM/file type if adding an adapter/parser

---

## Questions

Open a GitHub issue with the `question` label. We'll respond within 48 hours.
