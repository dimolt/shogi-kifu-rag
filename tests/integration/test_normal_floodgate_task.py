"""floodgateタスクの統合テスト。

floodgateタスクの実行と出力データを検証する。
Silver/Goldスキーマのデータを使用してfloodgate処理が正常に行われていることを確認する。

前提:
    本テストの実行前に、floodgate_jobが実行され、
    floodgateタスクが正常に完了していること。
"""
import pytest
from pyspark.sql import DataFrame

from tests.helpers.models import JobRunResult, TaskResult

pytestmark = [pytest.mark.integration, pytest.mark.normal]


@pytest.fixture(scope="session")
def floodgate_raw_task_result(floodgate_job_run_result: JobRunResult) -> TaskResult:
    """floodgate_job_run_resultからfloodgate_rawタスクの結果を抽出する。

    Args:
        floodgate_job_run_result: floodgate_job実行結果。

    Returns:
        TaskResult: floodgate_rawタスクの実行結果。
    """
    for task in floodgate_job_run_result.tasks:
        if task.task_key == "floodgate_raw":
            return task
    raise ValueError("floodgate_raw task not found in floodgate_job_run_result")


@pytest.fixture(scope="session")
def floodgate_pipeline_task_result(floodgate_job_run_result: JobRunResult) -> TaskResult:
    """floodgate_job_run_resultからfloodgate_pipelineタスクの結果を抽出する。

    Args:
        floodgate_job_run_result: floodgate_job実行結果。

    Returns:
        TaskResult: floodgate_pipelineタスクの実行結果。
    """
    for task in floodgate_job_run_result.tasks:
        if task.task_key == "floodgate_pipeline":
            return task
    raise ValueError("floodgate_pipeline task not found in floodgate_job_run_result")


def test_floodgate_rawタスクが正常に完了する(floodgate_raw_task_result: TaskResult) -> None:
    """floodgate_rawタスクがSUCCESS状態で完了することを検証する。

    Arrange:
        floodgate_raw_task_resultフィクスチャからタスク結果を取得する。
    Act:
        result_stateを検証する。
    Assert:
        result_stateがSUCCESSであること。
    """
    # Assert
    assert floodgate_raw_task_result.result_state == "SUCCESS", (
        f"floodgate_raw task ended with result_state={floodgate_raw_task_result.result_state}, "
        f"message={floodgate_raw_task_result.state_message}"
    )


def test_floodgate_rawタスクのlife_cycle_stateがTERMINATEDである(
    floodgate_raw_task_result: TaskResult,
) -> None:
    """floodgate_rawタスクのlife_cycle_stateがTERMINATEDであることを検証する。

    Arrange:
        floodgate_raw_task_resultフィクスチャからタスク結果を取得する。
    Act:
        life_cycle_stateを検証する。
    Assert:
        life_cycle_stateがTERMINATEDであること。
    """
    # Assert
    assert floodgate_raw_task_result.life_cycle_state == "TERMINATED", (
        f"floodgate_raw task life_cycle_state should be TERMINATED, but got "
        f"{floodgate_raw_task_result.life_cycle_state}"
    )


def test_floodgate_rawタスクのrun_idが取得できている(floodgate_raw_task_result: TaskResult) -> None:
    """floodgate_rawタスクのrun_idが正常に取得できていることを検証する。

    Arrange:
        floodgate_raw_task_resultフィクスチャからタスク結果を取得する。
    Act:
        run_idを検証する。
    Assert:
        run_idがNoneではなく、正の整数であること。
    """
    # Assert
    assert floodgate_raw_task_result.run_id is not None, "floodgate_raw task run_id should not be None"
    assert floodgate_raw_task_result.run_id > 0, (
        f"floodgate_raw task run_id should be positive, got {floodgate_raw_task_result.run_id}"
    )


def test_floodgate_pipelineタスクが正常に完了する(floodgate_pipeline_task_result: TaskResult) -> None:
    """floodgate_pipelineタスクがSUCCESS状態で完了することを検証する。

    Arrange:
        floodgate_pipeline_task_resultフィクスチャからタスク結果を取得する。
    Act:
        result_stateを検証する。
    Assert:
        result_stateがSUCCESSであること。
    """
    # Assert
    assert floodgate_pipeline_task_result.result_state == "SUCCESS", (
        f"floodgate_pipeline task ended with result_state={floodgate_pipeline_task_result.result_state}, "
        f"message={floodgate_pipeline_task_result.state_message}"
    )


def test_floodgate_pipelineタスクのlife_cycle_stateがTERMINATEDである(
    floodgate_pipeline_task_result: TaskResult,
) -> None:
    """floodgate_pipelineタスクのlife_cycle_stateがTERMINATEDであることを検証する。

    Arrange:
        floodgate_pipeline_task_resultフィクスチャからタスク結果を取得する。
    Act:
        life_cycle_stateを検証する。
    Assert:
        life_cycle_stateがTERMINATEDであること。
    """
    # Assert
    assert floodgate_pipeline_task_result.life_cycle_state == "TERMINATED", (
        f"floodgate_pipeline task life_cycle_state should be TERMINATED, but got "
        f"{floodgate_pipeline_task_result.life_cycle_state}"
    )


def test_floodgate_pipelineタスクのrun_idが取得できている(floodgate_pipeline_task_result: TaskResult) -> None:
    """floodgate_pipelineタスクのrun_idが正常に取得できていることを検証する。

    Arrange:
        floodgate_pipeline_task_resultフィクスチャからタスク結果を取得する。
    Act:
        run_idを検証する。
    Assert:
        run_idがNoneではなく、正の整数であること。
    """
    # Assert
    assert floodgate_pipeline_task_result.run_id is not None, "floodgate_pipeline task run_id should not be None"
    assert floodgate_pipeline_task_result.run_id > 0, (
        f"floodgate_pipeline task run_id should be positive, got {floodgate_pipeline_task_result.run_id}"
    )


def test_floodgate出力テーブルにデータが存在する(floodgate_positions_df: DataFrame) -> None:
    """floodgate出力テーブル（Silver）にデータが存在することを検証する。

    Arrange:
        floodgate_positions_dfフィクスチャからDataFrameを取得する。
    Act:
        行数をカウントする。
    Assert:
        行数が0より大きいこと。
    """
    # Act
    row_count = floodgate_positions_df.count()

    # Assert
    assert row_count > 0, "floodgate_positions table should contain data"


def test_floodgate_position_featuresテーブルにデータが存在する(floodgate_position_features_df: DataFrame) -> None:
    """floodgate_position_featuresテーブル（Gold）にデータが存在することを検証する。

    Arrange:
        floodgate_position_features_dfフィクスチャからDataFrameを取得する。
    Act:
        行数をカウントする。
    Assert:
        行数が0より大きいこと。
    """
    # Act
    row_count = floodgate_position_features_df.count()

    # Assert
    assert row_count > 0, "floodgate_position_features table should contain data"
