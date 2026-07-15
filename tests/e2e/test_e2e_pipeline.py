"""Layer 3 (E2E) テスト: DABs devターゲットへの実デプロイ後の動作確認。

前提:
    CDワークフロー（`deploy-dev` ジョブ）により
    `databricks bundle deploy -t dev` が実行済みであること。

フロー:
    1. Silver/Goldスキーマをdrop & recreate（conftest.pyのclean_schemasで実施）
    2. Silverパイプライン起動 -> COMPLETED待機
    3. Goldパイプライン起動（Silver完了後）-> COMPLETED待機
    4. event_log()ベースのexpectations確認
    5. 最終テーブルの存在・データ件数の最小限のスモークチェック
"""

import pytest
from pyspark.sql import SparkSession

from tests.helpers.expectations import (
    GOLD_EXPECTATIONS,
    SILVER_EXPECTATIONS,
    assert_expectations_pass,
)
from tests.helpers.models import UpdateResult

pytestmark = pytest.mark.e2e


class TestE2EPipeline:
    """Silver/Goldパイプラインの実行完了・データ品質を検証する。"""

    def test_start_pipeline_update_Silverパイプライン起動後_COMPLETEDになる(
        self, silver_update_result: UpdateResult
    ) -> None:
        assert silver_update_result.state == "COMPLETED"

    def test_start_pipeline_update_Silver完了後にGoldを起動すると_COMPLETEDになる(
        self, gold_update_result: UpdateResult
    ) -> None:
        assert gold_update_result.state == "COMPLETED"

    def test_assert_expectations_pass_Silver実行後_全expectationsのfailed_recordsが0(
        self, spark: SparkSession, silver_update_result: UpdateResult
    ) -> None:
        assert_expectations_pass(spark, silver_update_result.pipeline_id, SILVER_EXPECTATIONS)

    def test_assert_expectations_pass_Gold実行後_全expectationsのfailed_recordsが0(
        self, spark: SparkSession, gold_update_result: UpdateResult
    ) -> None:
        assert_expectations_pass(spark, gold_update_result.pipeline_id, GOLD_EXPECTATIONS)

    def test_positions_テーブル_パイプライン完了後_存在してデータがある(
        self, spark: SparkSession, silver_update_result: UpdateResult, positions_fqn: str
    ) -> None:
        count = spark.table(positions_fqn).count()
        assert count > 0

    def test_position_features_テーブル_パイプライン完了後_存在してデータがある(
        self,
        spark: SparkSession,
        gold_update_result: UpdateResult,
        position_features_fqn: str,
    ) -> None:
        count = spark.table(position_features_fqn).count()
        assert count > 0

    def test_game_summary_テーブル_パイプライン完了後_存在してデータがある(
        self, spark: SparkSession, gold_update_result: UpdateResult, game_summary_fqn: str
    ) -> None:
        count = spark.table(game_summary_fqn).count()
        assert count > 0
