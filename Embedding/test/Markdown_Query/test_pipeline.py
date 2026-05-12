import numpy as np
from parser import parse_file
from chunker import chunk_text
from embedder import embed_chunks, embed_query

# ── 1. PARSE ──────────────────────────────────────────────────────────────────
print("── Step 1: Parse ──")
text = parse_file("/Users/ankitpokhrel/Desktop/ragbase/Embedding/test/Markdown_Query/docs/about_rag.md")
print(text[:300])  # preview first 300 chars
print(f"\nTotal characters: {len(text)}")

# ── 2. CHUNK ──────────────────────────────────────────────────────────────────
print("\n── Step 2: Chunk ──")
chunks = chunk_text(text, chunk_size=150, overlap=30)
print(f"Total chunks: {len(chunks)}")
for i, chunk in enumerate(chunks):
    word_count = len(chunk.split())
    print(f"\nChunk {i+1} ({word_count} words):")
    print(chunk)
    print("-" * 60)

# ── 3. EMBED ──────────────────────────────────────────────────────────────────
print("\n── Step 3: Embed ──")
embeddings = embed_chunks(chunks)
print(f"Embeddings shape: {embeddings.shape}")  # (n_chunks, 384)

# ── 4. QUERY ──────────────────────────────────────────────────────────────────
print("\n── Step 4: Query ──")
query = "what does knowledge base may contain?"
query_vector = embed_query(query)
print(f"Query: '{query}'")
print(f"Query vector shape: {query_vector.shape}")  # (384,)

# ── 5. COSINE SEARCH (manual numpy) ───────────────────────────────────────────
print("\n── Step 5: Find Most Relevant Chunk ──")

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

scores = [cosine_similarity(query_vector, emb) for emb in embeddings]

# Rank chunks by score
ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

print(f"\nTop 3 chunks for: '{query}'\n")
for rank, (chunk_idx, score) in enumerate(ranked[:3], 1):
    print(f"Rank {rank} — Score: {score:.4f}")
    print(f"Chunk {chunk_idx + 1}: {chunks[chunk_idx][:200]}...")
    print()