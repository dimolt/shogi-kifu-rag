from __future__ import annotations

import os
from typing import TYPE_CHECKING

import chromadb as chromadb_lib

if TYPE_CHECKING:
    from shogi_kif_rag.vector.embedding.base import EmbeddingModel

from shogi_kif_rag.vector.base import VectorStore
from shogi_kif_rag.vector.models import Document, SearchResult


class ChromaDBVectorStore(VectorStore):
    """ChromaDBのVectorStore実装。

    シングルトンパターンを廃止し、依存注入を可能にした実装。
    EmbeddingModelを直接使用し、永続ストレージはDatabricks Volumeを使用する。

    Args:
        collection_name: 使用するコレクション名。デフォルトは'positions'。
        embedding_model: Embeddingモデルのインスタンス。
        persist_path: 永続ストレージパス。デフォルトは環境変数または
            '/Volumes/shogi/default/chromadb'。
    """

    def __init__(
        self,
        collection_name: str = 'positions',
        embedding_model: EmbeddingModel | None = None,
        persist_path: str | None = None,
    ) -> None:
        """ChromaDBVectorStoreを初期化する。

        Args:
            collection_name: 使用するコレクション名。デフォルトは'positions'。
            embedding_model: Embeddingモデルのインスタンス。
            persist_path: 永続ストレージパス。省略時は環境変数
                CHROMADB_PERSIST_PATH またはデフォルトパスを使用。
        """
        super().__init__(embedding_model=embedding_model)
        self._collection_name = collection_name

        if persist_path is None:
            persist_path = os.environ.get(
                'CHROMADB_PERSIST_PATH',
                '/Volumes/shogi/default/chromadb'
            )

        self._persist_path = persist_path
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
            raise RuntimeError("Client is not initialized. Call _initialize_client() first.")   #noqa: E501

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

    def add(self, documents: list[Document]) -> None:
        """ドキュメントをVectorStoreに追加する。

        Args:
            documents: 追加するドキュメントのリスト。
        """
        if len(documents) == 0:
            return

        self._ensure_collection_exists()
        collection = self._get_collection()

        texts = [doc['text'] for doc in documents]
        ids = [doc['id'] for doc in documents]
        metadatas = [doc['metadata'] for doc in documents]

        if self._embedding_model is not None:
            embeddings = self._embedding_model.encode_batch(texts)
        else:
            raise RuntimeError("EmbeddingModel is required for add operation")

        collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids,
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

        if self._embedding_model is None:
            raise RuntimeError("EmbeddingModel is required for search operation")

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

    def delete(self, document_ids: list[str]) -> None:
        """指定したIDのドキュメントを削除する。

        Args:
            document_ids: 削除対象のドキュメントIDリスト。
        """
        self._ensure_collection_exists()
        collection = self._get_collection()
        collection.delete(ids=document_ids)

    def update(self, document_id: str, document: Document) -> None:
        """指定したIDのドキュメントを更新する。

        Args:
            document_id: 更新対象のドキュメントID。
            document: 更新後のドキュメント。
        """
        self._ensure_collection_exists()
        collection = self._get_collection()

        if self._embedding_model is None:
            raise RuntimeError("EmbeddingModel is required for update operation")

        embedding = self._embedding_model.encode_batch([document['text']])[0]

        collection.update(
            ids=[document_id],
            embeddings=[embedding],
            documents=[document['text']],
            metadatas=[document['metadata']],
        )
