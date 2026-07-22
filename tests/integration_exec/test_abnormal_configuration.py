"""Configuration異常系の統合実行テスト（Issue #147のサブIssue: #209, #211）。

対象Issue:
    #209 Invalid configuration parameters（Job実行時のcatalogパラメータ上書き）
    #211 Environment-specific configuration validation（多環境対応の変数解決確認）

    #210 Missing required configuration は対応対象外（本ファイルには含まない）。

設計上の前提・注意:
    #209は当初「不正なcatalog名でデプロイ→Job実行」として計画していたが、
        Databricks Free Edition（ワークスペースが1つ）では複数targetを同時に
        デプロイできず（例: `test`にデプロイするには既存の`dev`を破棄する必要がある）、
        他のintegration_execテストが前提とする`dev`のデプロイ状態と両立しないため、
        **デプロイを伴わない設計に変更した**。
        `shogi_kif_rag_main_job`にJobレベルパラメータ`catalog`を追加し
        （dbx_bundle/resources/workflows/jobs.yml）、`run_now(job_parameters=...)`で
        Bundle再デプロイ無しに実行時だけcatalogを不正な値に差し替える。
        `dev`のデプロイ状態には一切変更を加えないため、他のintegration_execテストと
        同一CI実行内で安全に共存できる。
        この方式で上書きできるのはJobレベルパラメータを参照するタスク
        （floodgate, wikipedia）のみ。silver_pipeline/gold_pipeline（DLTパイプライン）は
        catalogがパイプラインリソース自体の定義に紐づき、実行時上書きの対象外のため、
        本テストのスコープからは意図的に除外している（Issueコメントで経緯を記録）。
    #211は`bundle validate --output json`の`variables.<name>.value`から
        解決済み変数値を取得する前提で実装している。`bundle validate`はローカルでの
        変数解決・スキーマチェックにとどまりリソースの作成/破棄を行わないため、
        dev/test/prodのいずれに対しても安全に実行できる。Databricks CLIのバージョンに
        よって出力スキーマが変わる可能性があるため、初回実行時に実際の出力と
        突き合わせて確認すること。
"""
from __future__ import annotations

import pytest

from tests.helpers.models import JobRunFailedError
from tests.helpers.monitoring.job_monitoring import JobMonitor
from tests.integration_exec.fixtures.config_validation import run_bundle_validate_json

pytestmark = pytest.mark.integration_exec

# Issue #209で使用する、実在しないことが確実なcatalog名。
_NONEXISTENT_CATALOG = "shogi_nonexistent_catalog_for_test_209"

# Issue #209でJobレベルパラメータの実行時上書きが効くタスク
# （catalogを`{{job.parameters.catalog}}`経由で参照しているタスクのみ）。
_TASKS_AFFECTED_BY_CATALOG_OVERRIDE = {"floodgate", "wikipedia"}

# Issue #211で検証する、target別に期待されるcatalog変数の解決値。
# databricks.yml のtargets.<target>.variables.catalog と対応させている。
_EXPECTED_CATALOG_BY_TARGET = {
    "dev": "shogi_dev",
    "test": "shogi_test",
    "prod": "shogi",
}


# ---------------------------------------------------------------------------
# Issue #209: Invalid configuration parameters
# ---------------------------------------------------------------------------


def test_job実行時に不正なcatalog名を上書き指定した場合_対象タスクが明確なエラーで失敗する(
    job_id: int, workspace_client
) -> None:
    """存在しないcatalog名をJobレベルパラメータとして実行時上書きすると、対象タスクが失敗する。

    デプロイ済みの`dev`のJob定義自体は一切変更しない
    （`run_now`の`job_parameters`によるこの実行1回限りの上書き）。

    Arrange:
        既存のdevデプロイから取得した`job_id`を使い、`job_parameters`で
        catalogを不正な値に上書きしてJobを起動する。
    Act:
        Job完了を待機する。
    Assert:
        `JobRunFailedError`が送出され、そのメッセージに不正catalog名を参照する
        floodgate/wikipediaタスクの失敗が含まれること。
    """
    # Arrange & Act
    waiter = workspace_client.jobs.run_now(
        job_id=job_id,
        job_parameters={"catalog": _NONEXISTENT_CATALOG},
    )

    with pytest.raises(JobRunFailedError) as exc_info:
        JobMonitor(workspace_client).wait_for_completion(waiter.run_id)

    # Assert
    error_message = str(exc_info.value)
    assert any(task_key in error_message for task_key in _TASKS_AFFECTED_BY_CATALOG_OVERRIDE), (
        f"failure message should reference one of {_TASKS_AFFECTED_BY_CATALOG_OVERRIDE}, "
        f"but got:\n{error_message}"
    )


# ---------------------------------------------------------------------------
# Issue #211: Environment-specific configuration validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("target", sorted(_EXPECTED_CATALOG_BY_TARGET))
def test_bundle_validate_各targetでcatalog変数が意図通りに解決される(target: str) -> None:
    """target別に`bundle validate`を実行し、catalog変数が意図した値に解決されることを確認する。

    Arrange:
        dev/test/prodそれぞれに対応する期待catalog名（databricks.ymlのtargets定義と一致）
        を用意する。
    Act:
        `databricks bundle validate -t <target> --output json`を実行し、
        変数`catalog`の解決結果を取得する。
    Assert:
        解決されたcatalog値が、そのtargetに期待する値と一致すること。
    """
    # Act
    result = run_bundle_validate_json(target=target)

    # Assert
    resolved_catalog = result["variables"]["catalog"]["value"]
    assert resolved_catalog == _EXPECTED_CATALOG_BY_TARGET[target], (
        f"target={target}: expected catalog={_EXPECTED_CATALOG_BY_TARGET[target]}, "
        f"but got {resolved_catalog}"
    )
