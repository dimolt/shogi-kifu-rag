"""Databricks Job実行・監視まわりのfixture定義（Job-based integration test用）。"""
import pytest
from databricks.sdk import WorkspaceClient

from tests.helpers.models import JobRunResult
from tests.helpers.monitoring.job_monitoring import JobMonitor


@pytest.fixture(scope="session")
def workspace_client(databricks_profile: str) -> WorkspaceClient:
    """Job実行監視（JobMonitor）に使用するWorkspaceClientを構築する。

    sparkフィクスチャと同様、ローカル実行時はDATABRICKS_CONFIG_PROFILE環境変数で
    指定したプロファイルを使用し、CI/CD（サービスプリンシパル認証）では
    プロファイル指定なしで環境変数ベースのデフォルト認証チェーンに委ねる。
    """
    if databricks_profile:
        return WorkspaceClient(profile=databricks_profile)
    return WorkspaceClient()


@pytest.fixture(scope="session")
def job_id(_bundle_resources: dict) -> int:
    """デプロイ済みshogi_kif_rag_main_jobのjob_idをCLI経由で取得する。

    databricks bundle summary CLI実行結果から取得する。
    本fixtureはJobを起動しない。

    Returns:
        int: databricks.yml/jobs.yml で定義されたshogi_kif_rag_main_jobのID。
    """
    return _bundle_resources["resources"]["jobs"]["shogi_kif_rag_main_job"]["id"]


@pytest.fixture(scope="session")
def job_run_result(workspace_client: WorkspaceClient, job_id: int) -> JobRunResult:
    """shogi_kif_rag_main_jobをSDK経由で起動し、完了するまで待機した結果を提供する。

    job_idの取得はCLI経由、Job自体の起動・監視はDatabricks SDK経由という、
    Hybrid CLI + SDKアプローチを採る。

    Returns:
        JobRunResult: Job全体・タスク単位の実行結果。

    Raises:
        JobRunFailedError: いずれかのタスクがSUCCESS以外の結果で終了した場合。
        TimeoutError: タイムアウト時間内に完了しなかった場合。
    """
    waiter = workspace_client.jobs.run_now(job_id=job_id)
    return JobMonitor(workspace_client).wait_for_completion(waiter.run_id)
