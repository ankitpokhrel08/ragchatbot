# tests/test_server.py
from ragchatbot import RAG
rag = RAG(docs="./docs", llm="gemini")
rag.serve(port=8000)