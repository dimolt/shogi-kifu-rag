from __future__ import annotations

from typing import TYPE_CHECKING

import chromadb as chromadb_lib

if TYPE_CHECKING:
    from shogi_kif_rag.vector.embedding.base import EmbeddingModel

from shogi_kif_rag.vector.base import SearchIndex
from shogi_kif_rag.vector.models import Document, SearchResult


class ChromaSearchIndex(SearchIndex):
    """ChromaDBのSearchIndex実装。

    DI可能な設計で、EmbeddingModelと永続化パスを外部から注入できる。
    `search` のみを提供し、コレクションを変更する操作は持たない。
    コレクションの構築（Embedding→登録）は`ChromaIndexBuilder` が担当する。
    """


    def __init__(
        self,
        persist_path: str,
        embedding_model: EmbeddingModel,
        collection_name: str,
    ) -> None:
        """ChromaSearchIndexを初期化する。

        Args:
            persist_path: 永続ストレージパス
            embedding_model: Embeddingモデルのインスタンス
            collection_name: 使用するコレクション名
        """
        self._persist_path = persist_path
        self._embedding_model = embedding_model
        self._collection_name = collection_name
        self._client: chromadb_lib.ClientAPI | None = None

    def _initialize_client(self) -> None:
        """ChromaDBクライアントを初期化する。

        既に初期化済みの場合は何もしない。
        """
        if self._client is not None:
            return

        self._client = chromadb_lib.PersistentClient(path=self._persist_path)

    def _get_collection(self) -> chromadb_lib.Collection:
        """コレクションを取得する。

        Returns:
            指定したCollectionオブジェクト。

        Raises:
            RuntimeError: クライアントが初期化されていない場合。
            Exception: コレクションが存在しない場合。
        """
        if self._client is None:
            msg = 'Client is not initialized. Call _initialize_client() first.'
            raise RuntimeError(msg)

        return self._client.get_collection(self._collection_name)

    def _ensure_collection_exists(self) -> None:
        """コレクションが存在することを確認する。

        存在しない場合は作成する。
        """
        self._initialize_client()

        if self._client is None:
            raise RuntimeError("Client initialization failed")

        try:
            self._client.get_collection(self._collection_name)
        except Exception:
            # コレクションが存在しない場合は作成
            self._client.create_collection(
                name=self._collection_name,
                metadata={'hnsw:space': 'cosine'},
            )


    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """クエリに基づいて類似ドキュメントを検索する。

        Args:
            query: 検索クエリテキスト。
            top_k: 返すドキュメントの最大数。デフォルトは5。

        Returns:
            検索結果のリスト。スコアの昇順（類似度が高い順）でソートされている。
        """
        self._ensure_collection_exists()

        query_embedding = self._embedding_model.encode(query)

        try:
            collection = self._get_collection()
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )

            search_results: list[SearchResult] = []

            documents = results["documents"]
            ids = results["ids"]
            metadatas = results["metadatas"]
            distances = results["distances"]
            if not documents or not ids or not metadatas or not distances:
                return search_results

            for i in range(len(documents[0])):
                document: Document = {
                    "id": ids[0][i],
                    "text": documents[0][i],
                    "metadata": metadatas[0][i],
                }

                search_results.append(
                    {
                        "document": document,
                        "score": distances[0][i],
                    }
                )

            return search_results
        except Exception as e:
            print(f'ChromaDB検索エラー: {e}')
            return []
