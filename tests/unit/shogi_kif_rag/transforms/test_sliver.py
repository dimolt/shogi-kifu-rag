"""silver.pyのユニットテスト。"""

from pathlib import Path

from pyspark.sql import SparkSession

from shogi_kif_rag.kif.schemas.shemas import get_spark_schema
from shogi_kif_rag.transforms.silver import build_positions

CSV_HEADER = (
    "game_id,move_number,sfen,prev_sfen,move_usi,player,black_player,"
    "white_player,best_move,score_cp,pv\n"
)


def _write_csv(path: Path, body: str) -> str:
    """テスト用CSVファイルを書き出しパスを返す。

    Args:
        path: 書き出し先のパス。
        body: ヘッダーを除く本文。

    Returns:
        書き出したファイルのパス文字列。
    """
    path.write_text(CSV_HEADER + body, encoding="utf-8")
    return str(path)


def test_build_positions_正常なCSVを渡すと_スキーマ通りのDataFrameを返す(
    spark: SparkSession, tmp_path: Path
) -> None:
    # Arrange
    csv_path = _write_csv(
        tmp_path / "analysis.csv",
        "G1,1,sfen1,sfen0,7g7f,black,Alice,Bob,7g7f,50,7g7f 3c3d\n",
    )

    # Act
    result_df = build_positions(spark, csv_path)

    # Assert
    assert result_df.schema == get_spark_schema()


def test_build_positions_score_cpが空文字のとき_nullとして読み込まれる(
    spark: SparkSession, tmp_path: Path
) -> None:
    # Arrange
    csv_path = _write_csv(
        tmp_path / "analysis.csv",
        "G1,1,sfen1,sfen0,7g7f,black,Alice,Bob,7g7f,,7g7f 3c3d\n",
    )

    # Act
    result_df = build_positions(spark, csv_path)

    # Assert
    assert result_df.first()["score_cp"] is None
