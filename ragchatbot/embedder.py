import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from sentence_transformers import SentenceTransformer
import numpy as np

_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder="./model_cache",local_files_only=False)
    return _model

def embed_chunks(chunks: list[str]) -> np.ndarray:
    model = get_model()
    return model.encode(chunks, show_progress_bar=False)

def embed_query(query: str) -> np.ndarray:
    model = get_model()
    return model.encode(query)