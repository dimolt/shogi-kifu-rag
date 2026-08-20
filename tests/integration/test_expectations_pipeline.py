"""event_log()によるexpectations発火確認テスト。

前提条件:
    - このテストは対象パイプラインを起動しない。
      検証対象のevent_logは、以下いずれかの方法で事前に生成されている必要がある：
        1. CIの定期実行（post-merge scheduled run）
        2. 手動での `databricks bundle run <pipeline_name>` 実行
    - event_logのデータ鮮度は _assert_latest_run_is_recent() でチェックし、
      直近24時間以内の実行がなければテストをskipする（古いログへの誤検証を防ぐため）。
    - パイプラインの起動〜完了を含めた検証（真のE2E）はLayer 3（tests/e2e/）の責務とする。
"""

import datetime as dt

import pytest

from tests.helpers.monitoring.expectations import (
  GOLD_EXPECTATIONS,
  SILVER_EXPECTATIONS,
  get_latest_expectations_df,
)

# Unified expectations for the single shogi_kif_pipeline
UNIFIED_EXPECTATIONS = {**SILVER_EXPECTATIONS, **GOLD_EXPECTATIONS}

pytestmark = pytest.mark.integration

FRESHNESS_THRESHOLD_HOURS = 24


def _assert_latest_run_is_recent(rows: list) -> None:
    """event_logの最新実行が鮮度閾値内かを確認し、古い場合はskipする。

    Args:
        rows: get_latest_expectations_df()をcollect()した行リスト。
            呼び出し元で1度だけcollect()した結果を渡すことで、
            event_log()の再スキャンを避ける。
    """
    if not rows:
        pytest.skip("event_logにflow_progressイベントが存在しない。事前にパイプラインを実行してください。")

    latest_ts = max(row["timestamp"] for row in rows)
    # Databricks Connect経由で取得したtimestamp列はtz-naiveなdatetimeとして
    # 返ってくる場合があるため、UTCとして明示的にtz付与してから比較する。
    if latest_ts.tzinfo is None:
        latest_ts = latest_ts.replace(tzinfo=dt.UTC)
    age = dt.datetime.now(dt.UTC) - latest_ts
    if age > dt.timedelta(hours=FRESHNESS_THRESHOLD_HOURS):
        pytest.skip(
            f"最新のパイプライン実行が{FRESHNESS_THRESHOLD_HOURS}時間以上前"
            f"（{age}経過）。最新化してから再実行してください。"
        )


def _assert_expectations_pass(
    spark, pipeline_id: str, expected_expectations: dict[str, set[str]]
) -> None:
    """指定パイプラインのexpectationsが全て発火し、failed_records=0であることを確認する。

    Args:
        spark: SparkSession（Databricks Connect経由）。
        pipeline_id: 検証対象パイプラインのID。
        expected_expectations: テーブル名をキー、expectation名のセットを値とする辞書。
            `tests.helpers.expectations` の `SILVER_EXPECTATIONS` または
            `GOLD_EXPECTATIONS` を渡す想定。
    """
    df = get_latest_expectations_df(spark, pipeline_id)
    # collect()を1回だけ実行し、以降はPython側のリストで件数・最大timestamp・
    # 照合を行う。df.count() / df.agg(max).collect() / df.collect() を個別に
    # 呼ぶとevent_log()のスキャン・JOIN・explode・ウィンドウ処理が
    # それぞれ再実行され非効率なため。
    rows = df.collect()

    _assert_latest_run_is_recent(rows)

    results = {(r.dataset, r.name): r for r in rows}

    for table, expectation_names in expected_expectations.items():
        for expectation in expectation_names:
            key = (table, expectation)
            assert key in results, f"expectation未発火: {table}.{expectation}"
            assert results[key].failed_records == 0, (
                f"{table}.{expectation} でfailed_records>0: {results[key].failed_records}件"
            )
            assert results[key].passed_records > 0, (
                f"{table}.{expectation} でpassed_records=0（データ未投入の疑い）"
            )


def test_shogi_kif_pipelineの全expectationがfailed_records_0_品質ゲートが機能している(
    spark, shogi_kif_pipeline_id
):
    """shogi_kif_pipeline（positions/position_features/game_summaryテーブル）のexpectationsを確認する。

    Arrange:
        shogi_kif_pipeline_id fixtureで対象パイプラインのIDを取得する
        （パイプライン自体は事前実行済みである前提、モジュールdocstring参照）。
    Act:
        event_log()から最新update_idのexpectationsメトリクスを取得する。
    Assert:
        UNIFIED_EXPECTATIONS全件が存在し、failed_records=0かつpassed_records>0であること。
    """
    shogi_kif_expectations = {
        "positions": SILVER_EXPECTATIONS["positions"],
        "position_features": GOLD_EXPECTATIONS["position_features"],
        "game_summary": GOLD_EXPECTATIONS["game_summary"],
    }
    _assert_expectations_pass(spark, shogi_kif_pipeline_id, shogi_kif_expectations)


def test_floodgate_pipelineの全expectationがfailed_records_0_品質ゲートが機能している(
    spark, floodgate_pipeline_id
):
    """floodgate_pipeline（floodgate_positions/floodgate_position_featuresテーブル）のexpectationsを確認する。

    Arrange:
        floodgate_pipeline_id fixtureで対象パイプラインのIDを取得する
        （パイプライン自体は事前実行済みである前提、モジュールdocstring参照）。
    Act:
        event_log()から最新update_idのexpectationsメトリクスを取得する。
    Assert:
        floodgate_positions/floodgate_position_featuresのexpectations全件が存在し、
        failed_records=0かつpassed_records>0であること。
    """
    floodgate_expectations = {
        "floodgate_positions": SILVER_EXPECTATIONS["floodgate_positions"],
        "floodgate_position_features": GOLD_EXPECTATIONS["floodgate_position_features"],
    }
    _assert_expectations_pass(spark, floodgate_pipeline_id, floodgate_expectations)


def test_joseki_pipelineの全expectationがfailed_records_0_品質ゲートが機能している(
    spark, joseki_pipeline_id
):
    """joseki_pipeline（joseki_knowledge/joseki_featuresテーブル）のexpectationsを確認する。

    Arrange:
        joseki_pipeline_id fixtureで対象パイプラインのIDを取得する
        （パイプライン自体は事前実行済みである前提、モジュールdocstring参照）。
    Act:
        event_log()から最新update_idのexpectationsメトリクスを取得する。
    Assert:
        joseki_knowledge/joseki_featuresのexpectations全件が存在し、
        failed_records=0かつpassed_records>0であること。
    """
    joseki_expectations = {
        "joseki_knowledge": SILVER_EXPECTATIONS["joseki_knowledge"],
        "joseki_features": GOLD_EXPECTATIONS["joseki_features"],
    }
    _assert_expectations_pass(spark, joseki_pipeline_id, joseki_expectations)
