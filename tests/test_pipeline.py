import os
from ragbase.parser import parse_file
from ragbase.chunker import chunk_text
from ragbase.embedder import embed_chunks, embed_query
from ragbase.store import (
    hash_file,
    is_file_indexed,
    add_chunks,
    query_chunks,
    collection_stats
)

DB_PATH = "./chroma_db"
DOCS_PATH = "./docs"

# ── INDEX ─────────────────────────────────────────────────────────────────────
print("── Indexing docs/ ──")

for filename in os.listdir(DOCS_PATH):
    if not filename.endswith((".md", ".txt")):
        continue

    filepath = os.path.join(DOCS_PATH, filename)
    file_hash = hash_file(filepath)

    if is_file_indexed(filepath, file_hash, DB_PATH):
        print(f"Skipping {filename} — unchanged")
        continue

    print(f"Indexing {filename}...")
    text = parse_file(filepath)
    chunks = chunk_text(text)
    embeddings = embed_chunks(chunks)
    add_chunks(filepath, chunks, embeddings, file_hash, DB_PATH)

# ── STATS ─────────────────────────────────────────────────────────────────────
collection_stats(DB_PATH)

# ── QUERY ─────────────────────────────────────────────────────────────────────
print("\n── Query ──")
query = "What is RAG and how does it work?"  # Example query 
print(f"Query: '{query}'\n")

query_vector = embed_query(query)
results = query_chunks(query_vector, n_results=3, db_path=DB_PATH)

for i, result in enumerate(results, 1):
    print(f"Rank {i} — Score: {result['score']} — Source: {result['source']}")
    print(f"{result['text'][:200]}...")
    print()