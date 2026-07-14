"""Job全体の統合テスト。

shogi_kif_rag_main_jobの実行を検証し、全タスクが正常に完了することを確認する。
タスク間の依存関係、エラーハンドリング、タイムアウト処理を含む。

前提:
    本テストの実行前に、Jobがdevターゲットへデプロイされていること。
    テストデータが準備されていること（conftest.pyのprepare_test_dataフィクスチャ）。
"""
import pytest
from helpers.models import JobRunResult

pytestmark = pytest.mark.integration


def test_job全体が正常に完了する(job_run_result: JobRunResult) -> None:
    """Job全体がSUCCESS状態で完了することを検証する。

    Arrange:
        job_run_resultフィクスチャからJob実行結果を取得する。
    Act:
        result_stateを検証する。
    Assert:
        result_stateがSUCCESSであること。
    """
    # Assert
    assert job_run_result.result_state == "SUCCESS", (
        f"Job ended with result_state={job_run_result.result_state}, "
        f"message={job_run_result.state_message}"
    )


def test_jobの全タスクが正常に完了する(job_run_result: JobRunResult) -> None:
    """Job内の全タスクがSUCCESS状態で完了することを検証する。

    Arrange:
        job_run_resultフィクスチャからJob実行結果を取得する。
    Act:
        各タスクのresult_stateを検証する。
    Assert:
        全タスクのresult_stateがSUCCESSであること。
    """
    # Act & Assert
    for task in job_run_result.tasks:
        assert task.result_state == "SUCCESS", (
            f"Task {task.task_key} ended with result_state={task.result_state}, "
            f"message={task.state_message}"
        )


def test_jobに期待される全タスクが含まれている(
    job_run_result: JobRunResult,
) -> None:
    """Jobに期待される全タスクが含まれていることを検証する。

    Arrange:
        job_run_resultフィクスチャからJob実行結果を取得する。
    Act:
        タスクキーの集合を取得する。
    Assert:
        期待されるタスクキー（silver_pipeline, gold_pipeline, floodgate, wikipedia）
        が全て含まれていること。
    """
    # Act
    actual_task_keys = {task.task_key for task in job_run_result.tasks}
    expected_task_keys = {
        "silver_pipeline",
        "gold_pipeline",
        "floodgate",
        "wikipedia",
    }

    # Assert
    assert actual_task_keys == expected_task_keys, (
        f"Expected task keys {expected_task_keys}, but got {actual_task_keys}"
    )


def test_jobのlife_cycle_stateがTERMINATEDである(
    job_run_result: JobRunResult,
) -> None:
    """Jobのlife_cycle_stateがTERMINATEDであることを検証する。

    Arrange:
        job_run_resultフィクスチャからJob実行結果を取得する。
    Act:
        life_cycle_stateを検証する。
    Assert:
        life_cycle_stateがTERMINATEDであること。
    """
    # Assert
    assert job_run_result.life_cycle_state == "TERMINATED", (
        f"Job life_cycle_state should be TERMINATED, but got "
        f"{job_run_result.life_cycle_state}"
    )


def test_job_run_idが取得できている(job_run_result: JobRunResult) -> None:
    """Jobのrun_idが正常に取得できていることを検証する。

    Arrange:
        job_run_resultフィクスチャからJob実行結果を取得する。
    Act:
        run_idを検証する。
    Assert:
        run_idがNoneではなく、正の整数であること。
    """
    # Assert
    assert job_run_result.run_id is not None, "Job run_id should not be None"
    assert job_run_result.run_id > 0, f"Job run_id should be positive, got {job_run_result.run_id}"
