# ragchatbot

[![PyPI version](https://badge.fury.io/py/ragchatbot.svg)](https://badge.fury.io/py/ragchatbot)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Add a semantic search chatbot to any website in minutes. Drop in your docs, get a working API — no ML experience required.

```bash
pip install ragchatbot
ragchatbot setup
```

Your chatbot API is live at `http://localhost:8000`.

---

## What It Does

ragchatbot reads your documents, understands their meaning, and answers questions grounded in your actual content — not hallucinated responses.

Ask:

> "what is your refund policy?"

and it finds the answer from your docs.

---

## Requirements

- Python 3.10 or higher
- One of:
  - A Gemini API key (free) — get one at [aistudio.google.com](https://aistudio.google.com)
  - An OpenAI API key — get one at [platform.openai.com](https://platform.openai.com/api-keys)
  - Ollama installed locally (no API key, no cost)

---

## Quick Start

### Step 1 — Install

```bash
pip install ragchatbot
```

### Step 2 — Run guided setup

```bash
mkdir my-chatbot
cd my-chatbot
ragchatbot setup
```

Setup will:

- Ask which LLM you want to use (Gemini, OpenAI, or Ollama)
- Ask which model
- Ask for your API key
- Create all folders
- Scan and index your docs automatically

### Step 3 — Add your docs

Put your `.md`, `.txt`, `.pdf`, or `.docx` files in the `docs/` folder:

```text
docs/
├── faq.md
├── refund-policy.pdf
├── shipping-policy.docx
└── terms.txt
```

Then press `y` when setup prompts you — it will index everything.

### Step 4 — Ask a question

```bash
ragchatbot ask "what is your refund policy?"
```

### Step 5 — Start the API server

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
console.log(data.sources); // ["refund-policy.pdf"]
```

Works with React, Vue, vanilla JS, Next.js — any frontend.

---

## CLI Commands

```bash
ragchatbot setup                        # guided setup — LLM, API key, index docs
ragchatbot ask "your question"          # ask a question from terminal
ragchatbot ask "question" --llm ollama  # ask using a specific LLM
ragchatbot start                        # index docs + start API server
ragchatbot start --port 9000            # use a different port
ragchatbot start --llm ollama           # start with a specific LLM
ragchatbot verify                       # re-check everything is working
ragchatbot init                         # scaffold folders + .env manually (advanced)
ragchatbot --help                       # show all commands
```

---

## Using Ollama (Local, No API Key)

Ollama runs fully locally — no API key, no internet, no cost.

```bash
brew install ollama
ollama serve
ollama pull llama3.2
```

Then run setup and choose Ollama, or switch in `.env`:

```env
ragchatbot_LLM=ollama
ragchatbot_MODEL=llama3.2
```

---

## Using OpenAI

```bash
pip install ragchatbot[openai]
```

Run setup and choose OpenAI, or set in `.env`:

```env
OPENAI_API_KEY=your-openai-api-key
ragchatbot_LLM=openai
ragchatbot_MODEL=gpt-4o-mini
```

---

## Supported File Types

| Type              | Status       |
| ----------------- | ------------ |
| Markdown `.md`    | ✅ Supported |
| Plain text `.txt` | ✅ Supported |
| PDF `.pdf`        | ✅ Supported |
| Word `.docx`      | ✅ Supported |

---

## Settings Reference

All settings live in `.env` (created automatically by `ragchatbot setup`):

| Setting            | Default         | Description                                 |
| ------------------ | --------------- | ------------------------------------------- |
| `GEMINI_API_KEY`   | —               | Your Gemini API key                         |
| `OPENAI_API_KEY`   | —               | Your OpenAI API key                         |
| `ragchatbot_DOCS`  | `./docs`        | Folder containing your docs                 |
| `ragchatbot_DB`    | `./chroma_db`   | Where vectors are stored                    |
| `ragchatbot_LLM`   | `gemini`        | Which LLM: `gemini`, `openai`, or `ollama`  |
| `ragchatbot_MODEL` | per LLM default | Model name — set automatically during setup |
| `HF_HUB_OFFLINE`   | `1`             | Set to `0` only on first run                |

---

## Links

- PyPI: https://pypi.org/project/ragchatbot
- Issues: https://github.com/yourusername/ragchatbot/issues
- Contributing: `CONTRIBUTING.md`

---

## License

MIT
