"""transforms/floodgate.py のユニットテスト。"""

from pyspark.sql import SparkSession

from dbx_bundle.transforms.floodgate import (
    FLOODGATE_POSITIONS_SCHEMA,
    build_floodgate_positions,
    parse_csa,
)

# --- parse_csa ---------------------------------------------------------------


def test_parse_csa_コメントと対局者名と手番を正しく抽出する() -> None:
    # Arrange
    csa_text = "' comment\nN+先手\nN-後手\n+7776FU\n-3334FU\n"

    # Act
    result = parse_csa(csa_text)

    # Assert
    assert result == {
        "moves": [
            {"move_usi": "7776FU", "player": "black"},
            {"move_usi": "3334FU", "player": "white"},
        ],
        "black_player": "先手",
        "white_player": "後手",
    }


def test_parse_csa_対局者名の記載がないと_空文字を返す() -> None:
    # Arrange
    csa_text = "+7776FU\n-3334FU\n"

    # Act
    result = parse_csa(csa_text)

    # Assert
    assert result["black_player"] == ""
    assert result["white_player"] == ""


def test_parse_csa_指し手がない場合_空リストを返す() -> None:
    # Arrange
    csa_text = "N+先手\nN-後手\n"

    # Act
    result = parse_csa(csa_text)

    # Assert
    assert result["moves"] == []


def test_parse_csa_手番は先手と後手が交互に切り替わる() -> None:
    # Arrange
    csa_text = "+7776FU\n-3334FU\n+2726FU\n"

    # Act
    result = parse_csa(csa_text)

    # Assert
    players = [move["player"] for move in result["moves"]]
    assert players == ["black", "white", "black"]


# --- build_floodgate_positions ------------------------------------------------


def test_build_floodgate_positions_1局分のCSAから局面レコードを生成する(
    spark: SparkSession,
) -> None:
    # Arrange
    bronze_df = spark.createDataFrame(
        [("game-1", "N+先手\nN-後手\n+7776FU\n-3334FU\n")],
        schema=["game_id", "csa"],
    )

    # Act
    result_df = build_floodgate_positions(spark, bronze_df)

    # Assert
    assert result_df.count() == 2
    rows = result_df.orderBy("move_number").collect()
    assert rows[0]["game_id"] == "game-1"
    assert rows[0]["move_number"] == 0
    assert rows[0]["move_usi"] == "7776FU"
    assert rows[0]["player"] == "black"
    assert rows[0]["black_player"] == "先手"
    assert rows[0]["white_player"] == "後手"
    assert rows[1]["move_number"] == 1
    assert rows[1]["move_usi"] == "3334FU"
    assert rows[1]["player"] == "white"


def test_build_floodgate_positions_複数局が含まれると_game_idごとに独立して局面が生成される(
    spark: SparkSession,
) -> None:
    # Arrange
    bronze_df = spark.createDataFrame(
        [
            ("game-1", "N+Alice\nN-Bob\n+7776FU\n"),
            ("game-2", "N+Carol\nN-Dave\n+2726FU\n-8384FU\n"),
        ],
        schema=["game_id", "csa"],
    )

    # Act
    result_df = build_floodgate_positions(spark, bronze_df)

    # Assert
    assert result_df.count() == 3
    game_ids = {
        row["game_id"] for row in result_df.select("game_id").distinct().collect()
    }
    assert game_ids == {"game-1", "game-2"}


def test_build_floodgate_positions_指し手がない棋譜は局面レコードを生成しない(
    spark: SparkSession,
) -> None:
    # Arrange
    bronze_df = spark.createDataFrame(
        [("game-1", "N+先手\nN-後手\n")],
        schema=["game_id", "csa"],
    )

    # Act
    result_df = build_floodgate_positions(spark, bronze_df)

    # Assert
    assert result_df.count() == 0


def test_build_floodgate_positions_Bronzeが空の場合_空のDataFrameを返す(
    spark: SparkSession,
) -> None:
    # Arrange
    bronze_df = spark.createDataFrame([], schema="game_id STRING, csa STRING")

    # Act
    result_df = build_floodgate_positions(spark, bronze_df)

    # Assert
    assert result_df.count() == 0
    assert result_df.schema == FLOODGATE_POSITIONS_SCHEMA


def test_build_floodgate_positions_出力スキーマがFLOODGATE_POSITIONS_SCHEMAと一致する(
    spark: SparkSession,
) -> None:
    # Arrange
    bronze_df = spark.createDataFrame(
        [("game-1", "N+先手\nN-後手\n+7776FU\n")],
        schema=["game_id", "csa"],
    )

    # Act
    result_df = build_floodgate_positions(spark, bronze_df)

    # Assert
    assert result_df.schema == FLOODGATE_POSITIONS_SCHEMA
