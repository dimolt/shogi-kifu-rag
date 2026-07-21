"""silver_transforms.pyのユニットテスト。"""

from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F  # noqa: N812

from dbx_bundle.pipelines.silver_transforms import (
    build_positions,
    get_analysis_schema,
)
from tests.helpers.csv_helpers import write_analysis_csv


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


def test_build_positions_複数行のCSVを正しく読み込む(
    spark: SparkSession, tmp_path: Path
) -> None:
    # Arrange
    csv_path = write_analysis_csv(
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


def test_build_positions_複数CSVファイルをワイルドカードで読み込める(
    spark: SparkSession, tmp_path: Path
) -> None:
    # Arrange
    write_analysis_csv(
        tmp_path / "small_01.csv",
        "G1,0,sfen0,,7g7f,black,Alice,Bob,7g7f,50,\n"
        "G1,1,sfen1,sfen0,3c3d,white,Alice,Bob,3c3d,30,\n"
    )
    write_analysis_csv(
        tmp_path / "small_02.csv",
        "G2,0,sfen0,,7g7f,black,Carol,David,7g7f,45,\n"
        "G2,1,sfen1,sfen0,3c3d,white,Carol,David,3c3d,25,\n"
    )

    # Act
    csv_path = str(tmp_path / "small_*.csv")
    result_df = build_positions(spark, csv_path)

    # Assert
    assert result_df.count() == 4
    game_ids = [row["game_id"] for row in result_df.select("game_id").distinct().collect()]
    assert set(game_ids) == {"G1", "G2"}


def test_build_positions_重複するgame_id_move_numberが含まれる場合_重複排除される(
    spark: SparkSession, tmp_path: Path
) -> None:
    # Arrange
    write_analysis_csv(
        tmp_path / "file1.csv",
        "G1,0,sfen0,,7g7f,black,Alice,Bob,7g7f,50,\n"
        "G1,1,sfen1,sfen0,3c3d,white,Alice,Bob,3c3d,30,\n"
    )
    write_analysis_csv(
        tmp_path / "file2.csv",
        "G1,0,sfen0,,7g7f,black,Alice,Bob,7g7f,55,\n"  # G1,0が重複
        "G1,2,sfen2,sfen1,2g2f,black,Alice,Bob,2g2f,20,\n"
    )

    # Act
    csv_path = str(tmp_path / "*.csv")
    result_df = build_positions(spark, csv_path)

    # Assert
    assert result_df.count() == 3  # 重複排除後は3行
    rows = result_df.filter(F.col("game_id") == "G1").orderBy("move_number").collect()
    assert rows[0]["move_number"] == 0
    assert rows[1]["move_number"] == 1
    assert rows[2]["move_number"] == 2


def test_build_positions_ヘッダーのみのCSVを渡すと_0行のDataFrameを返す(
    spark: SparkSession, tmp_path: Path
) -> None:
    # Arrange
    csv_path = write_analysis_csv(
        tmp_path / "analysis.csv",
        "",  # ヘッダーのみ・本文0行
    )

    # Act
    result_df = build_positions(spark, csv_path)

    # Assert
    assert result_df.count() == 0
    assert result_df.schema == get_analysis_schema()
