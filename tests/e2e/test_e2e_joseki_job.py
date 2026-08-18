"""Layer 3 (E2E) テスト: joseki_jobの実行完了・データ品質を検証する。

前提:
    CDワークフロー（`deploy-dev` ジョブ）により
    `databricks bundle deploy -t dev` が実行済みであること。

フロー:
    1. Bronze/Silver/Goldスキーマをdrop & recreate（conftest.pyのclean_tablesで実施）
    2. joseki_job起動 -> SUCCESS待機
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

# joseki_pipelineのexpectations（joseki_knowledge, joseki_features）
JOSEKI_EXPECTATIONS = {
    **{
        k: v for k, v in SILVER_EXPECTATIONS.items()
        if k in {"joseki_knowledge"}
    },
    **{
        k: v for k, v in GOLD_EXPECTATIONS.items()
        if k in {"joseki_features"}
    }
}

pytestmark = pytest.mark.e2e


class TestE2EJosekiJob:
    """joseki_jobの実行完了・データ品質を検証する。"""

    def test_joseki_job実行後_SUCCESSになる(
        self, joseki_job_run_result: JobRunResult
    ) -> None:
        assert joseki_job_run_result.result_state == "SUCCESS"

    def test_assert_expectations_pass_パイプライン実行後_全expectationsのfailed_recordsが0(
        self, spark: SparkSession, joseki_pipeline_id: str
    ) -> None:
        assert_expectations_pass(spark, joseki_pipeline_id, JOSEKI_EXPECTATIONS)

    def test_joseki_knowledge_テーブル_パイプライン完了後_存在してデータがある(
        self,
        joseki_knowledge_df: DataFrame
    ) -> None:
        count = joseki_knowledge_df.count()
        assert count > 0

    def test_joseki_features_テーブル_パイプライン完了後_存在してデータがある(
        self,
        joseki_features_df: DataFrame
    ) -> None:
        count = joseki_features_df.count()
        assert count > 0
