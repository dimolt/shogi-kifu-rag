"""Layer 2.5 (Integration-Execution) テスト用フィクスチャ。

Job/パイプラインの起動〜完了を検証するテスト用。
spark, workspace_client は tests/conftest.py から継承。
"""
from tests.helpers.databricks.spark_fixture import spark  # noqa: F401
from tests.integration_exec.fixtures.job_execution import (  # noqa: F401
    job_id,
    job_run_result,
    workspace_client,
)
