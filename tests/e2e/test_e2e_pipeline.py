"""Layer 3 (E2E) テスト: DABs devターゲットへの実デプロイ後の動作確認。

前提:
    CDワークフロー（`deploy-dev` ジョブ）により
    `databricks bundle deploy -t dev` が実行済みであること。

フロー:
    1. Silver/Goldスキーマをdrop & recreate（conftest.pyのclean_schemasで実施）
    2. shogi_kif_rag_main_job起動 -> SUCCESS待機
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

pytestmark = pytest.mark.e2e


class TestE2EPipeline:
    """shogi_kif_rag_main_jobの実行完了・データ品質を検証する。"""

    def test_main_job実行後_SUCCESSになる(
        self, main_job_run_result: JobRunResult
    ) -> None:
        assert main_job_run_result.result_state == "SUCCESS"

    def test_assert_expectations_pass_Silver実行後_全expectationsのfailed_recordsが0(
        self, spark: SparkSession, silver_pipeline_id: str
    ) -> None:
        assert_expectations_pass(spark, silver_pipeline_id, SILVER_EXPECTATIONS)

    def test_assert_expectations_pass_Gold実行後_全expectationsのfailed_recordsが0(
        self, spark: SparkSession, gold_pipeline_id: str
    ) -> None:
        assert_expectations_pass(spark, gold_pipeline_id, GOLD_EXPECTATIONS)

    def test_positions_テーブル_パイプライン完了後_存在してデータがある(
        self,
        positions_df: DataFrame
    ) -> None:
        count = positions_df.count()
        assert count > 0

    def test_position_features_テーブル_パイプライン完了後_存在してデータがある(
        self,
        position_features_df: DataFrame,
    ) -> None:
        count = position_features_df.count()
        assert count > 0

    def test_game_summary_テーブル_パイプライン完了後_存在してデータがある(
        self,
        game_summary_df: DataFrame
    ) -> None:
        count = game_summary_df.count()
        assert count > 0
