import os
import hashlib
import chromadb
from chromadb.config import Settings

#CLIENT SETUP 

_client = None
_collection = None

def get_collection(db_path: str = "./chroma_db") -> chromadb.Collection:
    """
    Returns the ChromaDB collection.
    Creates it if it doesn't exist.
    Called once — reused across all store operations.
    """
    global _client, _collection

    if _collection is not None:
        return _collection

    _client = chromadb.PersistentClient(path=db_path)

    _collection = _client.get_or_create_collection(
        name="ragchatbot",
        metadata={"hnsw:space": "cosine"}  # use cosine similarity for all queries
    )

    return _collection


#HASHING

def hash_file(filepath: str) -> str:
    """
    Generate MD5 hash of a file's content.
    Used to detect if file has changed since last index.
    """
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def is_file_indexed(filepath: str, current_hash: str, db_path: str = "./chroma_db") -> bool:
    """
    Check if file is already indexed with the same hash.
    Returns True  -> file unchanged, skip re-indexing
    Returns False -> file new or changed, needs indexing
    """
    collection = get_collection(db_path)

    # Query metadata for any chunk from this file
    results = collection.get(
        where={"source": os.path.basename(filepath)},
        limit=1
    )

    if not results["ids"]:
        # No chunks found for this file -> never indexed
        return False

    # Check stored hash against current hash
    stored_hash = results["metadatas"][0].get("file_hash", "")
    return stored_hash == current_hash


# ── ADD ───────────────────────────────────────────────────────────────────────

def add_chunks(
    filepath: str,
    chunks: list[str],
    embeddings,
    file_hash: str,
    db_path: str = "./chroma_db"
) -> None:
    """
    Store chunks + embeddings + metadata in ChromaDB.
    Deletes old chunks for this file first (handles re-indexing).
    """
    collection = get_collection(db_path)
    filename = os.path.basename(filepath)

    # Delete existing chunks for this file before adding new ones
    # Handles case where file changed — old chunks must go
    delete_file_chunks(filepath, db_path)

    ids = []
    docs = []
    metas = []
    embeds = []

    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        ids.append(f"{filename}_chunk_{i}")
        docs.append(chunk)
        metas.append({
            "source": filename,
            "chunk_index": i,
            "file_hash": file_hash
        })
        embeds.append(embedding.tolist())  # numpy array -> plain list for ChromaDB

    collection.add(
        ids=ids,
        embeddings=embeds,
        documents=docs,
        metadatas=metas
    )

    print(f"Indexed {len(chunks)} chunks from {filename}")


# ── DELETE ────────────────────────────────────────────────────────────────────

def delete_file_chunks(filepath: str, db_path: str = "./chroma_db") -> None:
    """
    Delete all chunks belonging to a specific file.
    Called before re-indexing a changed file.
    """
    collection = get_collection(db_path)
    filename = os.path.basename(filepath)

    # Get all chunk ids for this file
    results = collection.get(where={"source": filename})

    if results["ids"]:
        collection.delete(ids=results["ids"])
        print(f"Deleted {len(results['ids'])} old chunks for {filename}")


# ── QUERY ─────────────────────────────────────────────────────────────────────

def query_chunks(
    query_embedding,
    n_results: int = 3,
    db_path: str = "./chroma_db"
) -> list[dict]:
    """
    Find top-N most relevant chunks for a query embedding.

    Returns list of dicts:
    [
        {
            "text":   "We offer a 30-day refund...",
            "source": "refund-policy.md",
            "score":  0.87
        },
        ...
    ]
    """
    collection = get_collection(db_path)

    # Safety check — don't query empty collection
    if collection.count() == 0:
        print("Collection is empty. Run index first.")
        return []

    # Clamp n_results to available chunks
    n_results = min(n_results, collection.count())

    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )

    # distances in cosine space = 1 - similarity
    # convert to similarity score: 1 - distance
    output = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        output.append({
            "text":   doc,
            "source": meta["source"],
            "score":  round(1 - dist, 4)  # convert distance -> similarity
        })

    return output


# ── STATS ─────────────────────────────────────────────────────────────────────

def collection_stats(db_path: str = "./chroma_db") -> None:
    """Print basic stats about what's indexed."""
    collection = get_collection(db_path)
    total = collection.count()

    print(f"\n── ChromaDB Stats ──")
    print(f"Total chunks indexed: {total}")

    if total == 0:
        print("Collection is empty.")
        return

    # Get all metadatas to count per-file
    all_data = collection.get(include=["metadatas"])
    sources = {}
    for meta in all_data["metadatas"]:
        src = meta["source"]
        sources[src] = sources.get(src, 0) + 1

    print(f"Files indexed: {len(sources)}")
    for filename, count in sources.items():
        print(f"  {filename}: {count} chunks")