"""Goldテーブルの統合テスト。

ビジネスルール検証とデータ品質検証を統合したGoldテーブル用テストファイル。
テーブルが増えた段階でファイル分割を検討する。

前提:
    本テストの実行前に、対象パイプラインがdevターゲットへデプロイ・実行され、
    Goldテーブルが実データで実体化されていること。
"""

import json

import pytest
from pyspark.sql import DataFrame
from pyspark.sql import functions as F  # noqa: N812

pytestmark = pytest.mark.integration

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


#TODO: fooldgate, wikipediaテーブルの検証も追加したい

# --- position_features -------------------------------------------------------


def test_position_featuresテーブルのスキーマが仕様通りの列集合と一致する(
    position_features_df: DataFrame,
) -> None:
    """スキーマ整合性を検証する。"""
    actual_columns = set(position_features_df.columns)
    assert actual_columns == _EXPECTED_POSITION_FEATURES_COLUMNS


def test_position_featuresテーブルにデータが存在する(position_features_df: DataFrame) -> None:
    """データ存在確認。"""
    assert position_features_df.count() > 0


def test_position_featuresテーブルの行数がpositionsテーブルと一致する(
    position_features_df: DataFrame, positions_df: DataFrame
) -> None:
    """position_featuresはpositionsの全行に特徴量列を付与したものであるため、
    行数が完全に一致するはずである。
    """
    positions_count = positions_df.count()
    position_features_count = position_features_df.count()
    assert position_features_count == positions_count


# --- game_summary --------------------------------------------------------------


def test_game_summaryテーブルのスキーマが仕様通りの列集合と一致する(
    game_summary_df: DataFrame,
) -> None:
    """スキーマ整合性を検証する。"""
    actual_columns = set(game_summary_df.columns)
    assert actual_columns == _EXPECTED_GAME_SUMMARY_COLUMNS


def test_game_summaryテーブルにデータが存在する(game_summary_df: DataFrame) -> None:
    """データ存在確認。"""
    assert game_summary_df.count() > 0


def test_game_summaryテーブルはgame_idごとに1行のみ存在する(
    game_summary_df: DataFrame,
) -> None:
    """game_idごとの一意性を検証する。"""
    total_count = game_summary_df.count()
    distinct_game_id_count = game_summary_df.select("game_id").distinct().count()
    assert total_count == distinct_game_id_count


def test_game_summaryテーブルのscore_series_jsonはmove_number昇順でソートされている(
    game_summary_df: DataFrame,
) -> None:
    """score_series_json内のmove_numberが昇順でソートされていることを検証する。"""
    rows = game_summary_df.select("score_series_json").collect()
    sorted_flags = [
        [entry["move_number"] for entry in json.loads(row["score_series_json"])]
        == sorted(entry["move_number"] for entry in json.loads(row["score_series_json"]))
        for row in rows
    ]
    assert all(sorted_flags)


# --- データ品質検証 ---------------------------------------------------------


def test_position_featuresテーブルのデータ品質(position_features_df: DataFrame) -> None:
    """Goldテーブルposition_featuresのデータ品質を検証する。

    検証項目:
        - game_idにNULLが存在しない
        - move_numberにNULLが存在しない
        - move_qualityが許容セット内にある
        - score_from_turnにNULLが存在しない
        - is_best_moveにNULLが存在しない
        - search_textにNULLが存在しない
        - move_number=0の行でmove_qualityが'start'である
    """
    # game_id NULLチェック
    null_game_id_count = position_features_df.filter(F.col("game_id").isNull()).count()
    assert null_game_id_count == 0, f"game_idにNULLが存在する: {null_game_id_count}件"

    # move_number NULLチェック
    null_move_number_count = position_features_df.filter(F.col("move_number").isNull()).count()
    assert null_move_number_count == 0, f"move_numberにNULLが存在する: {null_move_number_count}件"

    # move_quality値チェック
    invalid_quality_count = position_features_df.filter(
        ~F.col("move_quality").isin(_ALLOWED_MOVE_QUALITIES)
    ).count()
    assert invalid_quality_count == 0, (
        f"move_qualityが許容セット外の値: {invalid_quality_count}件"
    )

    # score_from_turn NULLチェック
    null_score_from_turn_count = position_features_df.filter(
        F.col("score_from_turn").isNull()
    ).count()
    assert null_score_from_turn_count == 0, (
        f"score_from_turnにNULLが存在する: {null_score_from_turn_count}件"
    )

    # is_best_move NULLチェック
    null_is_best_move_count = position_features_df.filter(
        F.col("is_best_move").isNull() &
        (F.col("move_number") != 0) # 初手以外
    ).count()
    assert null_is_best_move_count == 0, (
        f"is_best_moveにNULLが存在する: {null_is_best_move_count}件"
    )

    # search_text NULLチェック
    null_search_text_count = position_features_df.filter(
        F.col("search_text").isNull() &
        (F.col("move_number") != 0) # 初手以外
    ).count()
    assert null_search_text_count == 0, (
        f"search_textにNULLが存在する: {null_search_text_count}件"
    )

    # move_number=0でmove_quality='start'チェック
    invalid_start_count = position_features_df.filter(
        (F.col("move_number") == 0) & (F.col("move_quality") != "start")
    ).count()
    assert invalid_start_count == 0, (
        f"move_number=0でmove_qualityが'start'でない: {invalid_start_count}件"
    )


def test_game_summaryテーブルのデータ品質(game_summary_df: DataFrame) -> None:
    """Goldテーブルgame_summaryのデータ品質を検証する。

    検証項目:
        - game_idにNULLが存在しない
        - game_idに重複が存在しない
        - black_playerにNULLが存在しない
        - white_playerにNULLが存在しない
        - total_movesにNULLが存在しない
        - total_movesが0以上である
        - final_score_cpにNULLが存在しない
        - black_blundersにNULLが存在しない
        - white_blundersにNULLが存在しない
        - black_blunders/white_blundersが0以上である
        - score_series_jsonが有効なJSON配列である
    """
    # game_id NULLチェック
    null_game_id_count = game_summary_df.filter(F.col("game_id").isNull()).count()
    assert null_game_id_count == 0, f"game_idにNULLが存在する: {null_game_id_count}件"

    # game_id重複チェック
    total_count = game_summary_df.count()
    distinct_game_id_count = game_summary_df.select("game_id").distinct().count()
    assert total_count == distinct_game_id_count, (
        f"game_idに重複が存在する: 全{total_count}件 vs ユニーク{distinct_game_id_count}件"
    )

    # black_player NULLチェック
    null_black_player_count = game_summary_df.filter(F.col("black_player").isNull()).count()
    assert null_black_player_count == 0, (
        f"black_playerにNULLが存在する: {null_black_player_count}件"
    )

    # white_player NULLチェック
    null_white_player_count = game_summary_df.filter(F.col("white_player").isNull()).count()
    assert null_white_player_count == 0, (
        f"white_playerにNULLが存在する: {null_white_player_count}件"
    )

    # total_moves NULLチェック
    null_total_moves_count = game_summary_df.filter(F.col("total_moves").isNull()).count()
    assert null_total_moves_count == 0, (
        f"total_movesにNULLが存在する: {null_total_moves_count}件"
    )

    # total_moves範囲チェック（0以上）
    invalid_total_moves_count = game_summary_df.filter(F.col("total_moves") < 0).count()
    assert invalid_total_moves_count == 0, (
        f"total_movesが負の値: {invalid_total_moves_count}件"
    )

    # final_score_cp NULLチェック
    null_final_score_count = game_summary_df.filter(F.col("final_score_cp").isNull()).count()
    assert null_final_score_count == 0, (
        f"final_score_cpにNULLが存在する: {null_final_score_count}件"
    )

    # black_blunders NULLチェック
    null_black_blunders_count = game_summary_df.filter(
        F.col("black_blunders").isNull()
    ).count()
    assert null_black_blunders_count == 0, (
        f"black_blundersにNULLが存在する: {null_black_blunders_count}件"
    )

    # white_blunders NULLチェック
    null_white_blunders_count = game_summary_df.filter(
        F.col("white_blunders").isNull()
    ).count()
    assert null_white_blunders_count == 0, (
        f"white_blundersにNULLが存在する: {null_white_blunders_count}件"
    )

    # black_blunders範囲チェック（0以上）
    invalid_black_blunders_count = game_summary_df.filter(
        F.col("black_blunders") < 0
    ).count()
    assert invalid_black_blunders_count == 0, (
        f"black_blundersが負の値: {invalid_black_blunders_count}件"
    )

    # white_blunders範囲チェック（0以上）
    invalid_white_blunders_count = game_summary_df.filter(
        F.col("white_blunders") < 0
    ).count()
    assert invalid_white_blunders_count == 0, (
        f"white_blundersが負の値: {invalid_white_blunders_count}件"
    )

    # score_series_json JSON妥当性チェック
    rows = game_summary_df.select("score_series_json").collect()
    invalid_json_count = 0
    for row in rows:
        try:
            parsed = json.loads(row["score_series_json"])
            if not isinstance(parsed, list):
                invalid_json_count += 1
        except (json.JSONDecodeError, TypeError):
            invalid_json_count += 1

    assert invalid_json_count == 0, (
        f"score_series_jsonが無効なJSONまたは配列でない: {invalid_json_count}件"
    )
