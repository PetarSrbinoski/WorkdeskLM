from __future__ import annotations

import logging
from functools import lru_cache
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger("embeddings")


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """
    Load embedding model once per process.
    Gen 1: CPU is safest (Docker GPU support is extra setup).
    """
    logger.info("loading embedding model name=%s", settings.embedding_model)
    model = SentenceTransformer(settings.embedding_model, device="cpu")
    return model


def embedding_dim() -> int:
    model = get_model()
    return int(model.get_sentence_embedding_dimension())


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Returns list of vectors ready for JSON.
    Normalize embeddings for cosine similarity.
    """
    if not texts:
        return []

    model = get_model()

    vectors = model.encode(
        texts,
        batch_size=int(settings.embedding_batch_size),
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    if isinstance(vectors, np.ndarray):
        return vectors.astype("float32").tolist()

    return [list(map(float, v)) for v in vectors]
