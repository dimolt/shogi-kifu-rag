from __future__ import annotations

import os
from typing import TYPE_CHECKING

import chromadb as chromadb_lib
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession

if TYPE_CHECKING:
    from shogi_kif_rag.vector.embedding.base import EmbeddingModel



class ChromadbService:
    """ChromaDB クライアントとコレクション管理を行うサービスクラス。

    シングルトンパターンを廃止し、依存注入を可能にした実装。
    コレクションの再構築機能を提供し、永続ストレージはDatabricks Volumeを使用する。

    Args:
        embedding_model: Embeddingモデルのインスタンス。
        persist_path: 永続ストレージパス。省略時は環境変数
            CHROMADB_PERSIST_PATH またはデフォルトパスを使用。
    """

    def __init__(
        self,
        embedding_model: EmbeddingModel,
        persist_path: str | None = None,
    ) -> None:
        """ChromadbServiceを初期化する。

        Args:
            embedding_model: Embeddingモデルのインスタンス。
            persist_path: 永続ストレージパス。省略時は環境変数
                CHROMADB_PERSIST_PATH またはデフォルトパスを使用。
        """
        if persist_path is None:
            persist_path = os.environ.get(
                'CHROMADB_PERSIST_PATH',
                '/Volumes/shogi/default/chromadb'
            )

        self._persist_path = persist_path
        self._embedding_model = embedding_model
        self._client: chromadb_lib.ClientAPI | None = None

    def _initialize_client(self) -> None:
        """ChromaDBクライアントを初期化する。

        既に初期化済みの場合は何もしない。
        """
        if self._client is not None:
            return

        self._client = chromadb_lib.PersistentClient(path=self._persist_path)

    def ensure_collection(self, collection_name: str) -> chromadb_lib.Collection:
        """コレクションが使用可能な状態にする。

        未初期化の場合はクライアントを生成する。
        コレクションが存在しない場合は作成する。

        Args:
            collection_name: コレクション名。

        Returns:
            Collectionオブジェクト。
        """
        self._initialize_client()

        if self._client is None:
            raise RuntimeError("Client initialization failed")

        try:
            return self._client.get_collection(collection_name)
        except Exception:
            return self._client.create_collection(
                name=collection_name,
                metadata={'hnsw:space': 'cosine'},
            )

    def rebuild_collections(
        self,
        spark: SparkSession | None = None,
        catalog: str = 'shogi',
    ) -> None:
        """すべてのコレクションを再構築する。

        クライアントが未初期化の場合は先に初期化する。

        Args:
            spark: SparkSession。省略時は getActiveSession() から取得する。
            catalog: カタログ名。デフォルトは 'shogi'。
        """
        self._initialize_client()
        if spark is None:
            spark = SparkSession.getActiveSession()
        if spark is None:
            raise RuntimeError("SparkSession is not available")

        self._rebuild_positions(spark, catalog)
        self._rebuild_floodgate(spark, catalog)
        self._rebuild_joseki(spark, catalog)

    def get_collection(self, name: str) -> chromadb_lib.Collection:
        """コレクションを取得する。

        Args:
            name: コレクション名。

        Returns:
            指定した Collection オブジェクト。

        Raises:
            RuntimeError: クライアントが初期化されていない場合。
            Exception: コレクションが存在しない場合。
        """
        if self._client is None:
            raise RuntimeError("Client is not initialized")
        return self._client.get_collection(name)

    def collection_exists(self, name: str) -> bool:
        """コレクションの存在を確認する。

        Args:
            name: コレクション名。

        Returns:
            コレクションが存在する場合は True。
        """
        if self._client is None:
            return False
        try:
            self._client.get_collection(name)
            return True
        except Exception:
            return False

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """テキストリストを Embedding に変換する。

        Args:
            texts: エンコード対象のテキストリスト。

        Returns:
            Embedding のリスト。
        """
        return self._embedding_model.encode_batch(texts)

    @staticmethod
    def clean_position_features(df: pd.DataFrame) -> pd.DataFrame:
        """position_features DataFrame から無効な search_text 行を除去する。

        Args:
            df: position_features の DataFrame。

        Returns:
            search_text が有効な行のみを含む DataFrame。
        """
        cleaned_df = df.copy()
        cleaned_df['search_text'] = cleaned_df['search_text'].apply(
            lambda value: '' if pd.isna(value) else str(value).strip()
        )
        is_valid = (
            cleaned_df['search_text'].notna()
            & (cleaned_df['search_text'] != '')
            & (cleaned_df['search_text'].str.lower() != 'nan')
            & (cleaned_df['search_text'].str.lower() != 'none')
        )
        return cleaned_df[is_valid]

    def _drop_and_create(self, name: str) -> chromadb_lib.Collection:
        """コレクションを削除して新規作成する。

        Args:
            name: コレクション名。

        Returns:
            新規作成した Collection オブジェクト。
        """
        if self._client is None:
            raise RuntimeError("Client is not initialized")
        try:
            self._client.delete_collection(name)
        except Exception:
            pass
        return self._client.create_collection(
            name=name,
            metadata={'hnsw:space': 'cosine'},
        )

    def _rebuild_positions(self, spark: SparkSession, catalog: str) -> None:
        """positions コレクションを再構築する。

        既存コレクションを削除後、
        Gold Table の position_features を読み込み、再作成する。

        Args:
            spark: SparkSession。
            catalog: カタログ名。
        """
        collection = self._drop_and_create('positions')

        df = spark.table(f'{catalog}.shogi_gold.position_features').toPandas()
        df = self.clean_position_features(df)

        if len(df) == 0:
            print('positions: 有効なデータがないためスキップします。')
            return

        texts = df['search_text'].tolist()
        embeddings = np.asarray(
            self.encode_batch(texts),
            dtype=np.float32,
        )
        collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=[{
                'game_id': str(row['game_id']),
                'move_number': int(row['move_number']),
                'sfen': str(row['sfen']),
                'move_usi': str(row['move_usi']),
                'player': str(row['player']),
                'move_quality': str(row['move_quality']),
                'score_cp': int(row['score_cp']),
            } for _, row in df.iterrows()],
            ids=[f'pos_{i}' for i in range(len(df))],
        )

    def _rebuild_floodgate(self, spark: SparkSession, catalog: str) -> None:
        """floodgate_positions コレクションを再構築する。

        既存コレクションを削除後、
        Gold Table の floodgate_position_features を読み込み、再作成する。
        テーブルが存在しない・空の場合はスキップする。

        Args:
            spark: SparkSession。
            catalog: カタログ名。
        """
        try:
            table_name = (
                f'{catalog}.shogi_gold.floodgate_position_features'
            )
            df = spark.table(table_name).toPandas()
        except Exception as e:
            print(f'floodgate_position_features テーブル読み込みスキップ: {e}')
            return

        if len(df) == 0:
            print('floodgate_position_features: データが空のためスキップします。')
            return

        collection = self._drop_and_create('floodgate_positions')

        search_texts = [
            f"局面: {row['sfen']} 指し手: {row['move_usi']}"
            for _, row in df.iterrows()  # type: ignore[attr-defined]
        ]
        embeddings = np.asarray(
            self.encode_batch(search_texts),
            dtype=np.float32,
        )
        collection.add(
            embeddings=embeddings,
            documents=search_texts,
            metadatas=[{
                'game_id': str(row['game_id']),
                'move_number': int(row['move_number']),
                'sfen': str(row['sfen']),
                'move_usi': str(row['move_usi']),
                'player': str(row['player']),
            } for _, row in df.iterrows()],  # type: ignore[attr-defined]
            ids=[f'floodgate_{i}' for i in range(len(df))],
        )

    def _rebuild_joseki(self, spark: SparkSession, catalog: str) -> None:
        """joseki_knowledge コレクションを再構築する。

        既存コレクションを削除後、
        Gold Table の joseki_features を読み込み、再作成する。
        テーブルが存在しない・空の場合はスキップする。

        Args:
            spark: SparkSession。
            catalog: カタログ名。
        """
        try:
            df = spark.table(f'{catalog}.shogi_gold.joseki_features').toPandas()
        except Exception as e:
            print(f'joseki_features テーブル読み込みスキップ: {e}')
            return

        if len(df) == 0:
            print('joseki_features: データが空のためスキップします。')
            return

        collection = self._drop_and_create('joseki_knowledge')

        search_texts = df['search_text'].tolist()  # type: ignore[index]
        embeddings = np.asarray(
            self.encode_batch(search_texts),
            dtype=np.float32,
        )
        collection.add(
            embeddings=embeddings,
            documents=search_texts,
            metadatas=[{
                'strategy': str(row['strategy']),
                'source': str(row['source']),
            } for _, row in df.iterrows()],  # type: ignore[attr-defined]
            ids=[f'joseki_{i}' for i in range(len(df))],
        )
