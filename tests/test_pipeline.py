from quickrag import RAG
import os

# ── TEST GEMINI ───────────────────────────────────────────────────────────────
print("── Testing Gemini ──")
rag_gemini = RAG(docs="./docs", llm="gemini")
rag_gemini.index()
result = rag_gemini.ask("what is RAG?")
print(f"Answer: {result['answer']}")
print(f"Sources: {result['sources']}")

# ── TEST OLLAMA ───────────────────────────────────────────────────────────────
print("\n── Testing Ollama ──")
rag_ollama = RAG(docs="./docs", llm="ollama", model="llama3.2")
rag_ollama.index()
result = rag_ollama.ask("what is RAG?")
print(f"Answer: {result['answer']}")
print(f"Sources: {result['sources']}")