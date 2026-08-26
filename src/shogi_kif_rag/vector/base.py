from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from shogi_kif_rag.vector.models import Document, SearchResult


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


class VectorStore(ABC):
    """VectorStoreの共通インターフェース。

    ChromaDBやDatabricks AI Searchなど、異なるVector DB実装を
    統一的に扱うための抽象基底クラス。
    """

    def __init__(
        self,
        embedding_model: EmbeddingModel | None = None,
    ) -> None:
        """VectorStoreを初期化する。

        Args:
            embedding_model: Embeddingモデルのインスタンス。
                一部の実装では不要（サービス側でEmbedding生成を行う場合など）。
        """
        self._embedding_model = embedding_model

    @abstractmethod
    def add(self, documents: list[Document]) -> None:
        """ドキュメントをVectorStoreに追加する。

        Args:
            documents: 追加するドキュメントのリスト。
        """
        pass

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

    @abstractmethod
    def delete(self, document_ids: list[str]) -> None:
        """指定したIDのドキュメントを削除する。

        Args:
            document_ids: 削除対象のドキュメントIDリスト。
        """
        pass

    @abstractmethod
    def update(self, document_id: str, document: Document) -> None:
        """指定したIDのドキュメントを更新する。

        Args:
            document_id: 更新対象のドキュメントID。
            document: 更新後のドキュメント。
        """
        pass
