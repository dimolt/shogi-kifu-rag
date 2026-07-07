"""silver_transforms.pyのユニットテスト。"""

from pathlib import Path

from pyspark.sql import SparkSession

from databricks_bundle.pipelines.silver_transforms import (
    build_positions,
    get_analysis_schema,
)

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


def test_get_analysis_schema_正しいスキーマを返す() -> None:
    # Act
    schema = get_analysis_schema()

    # Assert
    assert len(schema.fields) == 11
    field_names = [field.name for field in schema.fields]
    expected_names = [
        "game_id", "move_number", "sfen", "prev_sfen", "move_usi", "player",
        "black_player", "white_player", "best_move", "score_cp", "pv"
    ]
    assert field_names == expected_names


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
    assert result_df.schema == get_analysis_schema()


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


def test_build_positions_複数行のCSVを正しく読み込む(
    spark: SparkSession, tmp_path: Path
) -> None:
    # Arrange
    csv_path = _write_csv(
        tmp_path / "analysis.csv",
        "G1,0,sfen0,,7g7f,black,Alice,Bob,7g7f,50,\n"
        "G1,1,sfen1,sfen0,3c3d,white,Alice,Bob,3c3d,30,\n"
    )

    # Act
    result_df = build_positions(spark, csv_path)

    # Assert
    assert result_df.count() == 2
    rows = result_df.collect()
    assert rows[0]["move_number"] == 0
    assert rows[1]["move_number"] == 1
