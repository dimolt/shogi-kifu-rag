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
def spark(databricks_profile: str) -> SparkSession:
    """環境に応じてDatabricks Connectセッションを構築する。

    ローカル実行時はDATABRICKS_CONFIG_PROFILE環境変数で指定したプロファイルを使用し、
    CI/CD（サービスプリンシパル認証）ではprofile()を呼ばず、環境変数ベースの
    デフォルト認証チェーン（oauth-m2m）に委ねる。

    ローカルの`.databrickscfg`ではプロファイル側の`serverless_compute_id = auto`に
    暗黙的に依存していたが、CD環境にはプロファイル自体が存在せずクラスタ／サーバーレスの
    どちらも解決できないため、`.serverless()`を明示的に指定し環境差を無くす。
    """
    builder = DatabricksSession.builder.serverless()
    if databricks_profile:
        builder = builder.profile(databricks_profile)
    return builder.getOrCreate()


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
