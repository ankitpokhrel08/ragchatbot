# Contributing to ragchatbot

ragchatbot is a drop-in RAG SDK for website chatbots. Contributions welcome — bug fixes, new LLM adapters, new file parsers, tests, and docs.

---

## Architecture

ragchatbot is built in clean layers — each file has one job:

```text
ragchatbot/
├── parser.py       reads .md/.txt, strips formatting noise, returns clean text
├── chunker.py      splits text into 150-word overlapping chunks (30-word overlap)
├── embedder.py     generates 384-dim vectors via all-MiniLM-L6-v2
├── store.py        all ChromaDB ops — add, query, delete, hash-based skip
├── server.py       FastAPI — POST /ask, GET /health, GET /stats, CORS
├── cli.py          Typer CLI — init, verify, start, ask
├── __init__.py     RAG class — public interface, wires all layers
└── llm/
    ├── base.py     abstract interface all LLM adapters must implement
    ├── gemini.py   Gemini adapter via google-genai
    └── ollama.py   Ollama adapter via local HTTP (localhost:11434)
```

### Request lifecycle

```text
ragchatbot ask "question"
        |
        v
cli.py -> RAG.ask()
        |
        v
embedder.embed_query()     # question -> 384-dim vector
        |
        v
store.query_chunks()       # cosine search ChromaDB -> top 3 chunks
        |
        v
llm.generate()             # chunks + question -> prompt -> LLM -> answer
        |
        v
{ answer, sources }
```

### Indexing lifecycle

```text
ragchatbot start
        |
        v
server.py lifespan -> RAG.index()
        |
        v
for each file in docs/:
    parser.parse_file()      # clean text
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

# add GEMINI_API_KEY to .env
ragchatbot verify
```

---

## Adding a New LLM Adapter

Most common contribution. Every LLM follows the same interface.

### 1. Create `ragchatbot/llm/yourllm.py`

```python
from ragchatbot.llm.base import BaseLLM

class YourLLM(BaseLLM):

    def __init__(self, api_key: str = None, model: str = "model-name"):
        self.client = ...   # init your client
        self.model = model

    def generate(self, question: str, context_chunks: list[dict]) -> dict:
        if not context_chunks:
            return {
                "answer": "I don't have that information in my docs.",
                "sources": []
            }

        prompt = self._build_prompt(question, context_chunks)
        sources = self._extract_sources(context_chunks)

        response = self.client.complete(prompt)

        return {
            "answer": response.text.strip(),
            "sources": sources
        }
```

### 2. Register in `ragchatbot/__init__.py`

```python
def _load_llm(self, llm: str, **kwargs):
    if llm == "gemini":
        from ragchatbot.llm.gemini import GeminiLLM
        return GeminiLLM(**kwargs)

    elif llm == "ollama":
        from ragchatbot.llm.ollama import OllamaLLM
        return OllamaLLM(**kwargs)

    elif llm == "yourllm":
        from ragchatbot.llm.yourllm import YourLLM
        return YourLLM(**kwargs)
```

### 3. Add dependency to `pyproject.toml`

```toml
dependencies = [
    ...
    "your-llm-sdk",
]
```

### 4. Test

```python
from ragchatbot import RAG

rag = RAG(docs="./docs", llm="yourllm")
rag.index()

print(rag.ask("test question"))
```

---

## Adding a New File Parser

### 1. Add handler in `ragchatbot/parser.py`

```python
def parse_file(filepath: str) -> str:
    if filepath.endswith(".txt"):
        ...

    if filepath.endswith(".md"):
        ...

    if filepath.endswith(".pdf"):
        return parse_pdf(filepath)

def parse_pdf(filepath: str) -> str:
    # extract and return clean text
    ...
```

### 2. Update file filter in `ragchatbot/__init__.py`

```python
# change this
if not filename.endswith((".md", ".txt")):

# to this
if not filename.endswith((".md", ".txt", ".pdf")):
```

### 3. Add dependency to `pyproject.toml`

---

## Guidelines

### We welcome:

- Bug fixes
- New LLM adapters (OpenAI, Anthropic, Cohere)
- New file parsers (PDF, DOCX, HTML)
- Test coverage
- Documentation improvements

### Save for v0.2+

- Streaming responses
- Remote vector DBs
- Web UI
- Auth on `/ask`
- Auto file-watcher

### Code rules

- One job per file — don't mix concerns
- Type hints on all functions
- Docstrings on public methods
- Don't change `BaseLLM` interface — it's the contract
- No new dependencies without discussion

### Commit format

```text
feat: add OpenAI adapter
fix: handle empty docs folder
docs: update contributing guide
refactor: simplify chunker logic
```

---

## Submitting a PR

```bash
git checkout -b feat/openai-adapter

# make changes + write tests
pytest tests/

git commit -m "feat: add OpenAI adapter"
git push origin feat/openai-adapter
```

PR must include:

- What it does
- How to test it
- New dependencies (if any)

---

## Questions

Open a GitHub issue with the `question` label.
