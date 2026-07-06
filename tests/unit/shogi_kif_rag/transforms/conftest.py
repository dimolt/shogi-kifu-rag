"""pytest共有フィクスチャ。"""

import os
import sys

import pytest
from pyspark.sql import DataFrame, SparkSession

from shogi_kif_rag.kif.schemas.shemas import get_spark_schema

# Driverが使っているPython実行ファイルをWorkerにも強制させる
# (uv環境でPATH上に複数バージョンのPythonが存在する場合のバージョン不一致を防ぐ)
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable


@pytest.fixture(scope="session")
def spark() -> SparkSession:
    """テスト用SparkSessionを提供する。"""
    return (
        SparkSession.builder.master("local[1]")
        .appName("shogi_kif_rag_test")
        .getOrCreate()
    )


@pytest.fixture
def make_positions_df(spark: SparkSession):
    """get_spark_schema()に準拠したDataFrameを行データから生成するファクトリを提供する。

    行タプルの列順は get_spark_schema() と同一:
    (game_id, move_number, sfen, prev_sfen, move_usi, player,
     black_player, white_player, best_move, score_cp, pv)

    Args:
        spark: セッションフィクスチャ。

    Returns:
        行データのリストを受け取りDataFrameを返す関数。
    """

    def _make(rows: list[tuple]) -> DataFrame:
        return spark.createDataFrame(rows, schema=get_spark_schema())

    return _make
