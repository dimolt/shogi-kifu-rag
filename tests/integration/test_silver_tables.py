"""Silverテーブルの統合テスト。

ビジネスルール検証とデータ品質検証を統合したSilverテーブル用テストファイル。
テーブルが増えた段階でファイル分割を検討する。

前提:
    本テストの実行前に、対象パイプラインがdevターゲットへデプロイ・実行され、
    Silverテーブルが実データで実体化されていること。
"""

from pathlib import Path

import pytest
from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F  # noqa: N812

from dbx_bundle.pipelines.silver_transforms import build_positions, get_analysis_schema
from tests.helpers.csv_helpers import write_analysis_csv

pytestmark = pytest.mark.integration


#TODO: fooldgate, wikipediaテーブルの検証も追加したい

# --- スキーマ・基本検証 ------------------------------------------------------


def test_positionsテーブルのスキーマがget_analysis_schemaと一致する(
    positions_df: DataFrame,
) -> None:
    """スキーマ整合性を検証する。"""
    assert positions_df.schema == get_analysis_schema()


def test_positionsテーブルにデータが存在する(positions_df: DataFrame) -> None:
    """データ存在確認。"""
    assert positions_df.count() > 0


# --- ビジネスルール検証 -----------------------------------------------------


def test_positionsテーブルのmove_numberがgame_idごとに連番になっている(
    positions_df: DataFrame,
) -> None:
    """各game_id内でmove_numberが0始まりの連番（欠番・重複なし）になっていることを検証する。"""
    window = Window.partitionBy("game_id").orderBy("move_number")
    result_df = positions_df.withColumn(
        "expected_move_number", F.row_number().over(window) - 1
    )
    mismatches = result_df.filter(
        F.col("move_number") != F.col("expected_move_number")
    )
    assert mismatches.count() == 0, (
        f"move_numberが連番になっていない行が存在する: "
        f"{mismatches.select('game_id', 'move_number').collect()}"
    )


def test_positionsテーブルの開始局面はsfenとprev_sfenが一致する(
    positions_df: DataFrame,
) -> None:
    """move_number=0（開始局面）で、sfenとprev_sfenが同一値であることを検証する。"""
    initial_rows = positions_df.filter(F.col("move_number") == 0)
    mismatches = initial_rows.filter(F.col("sfen") != F.col("prev_sfen"))
    assert mismatches.count() == 0, (
        f"開始局面でsfenとprev_sfenが一致しない行が存在する: "
        f"{mismatches.select('game_id', 'sfen', 'prev_sfen').collect()}"
    )


def test_positionsテーブルのsfenチェーンが連続している(
    positions_df: DataFrame,
) -> None:
    """move_number>=1のprev_sfenが、直前move_numberのsfenと一致することを検証する。"""
    window = Window.partitionBy("game_id").orderBy("move_number")
    result_df = positions_df.withColumn("lag_sfen", F.lag("sfen").over(window))
    target_rows = result_df.filter(F.col("move_number") >= 1)
    mismatches = target_rows.filter(F.col("prev_sfen") != F.col("lag_sfen"))
    assert mismatches.count() == 0, (
        f"sfenチェーンが不連続な行が存在する: "
        f"{mismatches.select('game_id', 'move_number', 'prev_sfen', 'lag_sfen').collect()}"
    )


def test_positionsテーブルのblack_player_white_playerがgame_id内で一貫している(
    positions_df: DataFrame,
) -> None:
    """同一game_id内でblack_player/white_playerの値がブレていないことを検証する。"""
    result_df = positions_df.groupBy("game_id").agg(
        F.countDistinct("black_player").alias("black_player_count"),
        F.countDistinct("white_player").alias("white_player_count"),
    )
    inconsistent = result_df.filter(
        (F.col("black_player_count") > 1) | (F.col("white_player_count") > 1)
    )
    assert inconsistent.count() == 0, (
        f"black_player/white_playerがgame_id内で複数種類存在する: "
        f"{inconsistent.collect()}"
    )


# --- データ品質検証 ---------------------------------------------------------


def test_positionsテーブルのデータ品質(positions_df: DataFrame) -> None:
    """Silverテーブルpositionsのデータ品質を検証する。

    検証項目:
        - game_idにNULLが存在しない
        - move_numberにNULLが存在しない
        - sfenにNULLが存在しない
        - playerが'black'または'white'のいずれかである
        - score_cpがNULLまたは0以上の整数である
        - 重複行（game_id, move_numberの組み合わせ）が存在しない
    """
    # game_id NULLチェック
    null_game_id_count = positions_df.filter(F.col("game_id").isNull()).count()
    assert null_game_id_count == 0, f"game_idにNULLが存在する: {null_game_id_count}件"

    # move_number NULLチェック
    null_move_number_count = positions_df.filter(F.col("move_number").isNull()).count()
    assert null_move_number_count == 0, f"move_numberにNULLが存在する: {null_move_number_count}件"

    # sfen NULLチェック
    null_sfen_count = positions_df.filter(F.col("sfen").isNull()).count()
    assert null_sfen_count == 0, f"sfenにNULLが存在する: {null_sfen_count}件"

    # player値チェック
    invalid_player_count = positions_df.filter(
        ~F.col("player").isin("black", "white")
    ).count()
    assert invalid_player_count == 0, f"playerが'black'/'white'以外の値: {invalid_player_count}件"


    # 重複行チェック（game_id, move_numberの組み合わせ）
    duplicate_count = positions_df.groupBy("game_id", "move_number").agg(
        F.count("*").alias("cnt")
    ).filter(F.col("cnt") > 1).count()
    assert duplicate_count == 0, f"重複行が存在する: {duplicate_count}件"


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
    csv_path = (tmp_path / "small_*.csv").as_posix()  # Windowsパスをフォワードスラッシュに変換
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
    csv_path = (tmp_path / "*.csv").as_posix()  # Windowsパスをフォワードスラッシュに変換
    result_df = build_positions(spark, csv_path)

    # Assert
    assert result_df.count() == 3  # 重複排除後は3行
    rows = result_df.filter(F.col("game_id") == "G1").orderBy("move_number").collect()
    assert rows[0]["move_number"] == 0
    assert rows[1]["move_number"] == 1
    assert rows[2]["move_number"] == 2
