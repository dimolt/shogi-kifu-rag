"""josekiタスクの統合テスト。

josekiタスクの実行と出力データを検証する。
Silver/Goldスキーマのデータを使用してjoseki処理が正常に行われていることを確認する。

前提:
    本テストの実行前に、joseki_jobが実行され、
    josekiタスクが正常に完了していること。
"""
import pytest
from pyspark.sql import DataFrame

from tests.helpers.models import JobRunResult, TaskResult

pytestmark = [pytest.mark.integration, pytest.mark.normal]


@pytest.fixture(scope="session")
def wikipedia_raw_task_result(joseki_job_run_result: JobRunResult) -> TaskResult:
    """joseki_job_run_resultからwikipedia_rawタスクの結果を抽出する。

    Args:
        joseki_job_run_result: joseki_job実行結果。

    Returns:
        TaskResult: wikipedia_rawタスクの実行結果。
    """
    for task in joseki_job_run_result.tasks:
        if task.task_key == "wikipedia_raw":
            return task
    raise ValueError("wikipedia_raw task not found in joseki_job_run_result")


@pytest.fixture(scope="session")
def joseki_pipeline_task_result(joseki_job_run_result: JobRunResult) -> TaskResult:
    """joseki_job_run_resultからjoseki_pipelineタスクの結果を抽出する。

    Args:
        joseki_job_run_result: joseki_job実行結果。

    Returns:
        TaskResult: joseki_pipelineタスクの実行結果。
    """
    for task in joseki_job_run_result.tasks:
        if task.task_key == "joseki_pipeline":
            return task
    raise ValueError("joseki_pipeline task not found in joseki_job_run_result")


def test_wikipedia_rawタスクが正常に完了する(wikipedia_raw_task_result: TaskResult) -> None:
    """wikipedia_rawタスクがSUCCESS状態で完了することを検証する。

    Arrange:
        wikipedia_raw_task_resultフィクスチャからタスク結果を取得する。
    Act:
        result_stateを検証する。
    Assert:
        result_stateがSUCCESSであること。
    """
    # Assert
    assert wikipedia_raw_task_result.result_state == "SUCCESS", (
        f"wikipedia_raw task ended with result_state={wikipedia_raw_task_result.result_state}, "
        f"message={wikipedia_raw_task_result.state_message}"
    )


def test_wikipedia_rawタスクのlife_cycle_stateがTERMINATEDである(
    wikipedia_raw_task_result: TaskResult,
) -> None:
    """wikipedia_rawタスクのlife_cycle_stateがTERMINATEDであることを検証する。

    Arrange:
        wikipedia_raw_task_resultフィクスチャからタスク結果を取得する。
    Act:
        life_cycle_stateを検証する。
    Assert:
        life_cycle_stateがTERMINATEDであること。
    """
    # Assert
    assert wikipedia_raw_task_result.life_cycle_state == "TERMINATED", (
        f"wikipedia_raw task life_cycle_state should be TERMINATED, but got "
        f"{wikipedia_raw_task_result.life_cycle_state}"
    )


def test_wikipedia_rawタスクのrun_idが取得できている(wikipedia_raw_task_result: TaskResult) -> None:
    """wikipedia_rawタスクのrun_idが正常に取得できていることを検証する。

    Arrange:
        wikipedia_raw_task_resultフィクスチャからタスク結果を取得する。
    Act:
        run_idを検証する。
    Assert:
        run_idがNoneではなく、正の整数であること。
    """
    # Assert
    assert wikipedia_raw_task_result.run_id is not None, "wikipedia_raw task run_id should not be None"
    assert wikipedia_raw_task_result.run_id > 0, (
        f"wikipedia_raw task run_id should be positive, got {wikipedia_raw_task_result.run_id}"
    )


def test_joseki_pipelineタスクが正常に完了する(joseki_pipeline_task_result: TaskResult) -> None:
    """joseki_pipelineタスクがSUCCESS状態で完了することを検証する。

    Arrange:
        joseki_pipeline_task_resultフィクスチャからタスク結果を取得する。
    Act:
        result_stateを検証する。
    Assert:
        result_stateがSUCCESSであること。
    """
    # Assert
    assert joseki_pipeline_task_result.result_state == "SUCCESS", (
        f"joseki_pipeline task ended with result_state={joseki_pipeline_task_result.result_state}, "
        f"message={joseki_pipeline_task_result.state_message}"
    )


def test_joseki_pipelineタスクのlife_cycle_stateがTERMINATEDである(
    joseki_pipeline_task_result: TaskResult,
) -> None:
    """joseki_pipelineタスクのlife_cycle_stateがTERMINATEDであることを検証する。

    Arrange:
        joseki_pipeline_task_resultフィクスチャからタスク結果を取得する。
    Act:
        life_cycle_stateを検証する。
    Assert:
        life_cycle_stateがTERMINATEDであること。
    """
    # Assert
    assert joseki_pipeline_task_result.life_cycle_state == "TERMINATED", (
        f"joseki_pipeline task life_cycle_state should be TERMINATED, but got "
        f"{joseki_pipeline_task_result.life_cycle_state}"
    )


def test_joseki_pipelineタスクのrun_idが取得できている(joseki_pipeline_task_result: TaskResult) -> None:
    """joseki_pipelineタスクのrun_idが正常に取得できていることを検証する。

    Arrange:
        joseki_pipeline_task_resultフィクスチャからタスク結果を取得する。
    Act:
        run_idを検証する。
    Assert:
        run_idがNoneではなく、正の整数であること。
    """
    # Assert
    assert joseki_pipeline_task_result.run_id is not None, "joseki_pipeline task run_id should not be None"
    assert joseki_pipeline_task_result.run_id > 0, (
        f"joseki_pipeline task run_id should be positive, got {joseki_pipeline_task_result.run_id}"
    )


def test_joseki_knowledgeテーブルにデータが存在する(joseki_knowledge_df: DataFrame) -> None:
    """joseki_knowledgeテーブル（Silver）にデータが存在することを検証する。

    Arrange:
        joseki_knowledge_dfフィクスチャからDataFrameを取得する。
    Act:
        行数をカウントする。
    Assert:
        行数が0より大きいこと。
    """
    # Act
    row_count = joseki_knowledge_df.count()

    # Assert
    assert row_count > 0, "joseki_knowledge table should contain data"


def test_joseki_featuresテーブルにデータが存在する(joseki_features_df: DataFrame) -> None:
    """joseki_featuresテーブル（Gold）にデータが存在することを検証する。

    Arrange:
        joseki_features_dfフィクスチャからDataFrameを取得する。
    Act:
        行数をカウントする。
    Assert:
        行数が0より大きいこと。
    """
    # Act
    row_count = joseki_features_df.count()

    # Assert
    assert row_count > 0, "joseki_features table should contain data"
