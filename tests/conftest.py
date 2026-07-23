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
from tests.helpers.databricks.volume_helpers import (
    backup_csv_files,
    get_landing_volume_path,
    restore_csv_files,
)

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


def pytest_addoption(parser):
    """pytestコマンドラインオプションを追加する。

    Args:
        parser: pytestのコマンドラインパーサー。
    """
    parser.addoption("--bundle-target", default="dev", help="Bundle target (dev/test/prod)")
    parser.addoption("--catalog", default="shogi_dev", help="catalog name (shogi_dev/shogi_test/shogi)")


@pytest.fixture(scope="session")
def bundle_target(request):
    """Databricks Bundleのターゲット環境を返す。

    各テスト層のconftest.pyでpytest_configure()を通じて自動設定される。
    コマンドラインで--bundle-targetオプションを指定することで明示的に上書きも可能。

    Args:
        request: pytestのrequestオブジェクト。

    Returns:
        str: bundle target (dev/test/prod)。
    """
    return request.config.getoption("--bundle-target")


@pytest.fixture(scope="session")
def catalog(request):
    """テスト対象のUnity Catalogカタログ名を返す。

    各テスト層のconftest.pyでpytest_configure()を通じて自動設定される。
    コマンドラインで--catalogオプションを指定することで明示的に上書きも可能。

    Args:
        request: pytestのrequestオブジェクト。

    Returns:
        str: catalog name (shogi_dev/shogi_test/shogi)。
    """
    return request.config.getoption("--catalog")


@pytest.fixture(scope="session")
def databricks_profile() -> str | None:
    """Databricks CLIのプロファイル名を返す。

    Returns:
        str | None: プロファイル名。未設定時はNone。
    """
    return _DATABRICKS_PROFILE


@pytest.fixture(scope="session")
def _bundle_resources(bundle_target: str) -> dict:
    """`databricks bundle summary`の実行結果をパースして返す。

    Args:
        bundle_target: バンドルターゲット。

    Returns:
        dict: `resources`セクションを含むbundle summaryのJSON全体。
    """
    result = subprocess.run(
        ["databricks", "bundle", "summary", "--output", "json", "-t", bundle_target, *databricks_cli_base_args()],
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


@pytest.fixture(scope="session")
def main_job_id(_bundle_resources: dict) -> str:
    """デプロイ済みshogi_kif_rag_main_jobのjob_idを取得する。

    前提:
        本fixtureはJobを起動しない。e2e層では呼び出し元がこのIDを使って自ら起動する。

    Returns:
        str: jobs.yml で定義されたshogi_kif_rag_main_jobのID。
    """
    return _bundle_resources["resources"]["jobs"]["shogi_kif_rag_main_job"]["id"]


@pytest.fixture
def empty_landing_volume(catalog: str):
    """CSVファイルを一時的にバックアップし、テスト後に復元するfixture。

    テスト実行前にlanding volumeのCSVファイルをバックアップし、
    テスト実行後に復元する。テストが失敗しても復元は必ず実行される。

    Args:
        catalog: カタログ名。

    Yields:
        None: CSVファイルがバックアップされ、空の状態でテストが実行される。
    """
    volume_path = get_landing_volume_path(catalog)
    backup = backup_csv_files(volume_path)
    yield
    restore_csv_files(volume_path, backup)
