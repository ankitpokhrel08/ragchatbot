# quickrag

Drop-in RAG SDK for website chatbots. Add a semantic search chatbot to any website in minutes — no ML experience required.

```bash
pip install quickrag
quickrag init
quickrag verify
quickrag start
```

Your chatbot API is live at `http://localhost:8000`.

---

## How It Works

```
docs/ (your markdown files)
    |
    ↓
quickrag index — parse → chunk → embed → store in ChromaDB
    |
    ↓
POST /ask {"question": "..."}
    |
    ↓
embed query → cosine search → top chunks → Gemini/Ollama → answer + sources
```

quickrag reads your docs, understands their meaning using semantic embeddings, and answers questions grounded in your actual content — not hallucinated responses.

---

## Installation

```bash
pip install quickrag
```

Requires Python 3.10 or higher.

---

## Quick Start

### 1. Initialize project

```bash
mkdir my-chatbot
cd my-chatbot
quickrag init
```

This creates:

```
my-chatbot/
├── docs/          ← put your markdown/txt files here
├── chroma_db/     ← auto-managed vector database
├── model_cache/   ← embedding model cache
├── .env           ← your config
└── .gitignore
```

### 2. Add your docs

Drop any `.md` or `.txt` files into `docs/`:

```
docs/
├── faq.md
├── refund-policy.md
├── shipping-policy.md
└── terms-of-service.txt
```

### 3. Configure

Edit `.env`:

```env
GEMINI_API_KEY=your-gemini-api-key
quickrag_DOCS=./docs
quickrag_DB=./chroma_db
quickrag_LLM=gemini
```

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com).

### 4. Verify setup

```bash
quickrag verify
```

```
Verifying quickrag setup...

  ✅ docs folder — 3 file(s) found
  ✅ GEMINI_API_KEY — set
  ✅ ChromaDB — connected
  ✅ Embedding model — loaded

All checks passed. Run: quickrag start
```

### 5. Start

```bash
quickrag start
```

API live at `http://localhost:8000`.
Interactive docs at `http://localhost:8000/docs`.

---

## CLI Reference

```bash
quickrag init                         # scaffold project in current directory
quickrag verify                       # check config, connections, docs
quickrag start                        # index docs + start API server
quickrag start --port 9000            # custom port
quickrag start --llm ollama           # use Ollama instead of Gemini
quickrag ask "your question"          # test query from terminal
quickrag ask "question" --llm ollama  # test with specific LLM
```

---

## API Reference

### `POST /ask`

Ask a question against your indexed docs.

**Request:**

```json
{
  "question": "How long does a refund take?",
  "llm": "gemini",
  "n_results": 3
}
```

**Response:**

```json
{
  "answer": "Refunds are processed within 5 business days of receiving the returned item.",
  "sources": ["refund-policy.md"],
  "question": "How long does a refund take?"
}
```

### `GET /health`

```json
{ "status": "ok", "version": "0.1.0" }
```

### `GET /stats`

Returns indexing stats — total chunks, files indexed.

---

## Frontend Integration

```javascript
const response = await fetch("http://localhost:8000/ask", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ question: "What is your refund policy?" }),
});

const data = await response.json();
console.log(data.answer); // answer from your docs
console.log(data.sources); // ["refund-policy.md"]
```

Works with React, Vue, vanilla JS, Next.js — any frontend.

---

## LLM Support

### Gemini (default)

Free tier available. Get API key at [aistudio.google.com](https://aistudio.google.com).

```env
quickrag_LLM=gemini
GEMINI_API_KEY=your-key
```

### Ollama (fully local)

No API key. No internet. Runs on your machine.

```bash
# install ollama
brew install ollama

# start server
ollama serve

# pull a model
ollama pull llama3.2
```

```env
quickrag_LLM=ollama
```

Switch LLM per request via API:

```json
{ "question": "...", "llm": "ollama" }
```

---

## Python API

For advanced use or embedding quickrag into existing Python projects:

```python
from quickrag import RAG

rag = RAG(
    docs="./docs",
    db_path="./chroma_db",
    llm="gemini",          # "gemini" or "ollama"
    n_results=3
)

rag.index()                # index all docs (skips unchanged)

result = rag.ask("What is your return policy?")
print(result["answer"])
print(result["sources"])
```

---

## Configuration

All config lives in `.env`:

| Variable         | Default       | Description                               |
| ---------------- | ------------- | ----------------------------------------- |
| `GEMINI_API_KEY` | —             | Gemini API key (required if using Gemini) |
| `quickrag_DOCS`  | `./docs`      | Path to docs folder                       |
| `quickrag_DB`    | `./chroma_db` | Path to ChromaDB storage                  |
| `quickrag_LLM`   | `gemini`      | Default LLM: `gemini` or `ollama`         |
| `HF_HUB_OFFLINE` | `1`           | Load embedding model from cache only      |

---

## Supported File Types

| Type                | Support                           |
| ------------------- | --------------------------------- |
| Markdown (`.md`)    | ✅ Full — strips formatting noise |
| Plain text (`.txt`) | ✅ Full                           |
| PDF (`.pdf`)        | 🔜 v0.2                           |
| DOCX (`.docx`)      | 🔜 v0.2                           |

---

## How Indexing Works

- Files are parsed and split into overlapping chunks (~150 words, 30 word overlap)
- Each chunk is embedded using `all-MiniLM-L6-v2` (local, free, ~80MB)
- Embeddings stored in ChromaDB with file metadata
- File hashes tracked — unchanged files are skipped on re-index
- Modified files are automatically re-indexed

---

## Roadmap

- [ ] PDF and DOCX support
- [ ] Streaming responses
- [ ] Remote vector DB support (Qdrant, Pinecone)
- [ ] OpenAI LLM adapter
- [ ] Auth on `/ask` endpoint
- [ ] Auto file-watcher re-indexing
- [ ] Web UI for testing

---

## License

MIT
