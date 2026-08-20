"""Bronzeテーブルの統合テスト。

wikipedia_raw, floodgate_rawのスキーマ検証とデータ品質検証を行う。

前提:
    本テストの実行前に、対象パイプラインがdevターゲットへデプロイ・実行され、
    Bronzeテーブルが実データで実体化されていること。
"""

import pytest
from pyspark.sql import DataFrame
from pyspark.sql import functions as F  # noqa: N812

pytestmark = pytest.mark.integration

_EXPECTED_WIKIPEDIA_RAW_COLUMNS = {
    "strategy", "raw_content", "fetched_at", "source",
}

_EXPECTED_FLOODGATE_RAW_COLUMNS = {
    "game_id", "csa", "fetched_at", "source",
}


# --- wikipedia_raw -----------------------------------------------------------


def test_wikipedia_rawテーブルのスキーマが仕様通りの列集合と一致する(
    wikipedia_raw_df: DataFrame, normal_test_data
) -> None:
    """スキーマ整合性を検証する。"""
    actual_columns = set(wikipedia_raw_df.columns)
    assert actual_columns == _EXPECTED_WIKIPEDIA_RAW_COLUMNS


def test_wikipedia_rawテーブルにデータが存在する(wikipedia_raw_df: DataFrame, normal_test_data) -> None:
    """データ存在確認。"""
    assert wikipedia_raw_df.count() > 0


def test_wikipedia_rawテーブルのデータ品質(wikipedia_raw_df: DataFrame, normal_test_data) -> None:
    """Bronzeテーブルwikipedia_rawのデータ品質を検証する。

    検証項目:
        - strategyにNULLが存在しない
        - raw_contentにNULLが存在しない
        - fetched_atにNULLが存在しない
        - sourceにNULLが存在しない
        - raw_contentが空文字でない
    """
    # strategy NULLチェック
    null_strategy_count = wikipedia_raw_df.filter(F.col("strategy").isNull()).count()
    assert null_strategy_count == 0, f"strategyにNULLが存在する: {null_strategy_count}件"

    # raw_content NULLチェック
    null_raw_content_count = wikipedia_raw_df.filter(F.col("raw_content").isNull()).count()
    assert null_raw_content_count == 0, f"raw_contentにNULLが存在する: {null_raw_content_count}件"

    # raw_content空文字チェック
    empty_raw_content_count = wikipedia_raw_df.filter(F.col("raw_content") == "").count()
    assert empty_raw_content_count == 0, f"raw_contentに空文字が存在する: {empty_raw_content_count}件"

    # fetched_at NULLチェック
    null_fetched_at_count = wikipedia_raw_df.filter(F.col("fetched_at").isNull()).count()
    assert null_fetched_at_count == 0, f"fetched_atにNULLが存在する: {null_fetched_at_count}件"

    # source NULLチェック
    null_source_count = wikipedia_raw_df.filter(F.col("source").isNull()).count()
    assert null_source_count == 0, f"sourceにNULLが存在する: {null_source_count}件"


# --- floodgate_raw ------------------------------------------------------------


def test_floodgate_rawテーブルのスキーマが仕様通りの列集合と一致する(
    floodgate_raw_df: DataFrame, normal_test_data
) -> None:
    """スキーマ整合性を検証する。"""
    actual_columns = set(floodgate_raw_df.columns)
    assert actual_columns == _EXPECTED_FLOODGATE_RAW_COLUMNS


def test_floodgate_rawテーブルにデータが存在する(floodgate_raw_df: DataFrame, normal_test_data) -> None:
    """データ存在確認。"""
    assert floodgate_raw_df.count() > 0


def test_floodgate_rawテーブルのデータ品質(floodgate_raw_df: DataFrame, normal_test_data) -> None:
    """Bronzeテーブルfloodgate_rawのデータ品質を検証する。

    検証項目:
        - game_idにNULLが存在しない
        - csaにNULLが存在しない
        - fetched_atにNULLが存在しない
        - sourceにNULLが存在しない
        - csaが空文字でない
    """
    # game_id NULLチェック
    null_game_id_count = floodgate_raw_df.filter(F.col("game_id").isNull()).count()
    assert null_game_id_count == 0, f"game_idにNULLが存在する: {null_game_id_count}件"

    # csa NULLチェック
    null_csa_count = floodgate_raw_df.filter(F.col("csa").isNull()).count()
    assert null_csa_count == 0, f"csaにNULLが存在する: {null_csa_count}件"

    # csa空文字チェック
    empty_csa_count = floodgate_raw_df.filter(F.col("csa") == "").count()
    assert empty_csa_count == 0, f"csaに空文字が存在する: {empty_csa_count}件"

    # fetched_at NULLチェック
    null_fetched_at_count = floodgate_raw_df.filter(F.col("fetched_at").isNull()).count()
    assert null_fetched_at_count == 0, f"fetched_atにNULLが存在する: {null_fetched_at_count}件"

    # source NULLチェック
    null_source_count = floodgate_raw_df.filter(F.col("source").isNull()).count()
    assert null_source_count == 0, f"sourceにNULLが存在する: {null_source_count}件"
