"""Resource系異常系テスト（Issue #208）。

前提条件:
    - このテストは対象Jobを実際に並行起動する。
    - Jobの並行実行挙動を検証する。
    - テスト実行前にJobがdevターゲットへデプロイされていること。
"""
import pytest
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import RunLifeCycleState

from tests.helpers.monitoring.job_monitoring import JobMonitor

pytestmark = pytest.mark.integration_exec


def test_job並行実行時の挙動を検証する(
    workspace_client: WorkspaceClient,
    job_id: int,
) -> None:
    """Issue #208: 同一Jobを並行起動した場合の挙動を検証する。

    Arrange:
        同一job_idを使用して2つのJob実行をほぼ同時に起動する。
    Act:
        両方の実行を並行して監視し、完了状態を確認する。
    Assert:
        並行実行時の挙動が明文化されていること（エラーになるか、キューイングされるか）。
        少なくとも一方の実行が正常に完了すること、または
        適切なエラー処理が行われていることを確認する。

    Note:
        Databricks Jobのデフォルト挙動では、同一Jobの並行実行が許可される場合と、
        キューイングされる場合がある。このテストで実際の挙動を確認し、
        結果に基づいてドキュメントを更新する。
    """
    # Arrange: 同一Jobを2回並行起動
    run1 = workspace_client.jobs.run_now(job_id=job_id)
    run2 = workspace_client.jobs.run_now(job_id=job_id)

    monitor = JobMonitor(workspace_client)

    # Act: 両方の実行を監視
    try:
        result1 = monitor.wait_for_completion(run1.run_id)
        result2 = monitor.wait_for_completion(run2.run_id)
    except Exception as e:
        # 並行実行時にエラーが発生する場合の挙動を記録
        pytest.fail(f"並行実行時にエラーが発生: {e}")

    # Assert: 少なくとも一方が成功していることを確認
    # （Databricksの設定によっては、片方がキャンセルされる可能性がある）
    success_count = 0
    for result in [result1, result2]:
        if result.result_state == "SUCCESS":
            success_count += 1
        elif result.life_cycle_state == RunLifeCycleState.TERMINATED.value:
            # TERMINATEDだがresult_stateがSUCCESSでない場合の挙動を確認
            pass

    # 並行実行の挙動に基づいてアサーションを調整
    # デフォルトでは両方成功するか、片方がキューイングされる
    assert success_count >= 1, (
        f"並行実行時に少なくとも1つのJobが成功する必要があります。"
        f"run1: {result1.result_state}, run2: {result2.result_state}"
    )

    # 挙動のドキュメント化（テスト出力に挙動を記録）
    print("\n並行実行挙動:")
    print(f"  run1: life_cycle_state={result1.life_cycle_state}, result_state={result1.result_state}")
    print(f"  run2: life_cycle_state={result2.life_cycle_state}, result_state={result2.result_state}")
