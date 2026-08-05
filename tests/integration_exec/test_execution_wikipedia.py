"""wikipedia_rawタスクの統合テスト。

wikipedia_raw（Bronze層）タスクの実行と出力データを検証する。
Bronzeスキーマのデータを使用してwikipedia処理が正常に行われていることを確認する。

注意:
    joseki_knowledgeはLakeflowパイプライン（silver_pipeline）に移行したため、
    このファイルではwikipedia_rawタスクのみをテストする。
    joseki_knowledge/joseki_featuresはパイプライン統合テストで検証する。

前提:
    本テストの実行前に、shogi_kif_rag_main_jobが実行され、
    wikipedia_rawタスクが正常に完了していること。
"""
import pytest
from pyspark.sql import DataFrame

from tests.helpers.models import JobRunResult, TaskResult

pytestmark = pytest.mark.integration_exec


@pytest.fixture(scope="session")
def wikipedia_raw_task_result(job_run_result: JobRunResult) -> TaskResult:
    """job_run_resultからwikipedia_rawタスクの結果を抽出する。

    Args:
        job_run_result: Job実行結果。

    Returns:
        TaskResult: wikipedia_rawタスクの実行結果。
    """
    for task in job_run_result.tasks:
        if task.task_key == "wikipedia_raw":
            return task
    raise ValueError("wikipedia_raw task not found in job_run_result")


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


def test_wikipedia_raw出力テーブルにデータが存在する(wikipedia_raw_df: DataFrame) -> None:
    """wikipedia_raw出力テーブルにデータが存在することを検証する。

    Arrange:
        wikipedia_raw_dfフィクスチャからDataFrameを取得する。
    Act:
        行数をカウントする。
    Assert:
        行数が0より大きいこと。
    """
    # Act
    row_count = wikipedia_raw_df.count()

    # Assert
    assert row_count > 0, "wikipedia_raw table should contain data"


# TODO: タスクの出力構造が確定したら、以下のテストを実装する
# def test_wikipedia_raw出力テーブルのスキーマが仕様通りである(wikipedia_raw_df: DataFrame) -> None:
#     """wikipedia_raw出力テーブルのスキーマが仕様通りであることを検証する。"""
#     pass
#
# def test_wikipedia_raw出力テーブルのデータ整合性(wikipedia_raw_df: DataFrame) -> None:
#     """wikipedia_raw出力テーブルのデータ整合性を検証する。"""
#     pass
