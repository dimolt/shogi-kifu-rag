from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from shogi_kif_rag.vector.models import SearchResult


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


class SearchIndex(ABC):
    """SearchIndexの共通インターフェース。

    ChromaDBやDatabricks AI Searchなど、異なるVector DB実装を
    統一的に扱うための抽象基底クラス。
    """


    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """クエリに基づいて類似ドキュメントを検索する。

        Args:
            query: 検索クエリテキスト。
            top_k: 返すドキュメントの最大数。デフォルトは5。

        Returns:
            検索結果のリスト。スコアの昇順（類似度が高い順）でソートされている。
        """
        pass
