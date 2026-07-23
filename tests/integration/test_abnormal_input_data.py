"""InputData系異常系テスト（Issue #200, #202）。

前提条件:
    - このテストは対象パイプラインを実際に起動する。
    - パイプライン実行には数分かかるため、実行時間に注意すること。
    - テスト実行前にlanding volumeに不正CSVを配置し、パイプライン実行後に
      event_log()経由でexpectation発火を確認する。
"""
from pathlib import Path

import pytest
from pyspark.sql import SparkSession

from tests.helpers.csv_helpers import CSV_HEADER
from tests.helpers.databricks.volume_helpers import (
    get_landing_volume_path,
    upload_csv_to_volume,
)
from tests.helpers.monitoring.expectations import _get_latest_expectations_df
from tests.helpers.monitoring.pipeline_helpers import (
    start_pipeline_update,
    wait_for_update,
)

pytestmark = pytest.mark.integration




def _assert_expectation_failed(
    spark: SparkSession, pipeline_id: str, table: str, expectation: str
) -> None:
    """指定expectationがfailed_records > 0で発火したことを確認する。

    Args:
        spark: SparkSession。
        pipeline_id: 対象パイプラインのID。
        table: テーブル名。
        expectation: expectation名。

    Raises:
        AssertionError: expectationが発火していない、またはfailed_recordsが0の場合。
    """
    df = _get_latest_expectations_df(spark, pipeline_id)
    results = {(r.dataset, r.name): r for r in df.collect()}
    key = (table, expectation)
    assert key in results, f"expectation未発火: {table}.{expectation}"
    assert results[key].failed_records > 0, (
        f"{table}.{expectation} でfailed_records=0（期待: >0）"
    )


def test_missing_game_id_column_expectation_fires(spark, silver_pipeline_id, catalog):
    """Issue #200: game_id列を欠いたCSVでvalid_game_id expectationが発火すること。

    Arrange:
        game_id列を欠いた不正CSVを作成し、landing volumeに配置する。
    Act:
        Silver pipelineを実行し、完了まで待機する。
    Assert:
        valid_game_id expectationがfailed_records > 0で発火していること。
    """
    import tempfile

    # Arrange: game_id列を欠いた不正CSVを作成
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "missing_game_id.csv"
        invalid_header = (
            "move_number,sfen,prev_sfen,move_usi,player,black_player,"
            "white_player,best_move,score_cp,pv\n"
        )
        csv_path.write_text(
            invalid_header
            + "1,lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1,,black,player1,player2,7g7f,100,7g7f*",
            encoding="utf-8",
        )

        # Volumeにアップロード
        volume_path = get_landing_volume_path(catalog)
        upload_csv_to_volume(csv_path, volume_path, "missing_game_id.csv")

        # Act: Silver pipeline実行
        update_id = start_pipeline_update(silver_pipeline_id)
        wait_for_update(spark, silver_pipeline_id, update_id)

        # Assert: valid_game_id expectationがfailed_records > 0で発火
        _assert_expectation_failed(spark, silver_pipeline_id, "positions", "valid_game_id")


def test_invalid_move_number_data_type_expectation_fires(spark, silver_pipeline_id, catalog):
    """Issue #202: move_numberに文字列を混入させたCSVでvalid_move_number expectationが発火すること。

    Arrange:
        move_numberに文字列を混入させた不正CSVを作成し、landing volumeに配置する。
    Act:
        Silver pipelineを実行し、完了まで待機する。
    Assert:
        valid_move_number expectationがfailed_records > 0で発火していること。
    """
    import tempfile

    # Arrange: move_numberに文字列を混入させた不正CSVを作成
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "invalid_move_number.csv"
        csv_path.write_text(
            CSV_HEADER
            + "invalid,lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1,,black,player1,player2,7g7f,100,7g7f*",
            encoding="utf-8",
        )

        # Volumeにアップロード
        volume_path = get_landing_volume_path(catalog)
        upload_csv_to_volume(csv_path, volume_path, "invalid_move_number.csv")

        # Act: Silver pipeline実行
        update_id = start_pipeline_update(silver_pipeline_id)
        wait_for_update(spark, silver_pipeline_id, update_id)

        # Assert: valid_move_number expectationがfailed_records > 0で発火
        _assert_expectation_failed(spark, silver_pipeline_id, "positions", "valid_move_number")
