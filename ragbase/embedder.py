from sentence_transformers import SentenceTransformer
import numpy as np

# Load once at module level — expensive to reload
_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print("Loading embedding model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def embed_chunks(chunks: list[str]) -> np.ndarray:
    """
    Takes a list of text chunks.
    Returns a numpy array of shape (n_chunks, 384).
    """
    model = get_model()
    embeddings = model.encode(chunks, show_progress_bar=True)
    return embeddings

def embed_query(query: str) -> np.ndarray:
    """
    Embed a single query string.
    Returns a 1D numpy array of shape (384,).
    Same model as embed_chunks — critical for cosine search to work.
    """
    model = get_model()
    return model.encode(query)