"""Resource系異常系テスト（Issue #208）。

前提条件:
    - このテストは対象Jobを実際に並行起動する。
    - Jobの並行実行挙動を検証する。
    - テスト実行前にJobがdevターゲットへデプロイされていること。
"""
import pytest
from databricks.sdk import WorkspaceClient

from tests.helpers.monitoring.job_monitoring import JobMonitor

pytestmark = [pytest.mark.integration, pytest.mark.abnormal]


def test_job並行実行時の挙動を検証する(
    workspace_client: WorkspaceClient,
    job_id: int,
) -> None:
    """Issue #208: 同一Jobを並行起動した場合の挙動を検証する。

    Arrange:
        同一job_idを使用して2つのJob実行をほぼ同時に起動する。
    Act:
        両方の実行を並行して監視し、完了状態(または例外)を収集する。
    Assert:
        Job設定は Queue: OFF (max_concurrent_runs=1) であるため、
        後発の実行は MAXIMUM_CONCURRENT_RUNS_REACHED でスキップされ、
        それに依存するタスクは UPSTREAM_FAILED となって全体が失敗する。
        先発の実行は正常に完了する。

    Note:
        Queue: OFF の設定下では、並行実行時に一方が確実に
        MAXIMUM_CONCURRENT_RUNS_REACHED で失敗することが期待される挙動である。
        キューイングして両方成功させたい場合はJob設定を Queue: ON に戻すこと。

        また、Workspaceレベルの上限（active runs limit）に達した場合、
        RequestLimitExceeded が発生する可能性があり、これも同様に並行実行制限
        による失敗として扱う。
    """
    # Arrange: 同一Jobを2回並行起動
    # RequestLimitExceededを即座にキャッチしてリトライを回避
    run1 = workspace_client.jobs.run_now(job_id=job_id)
    try:
        run2 = workspace_client.jobs.run_now(job_id=job_id)
    # except RequestLimitExceeded as e:
    except Exception as e:
        # Workspaceレベルの上限に達した場合も、並行実行制限として扱う
        run2 = None
        run2_error = e

    monitor = JobMonitor(workspace_client)

    # Act: 例外を握りつぶさず、結果の一部として収集する
    outcomes: dict[int, object] = {}

    # run1の監視
    try:
        outcomes[run1.run_id] = monitor.wait_for_completion(run1.run_id)
    except Exception as e:  # noqa: BLE001
        outcomes[run1.run_id] = e

    # run2の監視（起動に失敗した場合はエラーをそのまま記録）
    if run2 is not None:
        try:
            outcomes[run2.run_id] = monitor.wait_for_completion(run2.run_id)
        except Exception as e:  # noqa: BLE001
            outcomes[run2.run_id] = e
    else:
        # run2の起動自体が失敗した場合、ダミーのrun_idを使用してエラーを記録
        outcomes[-1] = run2_error

    # Assert: Queue: OFF (max_concurrent_runs=1) のため、
    # 一方は成功し、もう一方は並行実行制限で失敗するはず
    succeeded = [
        run_id
        for run_id, outcome in outcomes.items()
        if not isinstance(outcome, Exception) and outcome.result_state == "SUCCESS"
    ]
    failed = [
        (run_id, outcome)
        for run_id, outcome in outcomes.items()
        if isinstance(outcome, Exception)
    ]

    assert len(succeeded) == 1, (
        f"Queue: OFF 設定下では並行実行のうち1件のみが成功するはず: {outcomes}"
    )
    assert len(failed) == 1, (
        f"Queue: OFF 設定下では並行実行のうち1件は "
        f"並行実行制限で失敗するはず: {outcomes}"
    )

    failed_run_id, failed_exception = failed[0]
    # MAXIMUM_CONCURRENT_RUNS_REACHED または RequestLimitExceeded のいずれかを許容
    error_str = str(failed_exception)
    assert (
        "MAXIMUM_CONCURRENT_RUNS_REACHED" in error_str
        or "RequestLimitExceeded" in error_str
        or "active runs" in error_str.lower()
        or "timed out" in error_str.lower()
    ), (
        f"失敗した実行(run_id={failed_run_id})の原因は "
        f"並行実行制限であるはず: {failed_exception}"
    )

    # 挙動のドキュメント化 (テスト出力に記録)
    print("\n並行実行挙動 (Queue: OFF):")
    for run_id, outcome in outcomes.items():
        if isinstance(outcome, Exception):
            print(f"  run_id={run_id}: FAILED - {outcome}")
        else:
            print(f"  run_id={run_id}: result_state={outcome.result_state}")
