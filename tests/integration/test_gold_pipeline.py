"""Gold層テーブルのLayer 2統合テスト。

Unity Catalog上に実体化されたposition_features / game_summaryテーブルを
直接クエリし、単体テストでは検証できないスキーマ整合性・分散実行下での
集計の正しさを確認する。

前提:
    本テストの実行前に、対象パイプラインがdevターゲットへデプロイ・実行され、
    Gold層のテーブルが実データで実体化されていること。
"""
import json

from pyspark.sql import DataFrame
from pyspark.sql import functions as F  #noqa: N812

_EXPECTED_POSITION_FEATURES_COLUMNS = {
    "game_id", "move_number", "sfen", "prev_sfen", "move_usi", "player",
    "black_player", "white_player", "best_move", "score_cp", "pv",
    "score_from_turn", "score_delta", "is_best_move", "is_blunder",
    "move_quality", "search_text",
}

_EXPECTED_GAME_SUMMARY_COLUMNS = {
    "game_id", "black_player", "white_player", "total_moves", "final_score_cp",
    "black_blunders", "white_blunders", "score_series_json",
}

_ALLOWED_MOVE_QUALITIES = {"start", "best", "blunder", "normal"}


# --- position_features -------------------------------------------------------


def test_position_featuresテーブルのスキーマが仕様通りの列集合と一致する(
    position_features_df: DataFrame,
) -> None:
    # Act
    actual_columns = set(position_features_df.columns)

    # Assert
    assert actual_columns == _EXPECTED_POSITION_FEATURES_COLUMNS


def test_position_featuresテーブルにデータが存在する(position_features_df: DataFrame) -> None:
    # Act
    row_count = position_features_df.count()

    # Assert
    assert row_count > 0


def test_position_featuresテーブルの行数がpositionsテーブルと一致する(
    position_features_df: DataFrame, positions_df: DataFrame
) -> None:
    """position_featuresはpositionsの全行に特徴量列を付与したものであるため、
    行数が完全に一致するはずである。
    """
    # Arrange
    positions_count = positions_df.count()

    # Act
    position_features_count = position_features_df.count()

    # Assert
    assert position_features_count == positions_count


def test_position_featuresテーブルのmove_qualityが許容セット外の値を持たない(
    position_features_df: DataFrame,
) -> None:
    # Act
    invalid_count = position_features_df.filter(
        ~F.col("move_quality").isin(_ALLOWED_MOVE_QUALITIES)
    ).count()

    # Assert
    assert invalid_count == 0


def test_position_featuresテーブルのmove_number0は_move_qualityが必ずstartになる(
    position_features_df: DataFrame,
) -> None:
    # Act
    invalid_start_count = position_features_df.filter(
        (F.col("move_number") == 0) & (F.col("move_quality") != "start")
    ).count()

    # Assert
    assert invalid_start_count == 0


# --- game_summary --------------------------------------------------------------


def test_game_summaryテーブルのスキーマが仕様通りの列集合と一致する(
    game_summary_df: DataFrame,
) -> None:
    # Act
    actual_columns = set(game_summary_df.columns)

    # Assert
    assert actual_columns == _EXPECTED_GAME_SUMMARY_COLUMNS


def test_game_summaryテーブルにデータが存在する(game_summary_df: DataFrame) -> None:
    # Act
    row_count = game_summary_df.count()

    # Assert
    assert row_count > 0


def test_game_summaryテーブルはgame_idごとに1行のみ存在する(
    game_summary_df: DataFrame,
) -> None:
    # Arrange
    total_count = game_summary_df.count()

    # Act
    distinct_game_id_count = game_summary_df.select("game_id").distinct().count()

    # Assert
    assert total_count == distinct_game_id_count


def test_game_summaryテーブルのtotal_movesは0以上の値になっている(
    game_summary_df: DataFrame,
) -> None:
    # Act
    invalid_count = game_summary_df.filter(
        F.col("total_moves").isNull() | (F.col("total_moves") < 0)
    ).count()

    # Assert
    assert invalid_count == 0


def test_game_summaryテーブルのfinal_score_cpがnullの行が存在しない(
    game_summary_df: DataFrame,
) -> None:
    """`@dp.expect("final_score_not_null", ...)`が実際に効いているかを
    テーブルレベルでも簡易的に確認する。expectations自体の詳細な検証は
    `test_pipeline_expectations.py`側で行う。
    """
    # Act
    null_count = game_summary_df.filter(F.col("final_score_cp").isNull()).count()

    # Assert
    assert null_count == 0


def test_game_summaryテーブルのscore_series_jsonはmove_number昇順でソートされている(
    game_summary_df: DataFrame,
) -> None:
    # Arrange
    rows = game_summary_df.select("score_series_json").collect()

    # Act
    sorted_flags = [
        [entry["move_number"] for entry in json.loads(row["score_series_json"])]
        == sorted(entry["move_number"] for entry in json.loads(row["score_series_json"]))
        for row in rows
    ]

    # Assert
    assert all(sorted_flags)
