"""InputData系異常系テスト（Issue #200, #202）。

前提条件:
    - このテストは対象パイプラインを実際に起動する。
    - パイプライン実行には数分かかるため、実行時間に注意すること。
    - テスト実行前にlanding volumeに不正CSVを配置し、パイプライン実行後に
      event_log()経由でexpectation発火を確認する。
"""

import pytest
from pyspark.sql import SparkSession

from tests.helpers.monitoring.expectations import get_latest_expectations_df
from tests.helpers.monitoring.pipeline_helpers import (
    start_pipeline_update,
    wait_for_update,
)

pytestmark = [pytest.mark.integration, pytest.mark.abnormal]


def _assert_expectation_failed(
    spark: SparkSession, pipeline_id: str, update_id: str, table: str, expectation: str
) -> None:
    """指定expectationがfailed_records > 0で発火したことを確認する。

    Args:
        spark: SparkSession。
        pipeline_id: 対象パイプラインのID。
        update_id: 検証対象のupdate ID（呼び出し元が起動・待機済みのもの）。
        table: テーブル名。
        expectation: expectation名。

    Raises:
        AssertionError: expectationが発火していない、またはfailed_recordsが0の場合。
    """
    df = get_latest_expectations_df(spark, pipeline_id, update_id=update_id)
    results = {(r.dataset, r.name): r for r in df.collect()}
    key = (table, expectation)
    assert key in results, f"expectation未発火: {table}.{expectation}"
    assert results[key].failed_records > 0, (
        f"{table}.{expectation} でfailed_records=0（期待: >0）"
    )


def test_missing_game_id_column_expectation_fires(spark, shogi_kif_pipeline_id, catalog, abnormal_test_data, clean_volume):
    """Issue #200: game_id列を欠いたCSVでvalid_game_id expectationが発火すること。

    Arrange:
        clean_volume fixtureにより前回のテストデータがクリアされ、
        abnormal_test_data fixtureにより、game_id列を欠いた不正CSVがlanding volumeに配置される。
    Act:
        shogi_kif_pipelineを実行し、完了まで待機する。
    Assert:
        valid_game_id expectationがfailed_records > 0で発火していること。
    """
    # Act: pipeline実行（正常系・異常系共通）
    update_id = start_pipeline_update(shogi_kif_pipeline_id)
    wait_for_update(spark, shogi_kif_pipeline_id, update_id)

    # Assert: valid_game_id expectationがfailed_records > 0で発火
    _assert_expectation_failed(spark, shogi_kif_pipeline_id, update_id, "positions", "valid_game_id")


def test_invalid_move_number_data_type_expectation_fires(spark, shogi_kif_pipeline_id, catalog, abnormal_test_data, clean_volume):
    """Issue #202: move_numberに文字列を混入させたCSVでvalid_move_number expectationが発火すること。

    Arrange:
        clean_volume fixtureにより前回のテストデータがクリアされ、
        abnormal_test_data fixtureにより、move_numberに文字列を混入させた不正CSVがlanding volumeに配置される。
    Act:
        shogi_kif_pipelineを実行し、完了まで待機する。
    Assert:
        valid_move_number expectationがfailed_records > 0で発火していること。
    """
    # Act: pipeline実行（正常系・異常系共通）
    update_id = start_pipeline_update(shogi_kif_pipeline_id)
    wait_for_update(spark, shogi_kif_pipeline_id, update_id)

    # Assert: valid_move_number expectationがfailed_records > 0で発火
    _assert_expectation_failed(spark, shogi_kif_pipeline_id, update_id, "positions", "valid_move_number")
