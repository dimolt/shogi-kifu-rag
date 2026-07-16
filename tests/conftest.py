"""pytest共通フィクスチャ定義（ルート）。

Databricks Connect経由のSpark統合テスト用フィクスチャを提供する。
integration層・e2e層の両方から参照される。
Databricks接続フィクスチャ（spark, pipeline_id等）はunitテストから参照しないこと。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

from tests.fixtures.tables import (  # noqa: F401
    floodgate_positions_df,
    game_summary_df,
    joseki_knowledge_df,
    position_features_df,
    positions_df,
)
from tests.helpers.databricks.cli import databricks_cli_base_args

# Driverが使っているPython実行ファイルをWorkerにも強制させる
# (uv環境でPATH上に複数バージョンのPythonが存在する場合のバージョン不一致を防ぐ)
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

# databricksモジュールをインポート可能にするためPythonパスに追加
_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

# dotenvで環境変数をロードする
load_dotenv(_PROJECT_ROOT / ".env")
_DATABRICKS_PROFILE = os.environ.get("DATABRICKS_CONFIG_PROFILE")


@pytest.fixture(scope="session")
def databricks_profile() -> str | None:
    """Databricks CLIのプロファイル名を返す。

    Returns:
        str | None: プロファイル名。未設定時はNone。
    """
    return _DATABRICKS_PROFILE


@pytest.fixture(scope="session")
def _bundle_resources() -> dict:
    """`databricks bundle summary`の実行結果をパースして返す。

    Returns:
        dict: `resources`セクションを含むbundle summaryのJSON全体。
    """
    result = subprocess.run(
        ["databricks", "bundle", "summary", "--output", "json", "-t", "dev", *databricks_cli_base_args()],
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
        本fixtureはパイプラインを起動しない。integration層では、event_log()の
        検証対象となる実行結果がCIの定期実行や手動実行によって事前に生成されて
        いることを前提とする。e2e層では呼び出し元がこのIDを使って自ら起動する。

    Returns:
        str: databricks.yml で定義されたsilver_pipelineのID。
    """
    return _bundle_resources["resources"]["pipelines"]["silver_pipeline"]["id"]


@pytest.fixture(scope="session")
def gold_pipeline_id(_bundle_resources: dict) -> str:
    """デプロイ済みgold_pipelineのpipeline_idを取得する。

    前提:
        本fixtureはパイプラインを起動しない。integration層では、event_log()の
        検証対象となる実行結果がCIの定期実行や手動実行によって事前に生成されて
        いることを前提とする。e2e層では呼び出し元がこのIDを使って自ら起動する。

    Returns:
        str: databricks.yml で定義されたgold_pipelineのID。
    """
    return _bundle_resources["resources"]["pipelines"]["gold_pipeline"]["id"]
