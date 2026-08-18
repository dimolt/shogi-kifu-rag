"""Layer 3 (E2E) テスト: shogi_kif_jobの実行完了・データ品質を検証する。

前提:
    CDワークフロー（`deploy-dev` ジョブ）により
    `databricks bundle deploy -t dev` が実行済みであること。

フロー:
    1. Bronze/Silver/Goldスキーマをdrop & recreate（conftest.pyのclean_tablesで実施）
    2. shogi_kif_job起動 -> SUCCESS待機
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

# shogi_kif_pipelineのexpectations（positions, position_features, game_summary）
SHOGI_KIF_EXPECTATIONS = {
    **SILVER_EXPECTATIONS,
    **{
        k: v for k, v in GOLD_EXPECTATIONS.items()
        if k in {"position_features", "game_summary"}
    }
}

pytestmark = pytest.mark.e2e


class TestE2EShogiKifJob:
    """shogi_kif_jobの実行完了・データ品質を検証する。"""

    def test_shogi_kif_job実行後_SUCCESSになる(
        self, shogi_kif_job_run_result: JobRunResult
    ) -> None:
        assert shogi_kif_job_run_result.result_state == "SUCCESS"

    def test_assert_expectations_pass_パイプライン実行後_全expectationsのfailed_recordsが0(
        self, spark: SparkSession, shogi_kif_pipeline_id: str
    ) -> None:
        assert_expectations_pass(spark, shogi_kif_pipeline_id, SHOGI_KIF_EXPECTATIONS)

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
