"""pytest共通フィクスチャ定義。

Databricks Connect経由のSpark統合テスト用フィクスチャを提供する。
unitテストからは参照しないこと（Databricksへの接続が発生するため）。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from databricks.connect import DatabricksSession
from pyspark.sql import DataFrame, SparkSession

_TEST_CATALOG = "test_catalog"
_TEST_SILVER_SCHEMA = "shogi_silver"
_TEST_GOLD_SCHEMA = "shogi_gold"

# Driverが使っているPython実行ファイルをWorkerにも強制させる
# (uv環境でPATH上に複数バージョンのPythonが存在する場合のバージョン不一致を防ぐ)
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

# databricksモジュールをインポート可能にするためPythonパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

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
def _bundle_resources() -> dict:
    """`databricks bundle summary`の実行結果をパースして返す。

    Returns:
        dict: `resources`セクションを含むbundle summaryのJSON全体。
    """
    result = subprocess.run(
        ["databricks", "bundle", "summary", "--output", "json", "-t", "dev", "-p", "shogi"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(result.stdout)


@pytest.fixture(scope="session")
def silver_pipeline_id(_bundle_resources: dict) -> str:
    """デプロイ済みsilver_pipelineのpipeline_idを取得する。

    前提:
        本fixtureはパイプラインを起動しない。event_log()の検証対象となる
        実行結果は、CIの定期実行や手動での`databricks bundle run`によって
        事前に生成されていることを前提とする。

    Returns:
        str: databricks.yml で定義されたsilver_pipelineのID。
    """
    return _bundle_resources["resources"]["pipelines"]["silver_pipeline"]["id"]


@pytest.fixture(scope="session")
def gold_pipeline_id(_bundle_resources: dict) -> str:
    """デプロイ済みgold_pipelineのpipeline_idを取得する。

    前提:
        本fixtureはパイプラインを起動しない。event_log()の検証対象となる
        実行結果は、CIの定期実行や手動での`databricks bundle run`によって
        事前に生成されていることを前提とする。

    Returns:
        str: databricks.yml で定義されたgold_pipelineのID。
    """
    return _bundle_resources["resources"]["pipelines"]["gold_pipeline"]["id"]


def _fqn(schema: str, table: str) -> str:
    """カタログ・スキーマ・テーブル名から完全修飾名を組み立てる。

    Args:
        schema: スキーマ名（Silver/Gold）。
        table: テーブル名。

    Returns:
        str: `catalog.schema.table` 形式の完全修飾名。
    """
    return f"{_TEST_CATALOG}.{schema}.{table}"


@pytest.fixture(scope="session")
def positions_fqn() -> str:
    """SilverテーブルpositionsのFQNを返す。"""
    return _fqn(_TEST_SILVER_SCHEMA, "positions")


@pytest.fixture(scope="session")
def position_features_fqn() -> str:
    """Goldテーブルposition_featuresのFQNを返す。"""
    return _fqn(_TEST_GOLD_SCHEMA, "position_features")


@pytest.fixture(scope="session")
def game_summary_fqn() -> str:
    """Goldテーブルgame_summaryのFQNを返す。"""
    return _fqn(_TEST_GOLD_SCHEMA, "game_summary")


@pytest.fixture(scope="session")
def positions_df(spark: SparkSession, positions_fqn: str) -> DataFrame:
    """Silverテーブルpositionsを読み込んだDataFrameを提供する。

    Returns:
        positionsテーブルの全件を保持するDataFrame。
    """
    return spark.table(positions_fqn)


@pytest.fixture(scope="session")
def position_features_df(spark: SparkSession, position_features_fqn: str) -> DataFrame:
    """Goldテーブルposition_featuresを読み込んだDataFrameを提供する。

    Returns:
        position_featuresテーブルの全件を保持するDataFrame。
    """
    return spark.table(position_features_fqn)


@pytest.fixture(scope="session")
def game_summary_df(spark: SparkSession, game_summary_fqn: str) -> DataFrame:
    """Goldテーブルgame_summaryを読み込んだDataFrameを提供する。

    Returns:
        game_summaryテーブルの全件を保持するDataFrame。
    """
    return spark.table(game_summary_fqn)
