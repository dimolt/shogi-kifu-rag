"""pytest共有フィクスチャ。"""


import pytest
from pyspark.sql import DataFrame, SparkSession

from dbx_bundle.pipelines.silver_transforms import get_analysis_schema


@pytest.fixture(scope="session")
def spark() -> SparkSession:
    """テスト用SparkSessionを提供する。"""
    return (
        SparkSession.builder.master("local[1]")
        .appName("shogi_kif_rag_pipeline_test")
        .getOrCreate()
    )


@pytest.fixture
def make_positions_df(spark: SparkSession):
    """AnalysisRowスキーマに準拠したDataFrameを行データから生成するファクトリを提供する。

    行タプルの列順は AnalysisRowスキーマと同一:
    (game_id, move_number, sfen, prev_sfen, move_usi, player,
     black_player, white_player, best_move, score_cp, pv)

    Args:
        spark: セッションフィクスチャ。

    Returns:
        行データのリストを受け取りDataFrameを返す関数。
    """

    def _make(rows: list[tuple]) -> DataFrame:
        return spark.createDataFrame(rows, schema=get_analysis_schema())

    return _make
