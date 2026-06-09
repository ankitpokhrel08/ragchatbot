import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
# removed the hardcoded HF_HUB_OFFLINE line

from sentence_transformers import SentenceTransformer
import numpy as np

_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        cache_dir = os.path.abspath("./model_cache")
        os.makedirs(cache_dir, exist_ok=True)
        _model = SentenceTransformer(
            "all-MiniLM-L6-v2",
            cache_folder=cache_dir
        )
    return _model

def embed_chunks(chunks: list[str]) -> np.ndarray:
    model = get_model()
    return model.encode(chunks, show_progress_bar=False)

def embed_query(query: str) -> np.ndarray:
    model = get_model()
    return model.encode(query)