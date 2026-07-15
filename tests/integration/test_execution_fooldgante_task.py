"""floodgateタスクの統合テスト。

floodgateタスクの実行と出力データを検証する。
Silverスキーマのデータを使用してfloodgate処理が正常に行われていることを確認する。

前提:
    本テストの実行前に、shogi_kif_rag_main_jobが実行され、
    floodgateタスクが正常に完了していること。
"""
import pytest
from pyspark.sql import DataFrame

from tests.helpers.models import JobRunResult, TaskResult

pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def floodgate_task_result(job_run_result: JobRunResult) -> TaskResult:
    """job_run_resultからfloodgateタスクの結果を抽出する。

    Args:
        job_run_result: Job実行結果。

    Returns:
        TaskResult: floodgateタスクの実行結果。
    """
    for task in job_run_result.tasks:
        if task.task_key == "floodgate":
            return task
    raise ValueError("floodgate task not found in job_run_result")


@pytest.fixture(scope="session")
def floodgate_output_df(spark, floodgate_positions_fqn: str) -> DataFrame:
    """floodgateタスクが出力したテーブルを読み込む。

    floodgateタスクが出力するテーブルのFQNを指定してDataFrameを返す。
    テーブル構造に応じて調整が必要。

    Args:
        spark: SparkSession。
        floodgate_positions_fqn: テーブル完全修飾名。

    Returns:
        DataFrame: floodgate出力テーブルのDataFrame。
    """
    return spark.table(floodgate_positions_fqn)


def test_floodgateタスクが正常に完了する(floodgate_task_result: TaskResult) -> None:
    """floodgateタスクがSUCCESS状態で完了することを検証する。

    Arrange:
        floodgate_task_resultフィクスチャからタスク結果を取得する。
    Act:
        result_stateを検証する。
    Assert:
        result_stateがSUCCESSであること。
    """
    # Assert
    assert floodgate_task_result.result_state == "SUCCESS", (
        f"floodgate task ended with result_state={floodgate_task_result.result_state}, "
        f"message={floodgate_task_result.state_message}"
    )


def test_floodgateタスクのlife_cycle_stateがTERMINATEDである(
    floodgate_task_result: TaskResult,
) -> None:
    """floodgateタスクのlife_cycle_stateがTERMINATEDであることを検証する。

    Arrange:
        floodgate_task_resultフィクスチャからタスク結果を取得する。
    Act:
        life_cycle_stateを検証する。
    Assert:
        life_cycle_stateがTERMINATEDであること。
    """
    # Assert
    assert floodgate_task_result.life_cycle_state == "TERMINATED", (
        f"floodgate task life_cycle_state should be TERMINATED, but got "
        f"{floodgate_task_result.life_cycle_state}"
    )


def test_floodgateタスクのrun_idが取得できている(floodgate_task_result: TaskResult) -> None:
    """floodgateタスクのrun_idが正常に取得できていることを検証する。

    Arrange:
        floodgate_task_resultフィクスチャからタスク結果を取得する。
    Act:
        run_idを検証する。
    Assert:
        run_idがNoneではなく、正の整数であること。
    """
    # Assert
    assert floodgate_task_result.run_id is not None, "floodgate task run_id should not be None"
    assert floodgate_task_result.run_id > 0, (
        f"floodgate task run_id should be positive, got {floodgate_task_result.run_id}"
    )


def test_floodgate出力テーブルにデータが存在する(floodgate_output_df: DataFrame) -> None:
    """floodgate出力テーブルにデータが存在することを検証する。

    Arrange:
        floodgate_output_dfフィクスチャからDataFrameを取得する。
    Act:
        行数をカウントする。
    Assert:
        行数が0より大きいこと。
    """
    # Act
    row_count = floodgate_output_df.count()

    # Assert
    assert row_count > 0, "floodgate output table should contain data"


# TODO: floodgateタスクの出力構造が確定したら、以下のテストを実装する
# def test_floodgate出力テーブルのスキーマが仕様通りである(floodgate_output_df: DataFrame) -> None:
#     """floodgate出力テーブルのスキーマが仕様通りであることを検証する。"""
#     pass
#
# def test_floodgate出力テーブルのデータ整合性(floodgate_output_df: DataFrame) -> None:
#     """floodgate出力テーブルのデータ整合性を検証する。"""
#     pass
