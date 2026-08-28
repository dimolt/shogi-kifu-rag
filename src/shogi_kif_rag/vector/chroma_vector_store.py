from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shogi_kif_rag.vector.embedding.base import EmbeddingModel

from shogi_kif_rag.vector.base import SearchIndex
from shogi_kif_rag.vector.chromadb.adapter import ChromadbService
from shogi_kif_rag.vector.models import Document, SearchResult


class ChromaVectorStore(SearchIndex):
    """ChromaDBのSearchIndex実装。

    ChromadbServiceを内部で使用し、SearchIndex共通インターフェースを提供する。
    EmbeddingModelが指定された場合はそれを使用し、指定されない場合は
    ChromadbServiceのデフォルトEmbeddingを使用する。
    """

    def __init__(
        self,
        collection_name: str = 'positions',
        embedding_model: EmbeddingModel | None = None,
    ) -> None:
        """ChromaVectorStoreを初期化する。

        Args:
            collection_name: 使用するコレクション名。デフォルトは'positions'。
            embedding_model: Embeddingモデルのインスタンス。
                省略時はChromadbServiceのデフォルトEmbeddingを使用する。
        """
        super().__init__(embedding_model=embedding_model)
        self._collection_name = collection_name
        self._service = ChromadbService.get_instance()


    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """クエリに基づいて類似ドキュメントを検索する。

        Args:
            query: 検索クエリテキスト。
            top_k: 返すドキュメントの最大数。デフォルトは5。

        Returns:
            検索結果のリスト。スコアの昇順（類似度が高い順）でソートされている。
        """
        self._service.ensure()

        if self._embedding_model is not None:
            query_embedding = self._embedding_model.encode(query)
        else:
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
