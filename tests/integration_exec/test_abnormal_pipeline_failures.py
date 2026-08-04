"""PipelineFailures系異常系テスト（Issue #203-#206）。

対象Issue:
    #203: Silver pipeline failure prevents Gold execution
    #204: Gold pipeline failure doesn't affect Silver output
    #205: Partial failure recovery
    #206: Failure notification and logging（#203-#205に統合）

設計上の前提:
    - integration_exec層なのでJob実行が必要（数分〜十数分待機）
    - #203-#205は並列実行可能
    - shogi_kif_pipeline_idはtests/conftest.pyから継承
    - #206は各失敗シナリオ内でget_event_log_errors()を呼び出してエラーメッセージを検証
"""
from __future__ import annotations

import pytest
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import RunResultState
from pyspark.sql import SparkSession

from tests.helpers.models import JobRunFailedError
from tests.helpers.monitoring.job_monitoring import JobMonitor

pytestmark = pytest.mark.integration_exec

# Issue #205で使用する、実在しないことが確実なcatalog名。
_NONEXISTENT_CATALOG = "shogi_nonexistent_catalog_for_test_205"

# Issue #205でJobレベルパラメータの実行時上書きが効くタスク
# （catalogを`{{job.parameters.catalog}}`経由で参照しているタスクのみ）。
_TASKS_AFFECTED_BY_CATALOG_OVERRIDE = {"floodgate", "wikipedia_raw", "joseki_knowledge"}


# ---------------------------------------------------------------------------
# Issue #203: Silver pipeline failure prevents Gold execution
# ---------------------------------------------------------------------------


def test_silver_pipeline_failure_prevents_gold_execution(
    spark: SparkSession,
    job_id: int,
    workspace_client: WorkspaceClient,
    catalog: str,
    shogi_kif_pipeline_id: str,
    empty_landing_volume,
) -> None:
    """Silver入力を意図的に破壊した状態でJobを実行し、パイプラインが失敗することを確認する。

    Note: Issue #203はパイプライン統合（Issue #245）により廃止された。
    元のテストはsilver_pipelineとgold_pipelineの依存関係を検証していたが、
    統合後は単一のshogi_kif_pipelineとなり、この依存関係は存在しない。
    本テストはパイプライン失敗時のエラーメッセージ検証に縮小して残している。

    Arrange:
        empty_landing_volume fixtureを使用してlanding volumeのCSVファイルを一時的に削除し、
        空の状態にする。テスト後にCSVファイルは自動的に復元される。
        注: CSVの列欠損や型不一致はexpectation発火のみでパイプライン失敗にはならないため、
        空のvolumeを参照させることでパイプライン失敗を誘発する。
    Act:
        Jobを実行し、完了まで待機。
    Assert:
        shogi_kif_pipelineタスクのresult_stateがFAILEDであること。
        失敗時に原因特定に足るエラーメッセージが取得できること（#206統合）。
    """
    # Arrange: empty_landing_volume fixtureがCSVをバックアップし、空の状態にする

    # Act: Job実行（失敗を期待）
    waiter = workspace_client.jobs.run_now(job_id=job_id)
    run_id = waiter.run_id

    with pytest.raises(JobRunFailedError) as exc_info:
        JobMonitor(workspace_client).wait_for_completion(run_id)

    # Assert: タスク状態を詳細確認
    run = workspace_client.jobs.get_run(run_id)

    # shogi_kif_pipelineが失敗していること
    pipeline_task = next((t for t in run.tasks if t.task_key == "shogi_kif_pipeline"), None)
    assert pipeline_task is not None, "shogi_kif_pipeline task not found"
    assert pipeline_task.state.result_state == RunResultState.FAILED, (
        f"shogi_kif_pipeline should be FAILED, but got {pipeline_task.state.result_state}"
    )

    # #206: エラーメッセージ取得・検証
    error_message = str(exc_info.value)
    assert "shogi_kif_pipeline" in error_message, (
        f"Error message should reference shogi_kif_pipeline:\n{error_message}"
    )


# ---------------------------------------------------------------------------
# Issue #204: Gold pipeline failure doesn't affect Silver output
# ---------------------------------------------------------------------------


def test_gold_pipeline_failure_doesnt_affect_silver_output(
    spark: SparkSession,
    job_id: int,
    workspace_client: WorkspaceClient,
    catalog: str,
    shogi_kif_pipeline_id: str,
) -> None:
    """Gold側のexpectation違反を誘発し、Silver出力が変更されていないことを確認する。

    Note: Issue #204はパイプライン統合（Issue #245）により廃止された。
    元のテストはsilver_pipelineとgold_pipelineの分離を検証していたが、
    統合後は単一のshogi_kif_pipelineとなり、この分離は存在しない。
    """
    pytest.skip(
        "Issue #204: パイプライン統合（Issue #245）により廃止された。"
        "silver_pipelineとgold_pipelineは単一のshogi_kif_pipelineに統合されたため、"
        "このテストは不要になった。"
    )


# ---------------------------------------------------------------------------
# Issue #205: Partial failure recovery
# ---------------------------------------------------------------------------


def test_partial_failure_recovery(
    job_id: int,
    workspace_client: WorkspaceClient,
) -> None:
    """floodgate/wikipedia_raw/joseki_knowledgeのみを意図的に失敗させ、他タスクが正常完了することを確認する。

    Arrange:
        不正なcatalog名をjob_parametersで指定。
    Act:
        Jobを実行し、完了まで待機。
    Assert:
        失敗タスク以外（shogi_kif_pipeline）が正常完了すること。
        失敗時に原因特定に足るエラーメッセージが取得できること（#206統合）。
    """
    # Arrange & Act
    waiter = workspace_client.jobs.run_now(
        job_id=job_id,
        job_parameters={"catalog": _NONEXISTENT_CATALOG},
    )
    run_id = waiter.run_id

    with pytest.raises(JobRunFailedError) as exc_info:
        JobMonitor(workspace_client).wait_for_completion(run_id)

    # Assert: タスク状態を詳細確認
    run = workspace_client.jobs.get_run(run_id)

    # floodgate/wikipediaが失敗していること
    for task_key in _TASKS_AFFECTED_BY_CATALOG_OVERRIDE:
        task = next((t for t in run.tasks if t.task_key == task_key), None)
        assert task is not None, f"{task_key} task not found"
        assert task.state.result_state == RunResultState.FAILED, (
            f"{task_key} should be FAILED, but got {task.state.result_state}"
        )

    # shogi_kif_pipelineは成功していること
    pipeline_task = next((t for t in run.tasks if t.task_key == "shogi_kif_pipeline"), None)
    assert pipeline_task is not None, "shogi_kif_pipeline task not found"
    assert pipeline_task.state.result_state == RunResultState.SUCCESS, (
        f"shogi_kif_pipeline should be SUCCESS, but got {pipeline_task.state.result_state}"
    )

    # #206: エラーメッセージ取得・検証
    error_message = str(exc_info.value)
    assert any(
        task_key in error_message for task_key in _TASKS_AFFECTED_BY_CATALOG_OVERRIDE
    ), (
        f"Error message should reference failed tasks ({_TASKS_AFFECTED_BY_CATALOG_OVERRIDE}):\n{error_message}"
    )
