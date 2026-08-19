"""異常系テスト用スキーマのfixture定義。

異常系テストで使用する専用スキーマのsetup/teardownを管理する。
"""
import pytest
from pyspark.sql import SparkSession

from tests.helpers.monitoring.pipeline_helpers import start_pipeline_update_with_params


@pytest.fixture(scope="module")
def abnormal_test_schema(spark: SparkSession, catalog: str) -> str:
    """異常系テスト用スキーマのsetup/teardownを管理するfixture。

    テストモジュール開始時にスキーマを作成し、終了時にDROP CASCADEで削除する。
    これにより、異常系テストで登録された不正データがMVに残り続ける問題を防ぐ。

    Args:
        spark: SparkSession。
        catalog: カタログ名（shogi_dev/shogi_test/shogi）。

    Yields:
        str: 異常系テスト用スキーマ名（{catalog}.test_abnormal）。

    Note:
        scope="module" により、同一テストモジュール内のテストでスキーマを共有する。
        テストモジュール完了時に自動的にDROP CASCADEが実行される。
    """
    schema_name = f"{catalog}.test_abnormal"

    # Setup: スキーマ作成
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS IDENTIFIER('{schema_name}')")

    yield schema_name

    # Teardown: スキーマ削除（CASCADEで配下のテーブル/MVも削除）
    spark.sql(f"DROP SCHEMA IF EXISTS IDENTIFIER('{schema_name}') CASCADE")


@pytest.fixture(scope="module")
def start_abnormal_pipeline_update(catalog: str):
    """異常系テスト用pipeline起動関数を提供するfixture。

    既存pipelineを再利用しつつ、異常系テスト用スキーマを指定して起動する。

    Args:
        catalog: カタログ名（shogi_dev/shogi_test/shogi）。

    Returns:
        Callable[[str], str]: pipeline_idを受け取り、update_idを返す関数。
    """
    def _start(pipeline_id: str) -> str:
        return start_pipeline_update_with_params(
            pipeline_id=pipeline_id,
            catalog=catalog,
            landing_schema="test_abnormal",
            silver_schema="test_abnormal",
            gold_schema="test_abnormal",
        )
    return _start
