from __future__ import annotations

import chromadb as chromadb_lib
import pandas as pd
from pyspark.sql import SparkSession
from sentence_transformers import SentenceTransformer

CHROMA_PATH = '/tmp/shogi/chromadb'
EMBEDDING_MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
EMBED_BATCH_SIZE = 32

# モジュールレベルのシングルトンキャッシュ
_instance: ChromadbService | None = None


class ChromadbService:
    """ChromaDB クライアントと Embedding モデルを管理するサービスクラス。

    クライアント・モデルはインスタンス内部に隠蔽し、
    ensure() / rebuild_collections() の2つの public メソッドで操作する。
    モジュールレベルのシングルトンとして利用することを想定している。

    使用例:
        service = ChromadbService.get_instance()
        service.ensure()
        service.rebuild_collections()
    """

    def __init__(self) -> None:
        self._client: chromadb_lib.ClientAPI | None = None
        self._model: SentenceTransformer | None = None

    # ------------------------------------------------------------------
    # シングルトンアクセサ
    # ------------------------------------------------------------------

    @classmethod
    def get_instance(cls) -> ChromadbService:
        """モジュールレベルのシングルトンインスタンスを返す。

        Returns:
            ChromadbService の唯一のインスタンス。
        """
        global _instance
        if _instance is None:
            _instance = cls()
        return _instance

    # ------------------------------------------------------------------
    # Public メソッド
    # ------------------------------------------------------------------

    def ensure(self) -> None:
        """ChromaDB が使用可能な状態にする。

        未初期化の場合はクライアントとモデルを生成する。
        positions コレクションが存在しない場合は全コレクションを再構築する。
        初期化済みの場合は何もしない。
        """
        if self._is_ready():
            return

        spark = SparkSession.getActiveSession()
        self._model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self._client = chromadb_lib.PersistentClient(path=CHROMA_PATH)

        if not self._collection_exists('positions'):
            self.rebuild_collections(spark)

    def rebuild_collections(self, spark: SparkSession | None = None) -> None:
        """すべてのコレクションを再構築する。

        クライアント・モデルが未初期化の場合は先に ensure() を呼び出す。

        Args:
            spark: SparkSession。省略時は getActiveSession() から取得する。
        """
        self.ensure()
        if spark is None:
            spark = SparkSession.getActiveSession()
        if spark is None:
            raise RuntimeError("SparkSession is not available")

        self._rebuild_positions(spark)
        self._rebuild_floodgate(spark)
        self._rebuild_joseki(spark)

    # ------------------------------------------------------------------
    # 内部ユーティリティ
    # ------------------------------------------------------------------

    def encode_query(self, query: str) -> list[float]:
        """クエリテキストを Embedding ベクトルに変換する。

        Args:
            query: クエリテキスト。

        Returns:
            Embedding ベクトル（float のリスト）。
        """
        if self._model is None:
            raise RuntimeError("Model is not initialized")
        return self._model.encode(query).tolist()

    def get_collection(self, name: str) -> chromadb_lib.Collection:
        """コレクションを取得する。

        Args:
            name: コレクション名。

        Returns:
            指定した Collection オブジェクト。

        Raises:
            Exception: コレクションが存在しない場合。
        """
        if self._client is None:
            raise RuntimeError("Client is not initialized")
        return self._client.get_collection(name)

    def _is_ready(self) -> bool:
        """クライアントとモデルが両方初期化済みか確認する。

        Returns:
            両方初期化済みの場合は True。
        """
        return self._client is not None and self._model is not None

    def _collection_exists(self, name: str) -> bool:
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

    def _encode(self, texts: list[str], batch_size: int = EMBED_BATCH_SIZE) -> list:
        """テキストリストを Embedding に変換する。

        Args:
            texts: エンコード対象のテキストリスト。
            batch_size: バッチサイズ。

        Returns:
            Embedding のリスト。
        """
        if self._model is None:
            raise RuntimeError("Model is not initialized")
        return self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
        ).tolist()

    @staticmethod
    def _clean_position_features(df: pd.DataFrame) -> pd.DataFrame:
        """position_features DataFrame から無効な search_text 行を除去する。

        Args:
            df: position_features の DataFrame。

        Returns:
            search_text が有効な行のみを含む DataFrame。
        """
        df['search_text'] = df['search_text'].astype(str).str.strip()
        is_valid = (
            df['search_text'].notna()
            & (df['search_text'] != '')
            & (df['search_text'].str.lower() != 'nan')
        )
        return df[is_valid]

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

    # ------------------------------------------------------------------
    # コレクション別再構築
    # ------------------------------------------------------------------

    def _rebuild_positions(self, spark: SparkSession) -> None:
        """positions コレクションを再構築する。

        既存コレクションを削除後、
        Gold Table の position_features を読み込み、再作成する。

        Args:
            spark: SparkSession。
        """
        collection = self._drop_and_create('positions')

        df = spark.table('shogi.shogi_gold.position_features').toPandas()
        df = self._clean_position_features(df)

        if len(df) == 0:
            print('positions: 有効なデータがないためスキップします。')
            return

        texts = df['search_text'].tolist()
        collection.add(
            embeddings=self._encode(texts),
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

    def _rebuild_floodgate(self, spark: SparkSession) -> None:
        """floodgate_positions コレクションを再構築する。

        既存コレクションを削除後
        Silver Table の floodgate_positions を読み込み、再作成する。
        テーブルが存在しない・空の場合はスキップする。

        Args:
            spark: SparkSession。
        """
        try:
            df = spark.table('shogi.shogi_silver.floodgate_positions').toPandas()
        except Exception as e:
            print(f'floodgate_positions テーブル読み込みスキップ: {e}')
            return

        if len(df) == 0:
            print('floodgate_positions: データが空のためスキップします。')
            return

        collection = self._drop_and_create('floodgate_positions')

        search_texts = [
            f"局面: {row['sfen']} 指し手: {row['move_usi']}"
            for _, row in df.iterrows()  # type: ignore[attr-defined]
        ]
        collection.add(
            embeddings=self._encode(search_texts),
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

    def _rebuild_joseki(self, spark: SparkSession) -> None:
        """joseki_knowledge コレクションを再構築する。

        既存コレクションを削除後、
        Silver Table の joseki_knowledge を読み込み、再作成する。
        テーブルが存在しない・空の場合はスキップする。

        Args:
            spark: SparkSession。
        """
        try:
            df = spark.table('shogi.shogi_silver.joseki_knowledge').toPandas()
        except Exception as e:
            print(f'joseki_knowledge テーブル読み込みスキップ: {e}')
            return

        if len(df) == 0:
            print('joseki_knowledge: データが空のためスキップします。')
            return

        collection = self._drop_and_create('joseki_knowledge')

        contents = df['content'].tolist()  # type: ignore[index]
        collection.add(
            embeddings=self._encode(contents),
            documents=contents,
            metadatas=[{
                'strategy': str(row['strategy']),
                'source': str(row['source']),
            } for _, row in df.iterrows()],  # type: ignore[attr-defined]
            ids=[f'joseki_{i}' for i in range(len(df))],
        )
