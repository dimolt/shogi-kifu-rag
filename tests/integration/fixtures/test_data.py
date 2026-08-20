"""テストデータ管理用fixture定義。

テストデータ原本からVolumeへのコピー、クリーンアップを管理する。
"""
from pathlib import Path

import pytest
from databricks.sdk import WorkspaceClient
from pyspark.sql import SparkSession

from tests.helpers.databricks.volume_helpers import (
    cleanup_volume_directory,
    copy_directory_to_volume,
    get_landing_volume_path,
)


@pytest.fixture(scope="session")
def workspace_client() -> WorkspaceClient:
    """WorkspaceClientインスタンスを提供する。

    Returns:
        WorkspaceClient: Databricks Workspaceクライアント。
    """
    import os

    profile = os.environ.get("DATABRICKS_CONFIG_PROFILE", "shogi")
    return WorkspaceClient(profile=profile)


@pytest.fixture(scope="session")
def volume_setup(spark: SparkSession, catalog: str):
    """セッション開始時にVolumeの初期化を行うfixture。

    Volumeの存在確認を行い、必要に応じて初期化する。
    スキーマ自体は削除しない。

    Args:
        spark: SparkSession。
        catalog: カタログ名。

    Yields:
        None: 初期化完了後にyield。
    """
    # landing schemaの存在確認
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS IDENTIFIER('{catalog}.landing')")
    # test schemaの存在確認
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS IDENTIFIER('{catalog}.test')")

    yield


@pytest.fixture
def clean_volume(volume_setup, spark: SparkSession, catalog: str):
    """各テスト前にVolume内のデータをクリーンアップするfixture。

    Volume内のファイルを削除し、Bronze/Silver/GoldテーブルをDROPする。
    テストケース間のデータ混在を防ぐ。

    Args:
        volume_setup: volume_setup fixture。
        spark: SparkSession。
        catalog: カタログ名。

    Yields:
        None: クリーンアップ完了後にyield。
    """
    # Setup: Volume内のファイルを削除
    landing_volume_path = get_landing_volume_path(catalog)
    cleanup_volume_directory(landing_volume_path)

    # Bronze/Silver/Goldテーブルを削除
    for schema in ["bronze", "silver", "gold"]:
        try:
            tables = spark.sql(f"SHOW TABLES IN {catalog}.{schema}")
            for row in tables.collect():
                table_name = row["tableName"]
                spark.sql(f"DROP TABLE IF EXISTS {catalog}.{schema}.{table_name}")
        except Exception:
            # スキーマが存在しない場合は無視
            pass

    yield

    # Teardown: テスト後に再度クリーンアップ（念のため）
    cleanup_volume_directory(landing_volume_path)


@pytest.fixture
def normal_test_data(clean_volume, catalog: str):
    """正常系テストデータをVolumeにコピーするfixture。

    tests/integration/data/normal/ の内容をVolume/analyzed/にコピーする。

    Args:
        clean_volume: clean_volume fixture。
        catalog: カタログ名。

    Yields:
        None: コピー完了後にyield。
    """
    project_root = Path(__file__).parent.parent.parent.parent
    normal_data_dir = project_root / "tests" / "integration" / "data" / "normal"
    landing_volume_path = get_landing_volume_path(catalog)

    # 正常系データをVolumeにコピー
    copy_directory_to_volume(normal_data_dir, landing_volume_path)

    yield


@pytest.fixture
def abnormal_test_data(clean_volume, catalog: str):
    """異常系テストデータをVolumeにコピーするfixture。

    tests/integration/data/abnormal/ の内容をVolume/analyzed/にコピーする。

    Args:
        clean_volume: clean_volume fixture。
        catalog: カタログ名。

    Yields:
        None: コピー完了後にyield。
    """
    project_root = Path(__file__).parent.parent.parent.parent
    abnormal_data_dir = project_root / "tests" / "integration" / "data" / "abnormal"
    landing_volume_path = get_landing_volume_path(catalog)

    # 異常系データをVolumeにコピー
    copy_directory_to_volume(abnormal_data_dir, landing_volume_path)

    yield
