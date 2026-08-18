"""Layer 3 (E2E) テスト: floodgate_jobの実行完了・データ品質を検証する。

前提:
    CDワークフロー（`deploy-dev` ジョブ）により
    `databricks bundle deploy -t dev` が実行済みであること。

フロー:
    1. Bronze/Silver/Goldスキーマをdrop & recreate（conftest.pyのclean_tablesで実施）
    2. floodgate_job起動 -> SUCCESS待機
    3. event_log()ベースのexpectations確認
    4. 最終テーブルの存在・データ件数の最小限のスモークチェック
"""

import pytest
from pyspark.sql import DataFrame, SparkSession

from tests.helpers.models import JobRunResult
from tests.helpers.monitoring.expectations import (
    GOLD_EXPECTATIONS,
    SILVER_EXPECTATIONS,
    assert_expectations_pass,
)

# floodgate_pipelineのexpectations（floodgate_positions, floodgate_position_features）
FLOODGATE_EXPECTATIONS = {
    **{
        k: v for k, v in SILVER_EXPECTATIONS.items()
        if k in {"floodgate_positions"}
    },
    **{
        k: v for k, v in GOLD_EXPECTATIONS.items()
        if k in {"floodgate_position_features"}
    }
}

pytestmark = pytest.mark.e2e


class TestE2EFloodgateJob:
    """floodgate_jobの実行完了・データ品質を検証する。"""

    def test_floodgate_job実行後_SUCCESSになる(
        self, floodgate_job_run_result: JobRunResult
    ) -> None:
        assert floodgate_job_run_result.result_state == "SUCCESS"

    def test_assert_expectations_pass_パイプライン実行後_全expectationsのfailed_recordsが0(
        self, spark: SparkSession, floodgate_pipeline_id: str
    ) -> None:
        assert_expectations_pass(spark, floodgate_pipeline_id, FLOODGATE_EXPECTATIONS)

    def test_floodgate_positions_テーブル_パイプライン完了後_存在してデータがある(
        self,
        floodgate_positions_df: DataFrame
    ) -> None:
        count = floodgate_positions_df.count()
        assert count > 0

    def test_floodgate_position_features_テーブル_パイプライン完了後_存在してデータがある(
        self,
        floodgate_position_features_df: DataFrame
    ) -> None:
        count = floodgate_position_features_df.count()
        assert count > 0
