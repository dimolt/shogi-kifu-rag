"""silver.pyのユニットテスト。"""

from pathlib import Path

from pyspark.sql import SparkSession

from shogi_kif_rag.kif.schemas.shemas import get_analysis_schema
from shogi_kif_rag.transforms.silver import build_positions
from tests.helpers.csv_helpers import write_analysis_csv


def test_build_positions_正常なCSVを渡すと_スキーマ通りのDataFrameを返す(
    spark: SparkSession, tmp_path: Path
) -> None:
    # Arrange
    csv_path = write_analysis_csv(
        tmp_path / "analysis.csv",
        "G1,1,sfen1,sfen0,7g7f,black,Alice,Bob,7g7f,50,7g7f 3c3d\n",
    )

    # Act
    result_df = build_positions(spark, csv_path)

    # Assert
    assert result_df.schema == get_analysis_schema()


def test_build_positions_score_cpが空文字のとき_nullとして読み込まれる(
    spark: SparkSession, tmp_path: Path
) -> None:
    # Arrange
    csv_path = write_analysis_csv(
        tmp_path / "analysis.csv",
        "G1,1,sfen1,sfen0,7g7f,black,Alice,Bob,7g7f,,7g7f 3c3d\n",
    )

    # Act
    result_df = build_positions(spark, csv_path)

    # Assert
    assert result_df.first()["score_cp"] is None
