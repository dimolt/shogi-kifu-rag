"""wikipediaタスクの統合テスト。

wikipediaタスクの実行と出力データを検証する。
Silverスキーマのデータを使用してwikipedia処理が正常に行われていることを確認する。

前提:
    本テストの実行前に、shogi_kif_rag_main_jobが実行され、
    wikipediaタスクが正常に完了していること。
"""
import pytest
from pyspark.sql import DataFrame

from tests.helpers.models import JobRunResult, TaskResult

pytestmark = pytest.mark.integration_exec


@pytest.fixture(scope="session")
def wikipedia_task_result(job_run_result: JobRunResult) -> TaskResult:
    """job_run_resultからwikipediaタスクの結果を抽出する。

    Args:
        job_run_result: Job実行結果。

    Returns:
        TaskResult: wikipediaタスクの実行結果。
    """
    for task in job_run_result.tasks:
        if task.task_key == "wikipedia":
            return task
    raise ValueError("wikipedia task not found in job_run_result")


def test_wikipediaタスクが正常に完了する(wikipedia_task_result: TaskResult) -> None:
    """wikipediaタスクがSUCCESS状態で完了することを検証する。

    Arrange:
        wikipedia_task_resultフィクスチャからタスク結果を取得する。
    Act:
        result_stateを検証する。
    Assert:
        result_stateがSUCCESSであること。
    """
    # Assert
    assert wikipedia_task_result.result_state == "SUCCESS", (
        f"wikipedia task ended with result_state={wikipedia_task_result.result_state}, "
        f"message={wikipedia_task_result.state_message}"
    )


def test_wikipediaタスクのlife_cycle_stateがTERMINATEDである(
    wikipedia_task_result: TaskResult,
) -> None:
    """wikipediaタスクのlife_cycle_stateがTERMINATEDであることを検証する。

    Arrange:
        wikipedia_task_resultフィクスチャからタスク結果を取得する。
    Act:
        life_cycle_stateを検証する。
    Assert:
        life_cycle_stateがTERMINATEDであること。
    """
    # Assert
    assert wikipedia_task_result.life_cycle_state == "TERMINATED", (
        f"wikipedia task life_cycle_state should be TERMINATED, but got "
        f"{wikipedia_task_result.life_cycle_state}"
    )


def test_wikipediaタスクのrun_idが取得できている(wikipedia_task_result: TaskResult) -> None:
    """wikipediaタスクのrun_idが正常に取得できていることを検証する。

    Arrange:
        wikipedia_task_resultフィクスチャからタスク結果を取得する。
    Act:
        run_idを検証する。
    Assert:
        run_idがNoneではなく、正の整数であること。
    """
    # Assert
    assert wikipedia_task_result.run_id is not None, "wikipedia task run_id should not be None"
    assert wikipedia_task_result.run_id > 0, (
        f"wikipedia task run_id should be positive, got {wikipedia_task_result.run_id}"
    )


def test_wikipedia出力テーブルにデータが存在する(joseki_knowledge_df: DataFrame) -> None:
    """wikipedia出力テーブルにデータが存在することを検証する。

    Arrange:
        wikipedia_output_dfフィクスチャからDataFrameを取得する。
    Act:
        行数をカウントする。
    Assert:
        行数が0より大きいこと。
    """
    # Act
    row_count = joseki_knowledge_df.count()

    # Assert
    assert row_count > 0, "wikipedia output table should contain data"


# TODO: wikipediaタスクの出力構造が確定したら、以下のテストを実装する
# def test_wikipedia出力テーブルのスキーマが仕様通りである(wikipedia_output_df: DataFrame) -> None:
#     """wikipedia出力テーブルのスキーマが仕様通りであることを検証する。"""
#     pass
#
# def test_wikipedia出力テーブルのデータ整合性(wikipedia_output_df: DataFrame) -> None:
#     """wikipedia出力テーブルのデータ整合性を検証する。"""
#     pass
