"""E2Eパイプライン更新処理で使う共通の型定義。

tests/e2e/conftest.py と tests/e2e/test_e2e_pipeline.py の双方から参照される。
テストコードがconftest.pyから直接importする構造を避けるため、本モジュールに切り出す。
"""

from dataclasses import dataclass
from pathlib import Path


class JobRunFailedError(Exception):
    """Job実行がSUCCESS以外のresult_stateで終了した場合の例外。"""

class PipelineUpdateFailedError(Exception):
    """パイプライン更新がFAILED/CANCELEDで終了した場合の例外。"""


@dataclass
class UpdateResult:
    """パイプライン更新の完了結果。

    Attributes:
        pipeline_id: 対象パイプラインのID。
        update_id: 完了したupdateのID。
        state: 最終状態（常にCOMPLETED。それ以外は例外送出のため保持しない）。
    """

    pipeline_id: str
    update_id: str
    state: str


@dataclass
class TaskResult:
    """Job実行内の単一タスクの完了結果。

    Attributes:
        task_key: タスクキー（databricks.yml/jobs.ymlで定義したtask_key）。
        run_id: タスク単位の実行ID。
        life_cycle_state: タスクのライフサイクル状態
            （例: "TERMINATED"）。取得できない場合は"UNKNOWN"。
        result_state: タスクの結果状態（例: "SUCCESS", "FAILED"）。
            終了状態でない場合はNone。
        state_message: 状態に関する補足メッセージ。存在しない場合はNone。
    """

    task_key: str
    run_id: int | None
    life_cycle_state: str
    result_state: str | None
    state_message: str | None


@dataclass
class JobRunResult:
    """Job実行全体の完了結果。

    Attributes:
        run_id: 対象Job実行のID。
        job_id: 対象JobのID。取得できない場合はNone。
        life_cycle_state: Run全体のライフサイクル状態（例: "TERMINATED"）。
        result_state: Run全体の結果状態（例: "SUCCESS", "FAILED"）。
        state_message: 状態に関する補足メッセージ。存在しない場合はNone。
        tasks: タスク単位の実行結果一覧。
    """

    run_id: int
    job_id: int | None
    life_cycle_state: str
    result_state: str | None
    state_message: str | None
    tasks: list[TaskResult]


@dataclass(frozen=True)
class TestDataScenarioConfig:
    """1テストシナリオ分のテストデータ設定。

    Attributes:
        kif_path: 変換元KIFファイルのローカルパス。
        csv_path: 生成先CSVファイルのローカルパス（tests/scripts/setup_test_data_volume.py
            が生成し、Volumeにアップロードする対象）。
        volume_path: Volume上のアップロード先ディレクトリパス。
        expected_game_count: このシナリオに含まれる対局数。
        expected_row_count: 生成されるCSVの期待行数（ヘッダを除いた局面数）。
    """

    kif_path: Path
    csv_path: Path
    volume_path: str
    expected_game_count: int
    expected_row_count: int
