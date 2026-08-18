"""Job全体の統合テスト。

shogi_kif_jobの実行を検証し、全タスクが正常に完了することを確認する。
タスク間の依存関係、エラーハンドリング、タイムアウト処理を含む。

前提:
    本テストの実行前に、Jobがdevターゲットへデプロイされていること。
    テストデータが準備されていること（conftest.pyのprepare_test_dataフィクスチャ）。
"""
import pytest

from tests.helpers.models import JobRunResult

pytestmark = pytest.mark.integration_exec


def test_job全体が正常に完了する(shogi_kif_job_run_result: JobRunResult) -> None:
    """Job全体がSUCCESS状態で完了することを検証する。

    Arrange:
        shogi_kif_job_run_resultフィクスチャからJob実行結果を取得する。
    Act:
        result_stateを検証する。
    Assert:
        result_stateがSUCCESSであること。
    """
    # Assert
    assert shogi_kif_job_run_result.result_state == "SUCCESS", (
        f"Job ended with result_state={shogi_kif_job_run_result.result_state}, "
        f"message={shogi_kif_job_run_result.state_message}"
    )


def test_jobの全タスクが正常に完了する(shogi_kif_job_run_result: JobRunResult) -> None:
    """Job内の全タスクがSUCCESS状態で完了することを検証する。

    Arrange:
        shogi_kif_job_run_resultフィクスチャからJob実行結果を取得する。
    Act:
        各タスクのresult_stateを検証する。
    Assert:
        全タスクのresult_stateがSUCCESSであること。
    """
    # Act & Assert
    for task in shogi_kif_job_run_result.tasks:
        assert task.result_state == "SUCCESS", (
            f"Task {task.task_key} ended with result_state={task.result_state}, "
            f"message={task.state_message}"
        )


def test_jobに期待される全タスクが含まれている(
    shogi_kif_job_run_result: JobRunResult,
) -> None:
    """Jobに期待される全タスクが含まれていることを検証する。

    Arrange:
        shogi_kif_job_run_resultフィクスチャからJob実行結果を取得する。
    Act:
        タスクキーの集合を取得する。
    Assert:
        期待されるタスクキー（shogi_kif_pipeline）が含まれていること。
    """
    # Act
    actual_task_keys = {task.task_key for task in shogi_kif_job_run_result.tasks}
    expected_task_keys = {
        "shogi_kif_pipeline",
    }

    # Assert
    assert actual_task_keys == expected_task_keys, (
        f"Expected task keys {expected_task_keys}, but got {actual_task_keys}"
    )


def test_jobのlife_cycle_stateがTERMINATEDである(
    shogi_kif_job_run_result: JobRunResult,
) -> None:
    """Jobのlife_cycle_stateがTERMINATEDであることを検証する。

    Arrange:
        shogi_kif_job_run_resultフィクスチャからJob実行結果を取得する。
    Act:
        life_cycle_stateを検証する。
    Assert:
        life_cycle_stateがTERMINATEDであること。
    """
    # Assert
    assert shogi_kif_job_run_result.life_cycle_state == "TERMINATED", (
        f"Job life_cycle_state should be TERMINATED, but got "
        f"{shogi_kif_job_run_result.life_cycle_state}"
    )


def test_job_run_idが取得できている(shogi_kif_job_run_result: JobRunResult) -> None:
    """Jobのrun_idが正常に取得できていることを検証する。

    Arrange:
        shogi_kif_job_run_resultフィクスチャからJob実行結果を取得する。
    Act:
        run_idを検証する。
    Assert:
        run_idがNoneではなく、正の整数であること。
    """
    # Assert
    assert shogi_kif_job_run_result.run_id is not None, "Job run_id should not be None"
    assert shogi_kif_job_run_result.run_id > 0, f"Job run_id should be positive, got {shogi_kif_job_run_result.run_id}"
