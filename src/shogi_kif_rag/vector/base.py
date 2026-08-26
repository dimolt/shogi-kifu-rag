from __future__ import annotations

from abc import ABC, abstractmethod

from shogi_kif_rag.vector.models import Document, SearchResult


class VectorStore(ABC):
    """VectorStoreの共通インターフェース。

    ChromaDBやDatabricks AI Searchなど、異なるVector DB実装を
    統一的に扱うための抽象基底クラス。
    """

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
