from __future__ import annotations

from shogi_kif_rag.vector.base import VectorStore
from shogi_kif_rag.vector.chromadb_service import ChromadbService
from shogi_kif_rag.vector.models import Document, SearchResult


class ChromaVectorStore(VectorStore):
    """ChromaDBのVectorStore実装。

    ChromadbServiceを内部で使用し、VectorStore共通インターフェースを提供する。
    """

    def __init__(self, collection_name: str = 'positions') -> None:
        """ChromaVectorStoreを初期化する。

        Args:
            collection_name: 使用するコレクション名。デフォルトは'positions'。
        """
        self._collection_name = collection_name
        self._service = ChromadbService.get_instance()

    def add(self, documents: list[Document]) -> None:
        """ドキュメントをVectorStoreに追加する。

        Args:
            documents: 追加するドキュメントのリスト。
        """
        self._service.ensure()
        collection = self._service.get_collection(self._collection_name)

        if len(documents) == 0:
            return

        texts = [doc['text'] for doc in documents]
        ids = [doc['id'] for doc in documents]
        metadatas = [doc['metadata'] for doc in documents]

        embeddings = self._service._encode(texts)

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
        self._service.ensure()
        query_embedding = self._service.encode_query(query)

        try:
            collection = self._service.get_collection(self._collection_name)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )

            search_results: list[SearchResult] = []
            for i in range(len(results['documents'][0])):
                document: Document = {
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                }
                search_results.append({
                    'document': document,
                    'score': results['distances'][0][i],
                })
            return search_results
        except Exception as e:
            print(f'ChromaDB検索エラー: {e}')
            return []

    def delete(self, document_ids: list[str]) -> None:
        """指定したIDのドキュメントを削除する。

        Args:
            document_ids: 削除対象のドキュメントIDリスト。
        """
        self._service.ensure()
        collection = self._service.get_collection(self._collection_name)
        collection.delete(ids=document_ids)

    def update(self, document_id: str, document: Document) -> None:
        """指定したIDのドキュメントを更新する。

        Args:
            document_id: 更新対象のドキュメントID。
            document: 更新後のドキュメント。
        """
        self._service.ensure()
        collection = self._service.get_collection(self._collection_name)

        embedding = self._service._encode([document['text']])

        collection.update(
            ids=[document_id],
            embeddings=embedding,
            documents=[document['text']],
            metadatas=[document['metadata']],
        )
