# ragchatbot

[![PyPI version](https://badge.fury.io/py/ragchatbot.svg)](https://badge.fury.io/py/ragchatbot)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Add a semantic search chatbot to any website in minutes. Drop in your docs, get a working API — no ML experience required.

```bash
pip install ragchatbot
ragchatbot init
ragchatbot verify
ragchatbot start
```

Your chatbot API is live at `http://localhost:8000`.

---

## What It Does

ragchatbot reads your markdown and text files, understands their meaning, and answers questions grounded in your actual content — not hallucinated responses.

Ask:

> "what is your refund policy?"

and it finds the answer from your docs.

---

## Requirements

- Python 3.10 or higher
- A Gemini API key (free) — get one at [aistudio.google.com](https://aistudio.google.com)
- Or Ollama installed locally (no API key needed)

---

## Quick Start

### Step 1 — Install

```bash
pip install ragchatbot
```

### Step 2 — Create a project

```bash
mkdir my-chatbot
cd my-chatbot
ragchatbot init
```

This creates:

```text
my-chatbot/
├── docs/          ← put your files here
├── chroma_db/     ← auto-managed (don't touch)
├── model_cache/   ← auto-managed (don't touch)
├── .env           ← your settings
└── .gitignore
```

### Step 3 — Add your docs

Drop any `.md` or `.txt` files into `docs/`.

Examples:

```text
docs/
├── faq.md
├── refund-policy.md
├── shipping-policy.md
└── terms.txt
```

### Step 4 — Configure

Open `.env` and fill in:

```env
GEMINI_API_KEY=your-gemini-api-key
RAGCHATBOT_DOCS=./docs
RAGCHATBOT_DB=./chroma_db
RAGCHATBOT_LLM=gemini
HF_HUB_OFFLINE=0
```

Set `HF_HUB_OFFLINE=0` on first run so the embedding model can download (~80MB, one time only).

Set it back to `1` after.

### Step 5 — Verify everything works

```bash
ragchatbot verify
```

You should see:

```text
Verifying ragchatbot setup...
✅ docs folder — 3 file(s) found
✅ GEMINI_API_KEY — set
✅ ChromaDB — connected
✅ Embedding model — loaded
All checks passed. Run: ragchatbot start
```

### Step 6 — Test a query

```bash
ragchatbot ask "what is your refund policy?"
```

### Step 7 — Start the server

```bash
ragchatbot start
```

API live at `http://localhost:8000`

Interactive API docs at `http://localhost:8000/docs`

---

## Using the API

Once the server is running, your frontend can call it:

```javascript
const response = await fetch("http://localhost:8000/ask", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    question: "What is your refund policy?",
  }),
});

const data = await response.json();

console.log(data.answer); // answer from your docs
console.log(data.sources); // ["refund-policy.md"]
```

Works with React, Vue, vanilla JS, Next.js — any frontend.

---

## CLI Commands

```bash
ragchatbot init                         # set up a new project
ragchatbot verify                       # check everything is working
ragchatbot start                        # index docs + start API
ragchatbot start --port 9000            # use a different port
ragchatbot start --llm ollama           # use Ollama instead of Gemini
ragchatbot ask "your question"          # test a query in terminal
ragchatbot ask "question" --llm ollama  # test with Ollama
```

---

## Using Ollama Instead of Gemini (Optional)

Ollama runs fully locally — no API key, no internet, no cost.

```bash
brew install ollama
ollama serve
ollama pull llama3.2
```

Update `.env`:

```env
RAGCHATBOT_LLM=ollama
```

Or switch per request:

```json
{
  "question": "...",
  "llm": "ollama"
}
```

---

## Supported File Types

| Type              | Status            |
| ----------------- | ----------------- |
| Markdown `.md`    | ✅ Supported      |
| Plain text `.txt` | ✅ Supported      |
| PDF `.pdf`        | 🔜 Coming in v0.2 |
| Word `.docx`      | 🔜 Coming in v0.2 |

---

## Settings Reference

All settings live in `.env`:

| Setting           | Default       | Description                            |
| ----------------- | ------------- | -------------------------------------- |
| `GEMINI_API_KEY`  | —             | Your Gemini API key                    |
| `RAGCHATBOT_DOCS` | `./docs`      | Folder containing your docs            |
| `RAGCHATBOT_DB`   | `./chroma_db` | Where vectors are stored               |
| `RAGCHATBOT_LLM`  | `gemini`      | Which LLM to use: `gemini` or `ollama` |
| `HF_HUB_OFFLINE`  | `1`           | Set to `0` only on first run           |

---

## Links

- PyPI: https://pypi.org/project/ragchatbot
- Issues: https://github.com/yourusername/ragchatbot/issues
- Contributing: `CONTRIBUTING.md`

---

## License

MIT
