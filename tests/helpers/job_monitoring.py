"""Databricks SDKを使用したJob実行監視ヘルパー。

tests/e2e層から、Databricks Jobの実行完了をポーリングし、Job全体および
タスク単位の実行結果を構造化して返す。パイプライン更新の監視
（tests/e2e/conftest.py の `_wait_for_update`）と同様のポーリング方式を採用しつつ、
Databricks CLI subprocessではなくDatabricks SDK（WorkspaceClient）を直接使用する。
"""

from __future__ import annotations

import time

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import Run, RunLifeCycleState, RunResultState
from helpers.models import JobRunFailedError, JobRunResult, TaskResult

# ポーリング設定のデフォルト値。
_DEFAULT_POLL_INTERVAL_SEC = 15
_DEFAULT_POLL_TIMEOUT_SEC = 900

# Run/タスクの実行が終了したとみなすlife_cycle_state。
_TERMINAL_LIFE_CYCLE_STATES = (
    RunLifeCycleState.TERMINATED,
    RunLifeCycleState.SKIPPED,
    RunLifeCycleState.INTERNAL_ERROR,
)


class JobMonitor:
    """Databricks SDKを使用してJob実行の完了を監視するクラス。

    Databricks CLI subprocessの代わりにDatabricks SDK（WorkspaceClient）の
    `jobs.get_run` APIを直接呼び出すことで、CLI起動オーバーヘッドを避けつつ
    型付きのレスポンスを扱う。
    """

    def __init__(
        self,
        client: WorkspaceClient,
        poll_interval_sec: int = _DEFAULT_POLL_INTERVAL_SEC,
        timeout_sec: int = _DEFAULT_POLL_TIMEOUT_SEC,
    ) -> None:
        """JobMonitorを初期化する。

        Args:
            client: Job実行状態の取得に使用するWorkspaceClient。
            poll_interval_sec: ポーリング間隔（秒）。デフォルトは15秒。
            timeout_sec: 完了待機のタイムアウト（秒）。デフォルトは900秒。
        """
        self._client = client
        self._poll_interval_sec = poll_interval_sec
        self._timeout_sec = timeout_sec

    def wait_for_completion(self, run_id: int) -> JobRunResult:
        """Job実行が終了状態になるまでポーリングし、結果を返す。

        Args:
            run_id: 待機対象のJob実行ID。

        Returns:
            SUCCESSで終了した場合のJobRunResult。

        Raises:
            JobRunFailedError: result_stateがSUCCESS以外で終了した場合。
                失敗したタスクの詳細をメッセージに含める。
            TimeoutError: タイムアウト時間内に終了状態に到達しなかった場合。
        """
        elapsed_sec = 0
        while elapsed_sec < self._timeout_sec:
            run = self._client.jobs.get_run(run_id)

            if (
                run.state is not None
                and run.state.life_cycle_state in _TERMINAL_LIFE_CYCLE_STATES
            ):
                return self._parse_result(run)

            time.sleep(self._poll_interval_sec)
            elapsed_sec += self._poll_interval_sec

        raise TimeoutError(
            f"Job run {run_id} did not finish within {self._timeout_sec}s"
        )

    def _parse_result(self, run: Run) -> JobRunResult:
        """終了状態のRunをJobRunResultに変換する。

        Args:
            run: 終了状態（life_cycle_stateがTERMINATED等）のRun。

        Returns:
            JobRunResult: Job全体の結果とタスク単位の結果一覧。

        Raises:
            JobRunFailedError: result_stateがSUCCESS以外の場合。
                失敗したタスクの詳細をメッセージに含める。
        """
        state = run.state
        life_cycle_state = (
            state.life_cycle_state.value if state.life_cycle_state else "UNKNOWN"
        )
        result_state = state.result_state.value if state.result_state else None
        task_results = self._get_task_results(run)

        job_result = JobRunResult(
            run_id=run.run_id,
            job_id=run.job_id,
            life_cycle_state=life_cycle_state,
            result_state=result_state,
            state_message=state.state_message,
            tasks=task_results,
        )

        if state.result_state != RunResultState.SUCCESS:
            failed_tasks = [
                task
                for task in task_results
                if task.result_state != RunResultState.SUCCESS.value
            ]
            failed_detail = "\n".join(
                f"  - {task.task_key}: result_state={task.result_state}, message={task.state_message}"
                for task in failed_tasks
            )
            raise JobRunFailedError(
                f"Job run {run.run_id} (job_id={run.job_id}) ended with "
                f"result_state={result_state}\nfailed tasks:\n{failed_detail}"
            )

        return job_result

    def _get_task_results(self, run: Run) -> list[TaskResult]:
        """RunからJob内の各タスクの実行結果一覧を抽出する。

        Args:
            run: 対象のRun。

        Returns:
            list[TaskResult]: 各タスクの実行結果。tasksが存在しない場合は空リスト。
        """
        if not run.tasks:
            return []

        task_results = []
        for task in run.tasks:
            task_state = task.state
            life_cycle_state = (
                task_state.life_cycle_state.value
                if task_state and task_state.life_cycle_state
                else "UNKNOWN"
            )
            result_state = (
                task_state.result_state.value
                if task_state and task_state.result_state
                else None
            )
            task_results.append(
                TaskResult(
                    task_key=task.task_key,
                    run_id=task.run_id,
                    life_cycle_state=life_cycle_state,
                    result_state=result_state,
                    state_message=task_state.state_message if task_state else None,
                )
            )
        return task_results
