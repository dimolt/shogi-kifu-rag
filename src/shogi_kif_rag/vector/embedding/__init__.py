from __future__ import annotations

from shogi_kif_rag.vector.embedding.base import EmbeddingModel
from shogi_kif_rag.vector.embedding.databricks_endpoint import DatabricksEmbedding
from shogi_kif_rag.vector.embedding.sentence_transformer import (
    SentenceTransformerEmbedding,
)

__all__ = [
    'EmbeddingModel',
    'SentenceTransformerEmbedding',
    'DatabricksEmbedding',
]
