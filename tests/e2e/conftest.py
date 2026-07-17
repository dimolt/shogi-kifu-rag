"""Layer 3 (E2E) テスト用フィクスチャ。

DABs devターゲットへの実デプロイ（CD workflowで実施済み）を前提に、
Silver/GoldスキーマのクリーンアップとJob起動・完了待機を行う。

spark, silver_pipeline_id, gold_pipeline_id, main_job_id は `tests/conftest.py`（ルート）で
定義されたものをそのまま利用する（本ファイルでの再定義は不要）。
"""


import os

import pytest
from databricks.sdk import WorkspaceClient

from tests.helpers.config.constants import (
    TEST_CATALOG,
    TEST_GOLD_SCHEMA,
    TEST_SILVER_SCHEMA,
)
from tests.helpers.databricks.spark_fixture import spark  # noqa: F401
from tests.helpers.models import JobRunResult
from tests.helpers.monitoring.job_monitoring import JobMonitor, start_job_run
from tests.helpers.operations.schema_helpers import drop_recreate_schema

# e2e層は常にshogi_testを使用
os.environ["TEST_CATALOG"] = "shogi_test"


@pytest.fixture(scope="session", autouse=True)
def clean_schemas() -> None:
    """E2Eテスト実行前にSilver/Goldスキーマをdrop & recreateする。

    テーブル・MVはLakeflowパイプライン実行時に自動作成されるため、
    ここではスキーマの器のみをクリーンな状態にする。
    """
    drop_recreate_schema(TEST_CATALOG, TEST_SILVER_SCHEMA)
    drop_recreate_schema(TEST_CATALOG, TEST_GOLD_SCHEMA)


@pytest.fixture(scope="session")
def main_job_run_result(
    clean_schemas: None,
    main_job_id: str,
    databricks_profile: str | None,
) -> JobRunResult:
    """shogi_kif_rag_main_jobを起動し、SUCCESSになるまで待機した結果を提供する。

    Args:
        clean_schemas: スキーマクリーンアップ（自動実行）。
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
