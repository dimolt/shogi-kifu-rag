"""Silverテーブル（positions）のLayer 2統合テスト。

前提:
    対象テーブルは事前にデプロイ・実行済みであること（conftest.pyのpipeline_id同様）。
    ここではCSVパースロジック自体（test_silver_transforms.pyでカバー済み）ではなく、
    Unity Catalog上に実体化されたテーブルのスキーマ整合性・ビジネス不変条件を検証する。
    `@dp.expect`の発火確認（valid_game_id等）はtest_pipeline_expectations.pyの責務とし、
    本ファイルでは重複させない。

データ仕様メモ:
    - move_numberは0始まり。0は「開始局面」を表し、sfen/prev_sfenは同一値（初期配置）。
    - move_number>=1は、prev_sfenが直前move_numberのsfenと一致する。
    - playerは「その手を指した対局者（black/white）」を表し、
      black_player/white_playerは「対局全体の対局者名」を表す（両者は別軸の情報）。
"""

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F  #noqa: N812

from databricks_bundle.pipelines.silver_transforms import get_analysis_schema


def test_positionsテーブルのスキーマがget_analysis_schemaと一致する(
    positions_df: DataFrame,
) -> None:
    # Assert
    assert positions_df.schema == get_analysis_schema()


def test_positionsテーブルにデータが存在する(positions_df: DataFrame) -> None:
    # Assert
    assert positions_df.count() > 0


def test_positionsテーブルのmove_numberがgame_idごとに連番になっている(
    positions_df: DataFrame,
) -> None:
    """各game_id内でmove_numberが0始まりの連番（欠番・重複なし）になっていることを検証する。

    Arrange:
        positions_df fixtureから実データを取得する。
    Act:
        game_idごとにmove_numberを昇順ソートし、row_number()ベースの期待値
        （0始まり連番）と実際の値を比較する。
    Assert:
        実際のmove_numberと期待される連番が全行で一致すること。
    """
    # Arrange
    window = Window.partitionBy("game_id").orderBy("move_number")

    # Act
    result_df = positions_df.withColumn(
        "expected_move_number", F.row_number().over(window) - 1
    )
    mismatches = result_df.filter(
        F.col("move_number") != F.col("expected_move_number")
    )

    # Assert
    assert mismatches.count() == 0, (
        f"move_numberが連番になっていない行が存在する: "
        f"{mismatches.select('game_id', 'move_number').collect()}"
    )


def test_positionsテーブルの開始局面はsfenとprev_sfenが一致する(
    positions_df: DataFrame,
) -> None:
    """move_number=0（開始局面）で、sfenとprev_sfenが同一値であることを検証する。

    Arrange:
        positions_df fixtureからmove_number=0の行を抽出する。
    Act:
        sfenとprev_sfenを比較する。
    Assert:
        全ての開始局面行でsfen == prev_sfenであること。
    """
    # Arrange
    initial_rows = positions_df.filter(F.col("move_number") == 0)

    # Act
    mismatches = initial_rows.filter(F.col("sfen") != F.col("prev_sfen"))

    # Assert
    assert mismatches.count() == 0, (
        f"開始局面でsfenとprev_sfenが一致しない行が存在する: "
        f"{mismatches.select('game_id', 'sfen', 'prev_sfen').collect()}"
    )


def test_positionsテーブルのsfenチェーンが連続している(
    positions_df: DataFrame,
) -> None:
    """move_number>=1のprev_sfenが、直前move_numberのsfenと一致することを検証する。

    Arrange:
        positions_df fixtureから実データを取得する。
    Act:
        game_idごとにmove_number昇順でsfenをラグ取得し、move_number>=1の行について
        prev_sfenと比較する。
    Assert:
        move_number>=1の全行で、prev_sfenが直前move_numberのsfenと一致すること。
    """
    # Arrange
    window = Window.partitionBy("game_id").orderBy("move_number")

    # Act
    result_df = positions_df.withColumn("lag_sfen", F.lag("sfen").over(window))
    target_rows = result_df.filter(F.col("move_number") >= 1)
    mismatches = target_rows.filter(F.col("prev_sfen") != F.col("lag_sfen"))

    # Assert
    assert mismatches.count() == 0, (
        f"sfenチェーンが不連続な行が存在する: "
        f"{mismatches.select('game_id', 'move_number', 'prev_sfen', 'lag_sfen').collect()}"
    )


def test_positionsテーブルのblack_player_white_playerがgame_id内で一貫している(
    positions_df: DataFrame,
) -> None:
    """同一game_id内でblack_player/white_playerの値がブレていないことを検証する。

    Arrange:
        positions_df fixtureから実データを取得する。
    Act:
        game_idごとにblack_player/white_playerのユニーク数を集計する。
    Assert:
        全game_idでblack_player・white_playerがそれぞれ1種類のみであること。
    """
    # Act
    result_df = positions_df.groupBy("game_id").agg(
        F.countDistinct("black_player").alias("black_player_count"),
        F.countDistinct("white_player").alias("white_player_count"),
    )
    inconsistent = result_df.filter(
        (F.col("black_player_count") > 1) | (F.col("white_player_count") > 1)
    )

    # Assert
    assert inconsistent.count() == 0, (
        f"black_player/white_playerがgame_id内で複数種類存在する: "
        f"{inconsistent.collect()}"
    )
