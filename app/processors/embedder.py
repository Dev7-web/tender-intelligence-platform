"""
Text embedding generation using sentence-transformers.
"""

from __future__ import annotations

from typing import List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings


class TextEmbedder:
    def __init__(self) -> None:
        self._model: Optional[SentenceTransformer] = None
        self._dim: int = 384

    def _load_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            self._dim = int(self._model.get_sentence_embedding_dimension())
        return self._model

    def embed(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self._dim
        model = self._load_model()
        vector = np.asarray(model.encode(text, normalize_embeddings=True), dtype=float)
        return vector.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        model = self._load_model()
        embeddings = np.atleast_2d(model.encode(texts, normalize_embeddings=True))
        return embeddings.astype(float).tolist()
