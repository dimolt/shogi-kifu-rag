"""Sparkセッション構築用フィクスチャ。

integration層・e2e層の双方から参照される。
"""
import pytest
from databricks.connect import DatabricksSession
from pyspark.sql import SparkSession


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
