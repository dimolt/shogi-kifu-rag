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

from tests.helpers.monitoring.expectations import GOLD_EXPECTATIONS, SILVER_EXPECTATIONS

pytestmark = pytest.mark.integration

FRESHNESS_THRESHOLD_HOURS = 24


def _get_latest_expectations_df(spark, pipeline_id: str):
    """最新update_idのexpectationsメトリクスを取得する。

    Args:
        spark: SparkSession（Databricks Connect経由）。
        pipeline_id: 対象パイプラインのID。

    Returns:
        DataFrame: dataset, name, passed_records, failed_records, timestamp列を持つDataFrame。
    """
    return spark.sql(f"""
        WITH latest_update AS (
            SELECT origin.update_id AS update_id
            FROM event_log('{pipeline_id}')
            WHERE event_type = 'update_progress'
              AND details:update_progress.state = 'COMPLETED'
            ORDER BY timestamp DESC
            LIMIT 1
        )
        SELECT
            exp.dataset,
            exp.name,
            exp.passed_records,
            exp.failed_records,
            e.timestamp
        FROM event_log('{pipeline_id}') e
        JOIN latest_update lu ON e.origin.update_id = lu.update_id
        LATERAL VIEW explode(
            from_json(
                e.details:flow_progress.data_quality.expectations,
                'array<struct<name:string,dataset:string,passed_records:long,failed_records:long>>'
            )
        ) t AS exp
        WHERE e.event_type = 'flow_progress'
    """)


def _assert_latest_run_is_recent(df) -> None:
    """event_logの最新実行が鮮度閾値内かを確認し、古い場合はskipする。

    Args:
        df: _get_latest_expectations_df()で取得したDataFrame。
    """
    if df.count() == 0:
        pytest.skip("event_logにflow_progressイベントが存在しない。事前にパイプラインを実行してください。")

    latest_ts = df.agg({"timestamp": "max"}).collect()[0][0]
    # Databricks Connect経由で取得したtimestamp列はtz-naiveなdatetimeとして
    # 返ってくる場合があるため、UTCとして明示的にtz付与してから比較する。
    if latest_ts.tzinfo is None:
        latest_ts = latest_ts.replace(tzinfo=dt.timezone.utc)
    age = dt.datetime.now(dt.timezone.utc) - latest_ts
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
    df = _get_latest_expectations_df(spark, pipeline_id)
    _assert_latest_run_is_recent(df)

    # event_log()のdatasetは`catalog.schema.table`形式のFQNで返るため、
    # catalog/schemaに依存せずテーブル名部分だけで照合する。
    results = {(r.dataset.split(".")[-1], r.name): r for r in df.collect()}

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


def test_silver_pipelineの全expectationがfailed_records_0_品質ゲートが機能している(
    spark, silver_pipeline_id
):
    """silver_pipeline（positionsテーブル）の3件のexpectationsを確認する。

    Arrange:
        silver_pipeline_id fixtureで対象パイプラインのIDを取得する
        （パイプライン自体は事前実行済みである前提、モジュールdocstring参照）。
    Act:
        event_log()から最新update_idのexpectationsメトリクスを取得する。
    Assert:
        SILVER_EXPECTATIONS全件が存在し、failed_records=0かつpassed_records>0であること。
    """
    _assert_expectations_pass(spark, silver_pipeline_id, SILVER_EXPECTATIONS)


def test_gold_pipelineの全expectationがfailed_records_0_品質ゲートが機能している(
    spark, gold_pipeline_id
):
    """gold_pipeline（position_features/game_summaryテーブル）の3件のexpectationsを確認する。

    Arrange:
        gold_pipeline_id fixtureで対象パイプラインのIDを取得する
        （パイプライン自体は事前実行済みである前提、モジュールdocstring参照）。
    Act:
        event_log()から最新update_idのexpectationsメトリクスを取得する。
    Assert:
        GOLD_EXPECTATIONS全件が存在し、failed_records=0かつpassed_records>0であること。
    """
    _assert_expectations_pass(spark, gold_pipeline_id, GOLD_EXPECTATIONS)
