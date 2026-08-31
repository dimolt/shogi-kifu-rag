"""search_documents.pyのユニットテスト。"""

import json

import pytest
from pyspark.sql import DataFrame, SparkSession

from shogi_kif_rag.transforms.search_documents import (
    _normalize_floodgate,
    _normalize_joseki,
    _normalize_positions,
    build_search_documents,
)

# --- Fixtures ----------------------------------------------------------------


@pytest.fixture(scope="session")
def spark() -> SparkSession:
    """テスト用SparkSessionを提供する。"""
    return (
        SparkSession.builder.master("local[1]")
        .appName("shogi_kif_rag_search_documents_test")
        .getOrCreate()
    )


@pytest.fixture
def make_positions_df(spark: SparkSession):
    """position_featuresスキーマに準拠したDataFrameを行データから生成するファクトリを提供する。

    行タプルの列順は position_features スキーマと同一:
    (game_id, move_number, sfen, prev_sfen, move_usi, player,
     black_player, white_player, best_move, score_cp, pv,
     score_from_turn, score_delta, is_best_move, is_blunder,
     move_quality, search_text)

    Args:
        spark: セッションフィクスチャ。

    Returns:
        行データのリストを受け取りDataFrameを返す関数。
    """

    def _make(rows: list[tuple]) -> DataFrame:
        schema = "game_id string, move_number int, sfen string, prev_sfen string, move_usi string, player string, black_player string, white_player string, best_move string, score_cp int, pv string, score_from_turn int, score_delta int, is_best_move boolean, is_blunder boolean, move_quality string, search_text string"
        return spark.createDataFrame(rows, schema=schema)

    return _make


@pytest.fixture
def make_floodgate_df(spark: SparkSession):
    """floodgate_position_featuresスキーマに準拠したDataFrameを行データから生成するファクトリを提供する。

    行タプルの列順は floodgate_position_features スキーマと同一:
    (game_id, move_number, sfen, move_usi, player, black_player, white_player, search_text)

    Args:
        spark: セッションフィクスチャ。

    Returns:
        行データのリストを受け取りDataFrameを返す関数。
    """

    def _make(rows: list[tuple]) -> DataFrame:
        schema = "game_id string, move_number int, sfen string, move_usi string, player string, black_player string, white_player string, search_text string"
        return spark.createDataFrame(rows, schema=schema)

    return _make


@pytest.fixture
def make_joseki_df(spark: SparkSession):
    """joseki_featuresスキーマに準拠したDataFrameを行データから生成するファクトリを提供する。

    行タプルの列順は joseki_features スキーマと同一:
    (strategy, content, source, search_text)

    Args:
        spark: セッションフィクスチャ。

    Returns:
        行データのリストを受け取りDataFrameを返す関数。
    """

    def _make(rows: list[tuple]) -> DataFrame:
        schema = "strategy string, content string, source string, search_text string"
        return spark.createDataFrame(rows, schema=schema)

    return _make


# --- _normalize_positions -----------------------------------------------------


def test_normalize_positions_idが正しい形式で生成される(
    make_positions_df,
) -> None:
    # Arrange
    df = make_positions_df(
        [("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 100, "", 100, None, True, False, "best", "局面: sfen0 指し手: 7g7f")]
    )

    # Act
    result_df = _normalize_positions(df)

    # Assert
    assert result_df.first()["id"] == "position:G1:0"


def test_normalize_positions_source_typeがpositionになる(
    make_positions_df,
) -> None:
    # Arrange
    df = make_positions_df(
        [("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 100, "", 100, None, True, False, "best", "局面: sfen0 指し手: 7g7f")]
    )

    # Act
    result_df = _normalize_positions(df)

    # Assert
    assert result_df.first()["source_type"] == "position"


def test_normalize_positions_textがsearch_textと一致する(
    make_positions_df,
) -> None:
    # Arrange
    df = make_positions_df(
        [("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 100, "", 100, None, True, False, "best", "局面: sfen0 指し手: 7g7f")]
    )

    # Act
    result_df = _normalize_positions(df)

    # Assert
    assert result_df.first()["text"] == "局面: sfen0 指し手: 7g7f"


def test_normalize_positions_metadataに必要なフィールドが含まれる(
    make_positions_df,
) -> None:
    # Arrange
    df = make_positions_df(
        [("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 100, "", 100, None, True, False, "best", "局面: sfen0 指し手: 7g7f")]
    )

    # Act
    result_df = _normalize_positions(df)
    metadata = json.loads(result_df.first()["metadata"])

    # Assert
    assert metadata["game_id"] == "G1"
    assert metadata["move_number"] == 0
    assert metadata["sfen"] == "sfen0"
    assert metadata["move_usi"] == "7g7f"
    assert metadata["player"] == "black"
    assert metadata["black_player"] == "Alice"
    assert metadata["white_player"] == "Bob"
    assert metadata["best_move"] == "7g7f"
    assert metadata["score_cp"] == 100
    assert metadata["move_quality"] == "best"


def test_normalize_positions出力列が共通スキーマと一致する(
    make_positions_df,
) -> None:
    # Arrange
    df = make_positions_df(
        [("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 100, "", 100, None, True, False, "best", "局面: sfen0 指し手: 7g7f")]
    )

    # Act
    result_df = _normalize_positions(df)

    # Assert
    assert set(result_df.columns) == {"id", "text", "metadata", "source_type"}


# --- _normalize_floodgate -----------------------------------------------------


def test_normalize_floodgate_idが正しい形式で生成される(
    make_floodgate_df,
) -> None:
    # Arrange
    df = make_floodgate_df(
        [("G1", 0, "sfen0", "7g7f", "black", "Alice", "Bob", "局面: sfen0 指し手: 7g7f")]
    )

    # Act
    result_df = _normalize_floodgate(df)

    # Assert
    assert result_df.first()["id"] == "floodgate:G1:0"


def test_normalize_floodgate_source_typeがfloodgateになる(
    make_floodgate_df,
) -> None:
    # Arrange
    df = make_floodgate_df(
        [("G1", 0, "sfen0", "7g7f", "black", "Alice", "Bob", "局面: sfen0 指し手: 7g7f")]
    )

    # Act
    result_df = _normalize_floodgate(df)

    # Assert
    assert result_df.first()["source_type"] == "floodgate"


def test_normalize_floodgate_textがsearch_textと一致する(
    make_floodgate_df,
) -> None:
    # Arrange
    df = make_floodgate_df(
        [("G1", 0, "sfen0", "7g7f", "black", "Alice", "Bob", "局面: sfen0 指し手: 7g7f")]
    )

    # Act
    result_df = _normalize_floodgate(df)

    # Assert
    assert result_df.first()["text"] == "局面: sfen0 指し手: 7g7f"


def test_normalize_floodgate_metadataに必要なフィールドが含まれる(
    make_floodgate_df,
) -> None:
    # Arrange
    df = make_floodgate_df(
        [("G1", 0, "sfen0", "7g7f", "black", "Alice", "Bob", "局面: sfen0 指し手: 7g7f")]
    )

    # Act
    result_df = _normalize_floodgate(df)
    metadata = json.loads(result_df.first()["metadata"])

    # Assert
    assert metadata["game_id"] == "G1"
    assert metadata["move_number"] == 0
    assert metadata["sfen"] == "sfen0"
    assert metadata["move_usi"] == "7g7f"
    assert metadata["player"] == "black"
    assert metadata["black_player"] == "Alice"
    assert metadata["white_player"] == "Bob"


def test_normalize_floodgate出力列が共通スキーマと一致する(
    make_floodgate_df,
) -> None:
    # Arrange
    df = make_floodgate_df(
        [("G1", 0, "sfen0", "7g7f", "black", "Alice", "Bob", "局面: sfen0 指し手: 7g7f")]
    )

    # Act
    result_df = _normalize_floodgate(df)

    # Assert
    assert set(result_df.columns) == {"id", "text", "metadata", "source_type"}


# --- _normalize_joseki -------------------------------------------------------


def test_normalize_joseki_idが正しい形式で生成される(
    make_joseki_df,
) -> None:
    # Arrange
    df = make_joseki_df(
        [("矢倉", "矢倉定跡の解説", "wikipedia", "矢倉定跡の解説")]
    )

    # Act
    result_df = _normalize_joseki(df)

    # Assert
    assert result_df.first()["id"] == "joseki:矢倉"


def test_normalize_joseki_source_typeがjosekiになる(
    make_joseki_df,
) -> None:
    # Arrange
    df = make_joseki_df(
        [("矢倉", "矢倉定跡の解説", "wikipedia", "矢倉定跡の解説")]
    )

    # Act
    result_df = _normalize_joseki(df)

    # Assert
    assert result_df.first()["source_type"] == "joseki"


def test_normalize_joseki_textがsearch_textと一致する(
    make_joseki_df,
) -> None:
    # Arrange
    df = make_joseki_df(
        [("矢倉", "矢倉定跡の解説", "wikipedia", "矢倉定跡の解説")]
    )

    # Act
    result_df = _normalize_joseki(df)

    # Assert
    assert result_df.first()["text"] == "矢倉定跡の解説"


def test_normalize_joseki_metadataに必要なフィールドが含まれる(
    make_joseki_df,
) -> None:
    # Arrange
    df = make_joseki_df(
        [("矢倉", "矢倉定跡の解説", "wikipedia", "矢倉定跡の解説")]
    )

    # Act
    result_df = _normalize_joseki(df)
    metadata = json.loads(result_df.first()["metadata"])

    # Assert
    assert metadata["strategy"] == "矢倉"
    assert metadata["content"] == "矢倉定跡の解説"
    assert metadata["source"] == "wikipedia"


def test_normalize_joseki出力列が共通スキーマと一致する(
    make_joseki_df,
) -> None:
    # Arrange
    df = make_joseki_df(
        [("矢倉", "矢倉定跡の解説", "wikipedia", "矢倉定跡の解説")]
    )

    # Act
    result_df = _normalize_joseki(df)

    # Assert
    assert set(result_df.columns) == {"id", "text", "metadata", "source_type"}


# --- build_search_documents ---------------------------------------------------


def test_build_search_documents_3ソースが正しくUNIONされる(
    make_positions_df,
    make_floodgate_df,
    make_joseki_df,
) -> None:
    # Arrange
    positions_df = make_positions_df(
        [("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 100, "", 100, None, True, False, "best", "局面: sfen0 指し手: 7g7f")]
    )
    floodgate_df = make_floodgate_df(
        [("G2", 0, "sfen1", "2g2f", "black", "Carol", "Dave", "局面: sfen1 指し手: 2g2f")]
    )
    joseki_df = make_joseki_df(
        [("矢倉", "矢倉定跡の解説", "wikipedia", "矢倉定跡の解説")]
    )

    # Act
    result_df = build_search_documents(positions_df, floodgate_df, joseki_df)

    # Assert
    assert result_df.count() == 3


def test_build_search_documents_source_typeで正しく識別できる(
    make_positions_df,
    make_floodgate_df,
    make_joseki_df,
) -> None:
    # Arrange
    positions_df = make_positions_df(
        [("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 100, "", 100, None, True, False, "best", "局面: sfen0 指し手: 7g7f")]
    )
    floodgate_df = make_floodgate_df(
        [("G2", 0, "sfen1", "2g2f", "black", "Carol", "Dave", "局面: sfen1 指し手: 2g2f")]
    )
    joseki_df = make_joseki_df(
        [("矢倉", "矢倉定跡の解説", "wikipedia", "矢倉定跡の解説")]
    )

    # Act
    result_df = build_search_documents(positions_df, floodgate_df, joseki_df)

    # Assert
    source_types = {row["source_type"] for row in result_df.collect()}
    assert source_types == {"position", "floodgate", "joseki"}


def test_build_search_documents空DataFrameでも例外にならない(
    make_positions_df,
    make_floodgate_df,
    make_joseki_df,
) -> None:
    # Arrange
    positions_df = make_positions_df([])
    floodgate_df = make_floodgate_df([])
    joseki_df = make_joseki_df([])

    # Act
    result_df = build_search_documents(positions_df, floodgate_df, joseki_df)

    # Assert
    assert result_df.count() == 0


def test_build_search_documents欠損値が含まれていても例外にならない(
    make_positions_df,
    make_floodgate_df,
    make_joseki_df,
) -> None:
    # Arrange
    positions_df = make_positions_df(
        [("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 100, "", 100, None, True, False, "best", "局面: sfen0 指し手: 7g7f")]
    )
    floodgate_df = make_floodgate_df(
        [("G2", 0, "sfen1", "2g2f", "black", "Carol", "Dave", "局面: sfen1 指し手: 2g2f")]
    )
    joseki_df = make_joseki_df(
        [("矢倉", "矢倉定跡の解説", "wikipedia", "矢倉定跡の解説")]
    )

    # Act
    result_df = build_search_documents(positions_df, floodgate_df, joseki_df)

    # Assert
    assert result_df.count() == 3


def test_build_search_documents出力スキーマが共通スキーマと一致する(
    make_positions_df,
    make_floodgate_df,
    make_joseki_df,
) -> None:
    # Arrange
    positions_df = make_positions_df(
        [("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 100, "", 100, None, True, False, "best", "局面: sfen0 指し手: 7g7f")]
    )
    floodgate_df = make_floodgate_df(
        [("G2", 0, "sfen1", "2g2f", "black", "Carol", "Dave", "局面: sfen1 指し手: 2g2f")]
    )
    joseki_df = make_joseki_df(
        [("矢倉", "矢倉定跡の解説", "wikipedia", "矢倉定跡の解説")]
    )

    # Act
    result_df = build_search_documents(positions_df, floodgate_df, joseki_df)

    # Assert
    assert set(result_df.columns) == {"id", "text", "metadata", "source_type"}
