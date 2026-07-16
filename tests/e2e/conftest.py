"""Layer 3 (E2E) テスト用フィクスチャ。

DABs devターゲットへの実デプロイ（CD workflowで実施済み）を前提に、
Silver/Goldスキーマのクリーンアップとパイプライン起動・完了待機を行う。

spark, silver_pipeline_id, gold_pipeline_id は `tests/conftest.py`（ルート）で
定義されたものをそのまま利用する（本ファイルでの再定義は不要）。
"""


import pytest
from pyspark.sql import SparkSession

from tests.helpers.config.constants import (
    TEST_CATALOG,
    TEST_GOLD_SCHEMA,
    TEST_SILVER_SCHEMA,
)
from tests.helpers.databricks.spark_fixture import spark  # noqa: F401
from tests.helpers.models import UpdateResult
from tests.helpers.monitoring.pipeline_helpers import (
    start_pipeline_update,
    wait_for_update,
)
from tests.helpers.operations.schema_helpers import drop_recreate_schema


@pytest.fixture(scope="session", autouse=True)
def clean_schemas() -> None:
    """E2Eテスト実行前にSilver/Goldスキーマをdrop & recreateする。

    テーブル・MVはLakeflowパイプライン実行時に自動作成されるため、
    ここではスキーマの器のみをクリーンな状態にする。
    """
    drop_recreate_schema(TEST_CATALOG, TEST_SILVER_SCHEMA)
    drop_recreate_schema(TEST_CATALOG, TEST_GOLD_SCHEMA)


@pytest.fixture(scope="session")
def silver_update_result(
    clean_schemas: None,
    spark: SparkSession,    #noqa: F811
    silver_pipeline_id: str
) -> UpdateResult:
    """Silverパイプラインを起動し、COMPLETEDになるまで待機した結果を提供する。"""
    update_id = start_pipeline_update(silver_pipeline_id)
    return wait_for_update(spark, silver_pipeline_id, update_id)


@pytest.fixture(scope="session")
def gold_update_result(
    silver_update_result: UpdateResult,
    spark: SparkSession,    #noqa: F811
    gold_pipeline_id: str
) -> UpdateResult:
    """Silver完了後にGoldパイプラインを起動し、COMPLETEDになるまで待機した結果を提供する。"""
    update_id = start_pipeline_update(gold_pipeline_id)
    return wait_for_update(spark, gold_pipeline_id, update_id)
