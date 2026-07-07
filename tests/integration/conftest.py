"""pytest統合テスト用フィクスチャ定義（Layer 2）。

spark, pipeline_id, FQN系のフィクスチャは `tests/conftest.py`（ルート）に
集約されているため、ここではintegration層固有のDataFrame系フィクスチャのみ定義する。
"""
import sys
from pathlib import Path

import pytest
from databricks.connect import DatabricksSession
from pyspark.sql import DataFrame, SparkSession

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
