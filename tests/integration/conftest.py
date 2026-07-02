"""pytest共通フィクスチャ定義。

Databricks Connect経由のSpark統合テスト用フィクスチャを提供する。
unitテストからは参照しないこと（Databricksへの接続が発生するため）。
"""

import pytest
from databricks.connect import DatabricksSession
from pyspark.sql import SparkSession

_TEST_CATALOG = "test_catalog"
_TEST_SCHEMA = "test_schema"


@pytest.fixture(scope="session")
def spark() -> SparkSession:
    """Databricks Connect経由のSparkSessionを提供する。

    `.databrickscfg` の DEFAULT プロファイルに設定されたServerless computeへ接続する。
    integration/e2eマーカー付きテストからのみ利用すること。

    Returns:
        接続済みのSparkSession。
    """
    return DatabricksSession.builder.profile("shogi").getOrCreate()


@pytest.fixture(scope="session")
def test_catalog_schema(spark: SparkSession) -> str:
    """テスト用カタログ・スキーマを作成し、完全修飾スキーマ名を返す。

    Args:
        spark: Databricks Connect経由のSparkSession。

    Returns:
        "catalog.schema" 形式のスキーマ完全修飾名。
    """
    full_schema_name = f"{_TEST_CATALOG}.{_TEST_SCHEMA}"
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {_TEST_CATALOG}")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {full_schema_name}")
    return full_schema_name
