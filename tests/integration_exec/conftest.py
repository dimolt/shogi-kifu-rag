"""Layer 2.5 (Integration-Execution) テスト用フィクスチャ。

Job/パイプラインの起動〜完了を検証するテスト用。
spark, workspace_client は tests/conftest.py から継承。
"""
from tests.helpers.databricks.spark_fixture import spark  # noqa: F401

# volume_setupと名前が衝突する可能性があるため、別名でインポート
from tests.integration.fixtures.test_data import (  # noqa: F401
    clean_volume,
)
from tests.integration_exec.fixtures.job_execution import (  # noqa: F401
    floodgate_job_id,
    floodgate_job_run_result,
    job_id,
    job_run_result,
    joseki_job_id,
    joseki_job_run_result,
    workspace_client,
)
