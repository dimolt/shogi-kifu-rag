from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from pyspark.sql import SparkSession

from shogi_kif_rag.vector.chromadb.service import ChromadbService as NewChromadbService


class ChromadbService:
    """既存のChromadbServiceとの後方互換性を提供するアダプター。

    新しいChromadbServiceへの移行期間中、既存コードの破壊的変更を防ぐために使用する。
    シングルトンパターンを維持しつつ、内部では新しい実装を使用する。

    注意: このアダプターは一時的なものであり、将来的には削除予定。
    新しいコードではChromaDBVectorStoreまたは新しいChromadbServiceを直接使用すること。
    """

    _instance: ChromadbService | None = None

    def __init__(self) -> None:
        """ChromadbServiceアダプターを初期化する。

        内部で新しいChromadbServiceを使用する。
        """
        # デフォルトのEmbeddingModelを使用
        from shogi_kif_rag.vector.embedding import SentenceTransformerEmbedding

        persist_path = os.environ.get(
            'CHROMADB_PERSIST_PATH',
            '/Volumes/shogi/default/chromadb'
        )

        self._embedding_model = SentenceTransformerEmbedding()
        self._service = NewChromadbService(
            embedding_model=self._embedding_model,
            persist_path=persist_path,
        )

    @classmethod
    def get_instance(cls) -> ChromadbService:
        """モジュールレベルのシングルトンインスタンスを返す。

        Returns:
            ChromadbService の唯一のインスタンス。
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def ensure(self, catalog: str = 'shogi') -> None:
        """ChromaDB が使用可能な状態にする。

        既存インターフェースとの互換性を維持。
        positions コレクションが存在しない場合は全コレクションを再構築する。

        Args:
            catalog: カタログ名。デフォルトは 'shogi'。
        """
        from pyspark.sql import SparkSession

        self._service._initialize_client()

        if not self._service.collection_exists('positions'):
            spark = SparkSession.getActiveSession()
            if spark is not None:
                self._service.rebuild_collections(spark, catalog)

    def rebuild_collections(
        self,
        spark: SparkSession | None = None,
        catalog: str = 'shogi',
    ) -> None:
        """すべてのコレクションを再構築する。

        Args:
            spark: SparkSession。省略時は getActiveSession() から取得する。
            catalog: カタログ名。デフォルトは 'shogi'。
        """
        self._service.rebuild_collections(spark, catalog)

    def encode_query(self, query: str) -> list[float]:
        """クエリテキストを Embedding ベクトルに変換する。

        既存インターフェースとの互換性を維持。

        Args:
            query: クエリテキスト。

        Returns:
            Embedding ベクトル（float のリスト）。
        """
        return self._embedding_model.encode(query)

    def get_collection(self, name: str):
        """コレクションを取得する。

        Args:
            name: コレクション名。

        Returns:
            指定した Collection オブジェクト。
        """
        return self._service.get_collection(name)

    def _is_ready(self) -> bool:
        """クライアントとモデルが両方初期化済みか確認する。

        Returns:
            両方初期化済みの場合は True。
        """
        return (
            self._service._client is not None
            and self._embedding_model is not None
        )

    def _collection_exists(self, name: str) -> bool:
        """コレクションの存在を確認する。

        Args:
            name: コレクション名。

        Returns:
            コレクションが存在する場合は True。
        """
        return self._service.collection_exists(name)

    def _encode(self, texts: list[str]) -> list:
        """テキストリストを Embedding に変換する。

        Args:
            texts: エンコード対象のテキストリスト。

        Returns:
            Embedding のリスト。
        """
        return self._service.encode_batch(texts)

    @staticmethod
    def _clean_position_features(df):
        """position_features DataFrame から無効な search_text 行を除去する。

        Args:
            df: position_features の DataFrame。

        Returns:
            search_text が有効な行のみを含む DataFrame。
        """
        return NewChromadbService.clean_position_features(df)
