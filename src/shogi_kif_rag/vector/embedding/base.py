from __future__ import annotations

from typing import Protocol


class EmbeddingModel(Protocol):
    """Embeddingモデルの共通インターフェース。

    異なるEmbedding実装（SentenceTransformer、Databricks Endpointなど）を
    統一的に扱うためのProtocol。
    """

    def encode(self, text: str) -> list[float]:
        """単一テキストをEmbeddingベクトルに変換する。

        Args:
            text: エンコード対象のテキスト。

        Returns:
            Embeddingベクトル（floatのリスト）。
        """
        ...

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """テキストリストをEmbeddingベクトルのリストに変換する。

        Args:
            texts: エンコード対象のテキストリスト。

        Returns:
            Embeddingベクトルのリスト。
        """
        ...
