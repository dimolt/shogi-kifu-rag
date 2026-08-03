"""Layer 3 (E2E) テスト用フィクスチャ。

DABs devターゲットへの実デプロイ（CD workflowで実施済み）を前提に、
Silver/GoldスキーマのクリーンアップとJob起動・完了待機を行う。

spark, shogi_kif_pipeline_id, main_job_id は `tests/conftest.py`（ルート）で
定義されたものをそのまま利用する（本ファイルでの再定義は不要）。
"""


import os

import pytest
from databricks.sdk import WorkspaceClient
from pyspark.sql import SparkSession

from tests.helpers.config.constants import (
    TEST_GOLD_SCHEMA,
    TEST_SILVER_SCHEMA,
)
from tests.helpers.models import JobRunResult
from tests.helpers.monitoring.job_monitoring import JobMonitor, start_job_run
from tests.helpers.operations.schema_helpers import drop_tables_in_schema

# e2e層向けに環境変数を設定
os.environ["DATABRICKS_BUNDLE_TARGET"] = "test"
os.environ["TEST_CATALOG"] = "shogi_test"


@pytest.fixture(scope="session", autouse=True)
def clean_tables(spark: SparkSession, catalog: str) -> None:
    """E2Eテスト実行前にSilver/Goldスキーマ内のテーブル・MVを削除する。

    スキーマは事前に作成済みとし、テーブル・MVのみを削除してクリーンな状態にする。
    Lakeflowパイプライン実行時にテーブル・MVは自動作成される。
    """
    drop_tables_in_schema(spark, catalog, TEST_SILVER_SCHEMA)
    drop_tables_in_schema(spark, catalog, TEST_GOLD_SCHEMA)


@pytest.fixture(scope="session")
def main_job_run_result(
    clean_tables: None,
    main_job_id: str,
    databricks_profile: str | None,
) -> JobRunResult:
    """shogi_kif_rag_main_jobを起動し、SUCCESSになるまで待機した結果を提供する。

    Args:
        clean_tables: テーブル・MVクリーンアップ（自動実行）。
        main_job_id: 対象JobのID。
        databricks_profile: Databricks CLIのプロファイル名。

    Returns:
        JobRunResult: Job実行の完了結果。
    """
    # Job実行を起動
    run_id = start_job_run(main_job_id)

    # WorkspaceClientを初期化してJobMonitorを作成
    client = WorkspaceClient(profile=databricks_profile) if databricks_profile else WorkspaceClient()
    monitor = JobMonitor(client)

    # Job実行完了を待機
    return monitor.wait_for_completion(run_id)
