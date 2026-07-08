"""Layer 3 (E2E) テスト用フィクスチャ。

DABs devターゲットへの実デプロイ（CD workflowで実施済み）を前提に、
Silver/Goldスキーマのクリーンアップとパイプライン起動・完了待機を行う。

spark, silver_pipeline_id, gold_pipeline_id は `tests/conftest.py`（ルート）で
定義されたものをそのまま利用する（本ファイルでの再定義は不要）。
"""

import json
import subprocess
import time
from dataclasses import dataclass

import pytest
from databricks.connect import DatabricksSession
from pyspark.sql import SparkSession

from tests.helpers.constants import TEST_CATALOG, TEST_GOLD_SCHEMA, TEST_SILVER_SCHEMA
from tests.helpers.expectations import _get_event_log_errors

# ポーリング設定。
_POLL_INTERVAL_SEC = 15
_POLL_TIMEOUT_SEC = 900


@pytest.fixture(scope="session")
def spark() -> SparkSession:
    """Databricks Connect経由のSparkSessionを提供する。

    `.databrickscfg` の DEFAULT プロファイルに設定されたServerless computeへ接続する。
    integration/e2eマーカー付きテストからのみ利用すること。

    Returns:
        接続済みのSparkSession。
    """
    return DatabricksSession.builder.profile("shogi").getOrCreate()


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


def _run_cli(args: list[str]) -> dict:
    """Databricks CLIをJSON出力モードで実行し、結果をパースして返す。

    Args:
        args: `databricks` に続くサブコマンド引数のリスト。

    Returns:
        CLI出力をJSONパースした辞書。
    """
    result = subprocess.run(
        ["databricks", *args, "--output", "json", "-p", "shogi"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(result.stdout)


def _drop_recreate_schema(catalog: str, schema: str) -> None:
    """Unity Catalogスキーマを削除・再作成する。

    MVを含むテーブルはLakeflowパイプライン実行時にタスクとして自動作成されるため、
    ここではスキーマの器のみを用意する。

    Args:
        catalog: 対象カタログ名。
        schema: 対象スキーマ名。
    """
    delete_result = subprocess.run(
        ["databricks", "schemas", "delete", f"{catalog}.{schema}", "-p", "shogi", "--force"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if delete_result.returncode != 0:
        # 「スキーマが存在しない」場合のみ許容し、それ以外は原因不明の失敗として扱う
        stderr = delete_result.stderr or ""
        if "does not exist" not in stderr and "NOT_FOUND" not in stderr:
            raise RuntimeError(
                f"schema delete failed unexpectedly for {catalog}.{schema}: "
                f"stdout={delete_result.stdout!r} stderr={stderr!r}"
            )

    subprocess.run(
        ["databricks", "schemas", "create", schema, catalog, "-p", "shogi"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )


def _start_pipeline_update(pipeline_id: str) -> str:
    """パイプライン更新を起動する。

    Args:
        pipeline_id: 対象パイプラインのID。

    Returns:
        起動したupdateのID。
    """
    response = _run_cli(["pipelines", "start-update", pipeline_id])
    return response["update_id"]


def _wait_for_update(
    spark: SparkSession, pipeline_id: str, update_id: str
) -> UpdateResult:
    """パイプライン更新がCOMPLETEDになるまでポーリングする。

    Args:
        spark: SparkSession（FAILED時のevent_log取得に使用）。
        pipeline_id: 対象パイプラインのID。
        update_id: 待機対象のupdate ID。

    Returns:
        COMPLETEDで終了した場合のUpdateResult。

    Raises:
        PipelineUpdateFailedError: FAILEDまたはCANCELEDで終了した場合。
            event_log()のERRORイベント詳細をメッセージに含める。
        TimeoutError: タイムアウト時間内に完了しなかった場合。
    """
    elapsed_sec = 0
    while elapsed_sec < _POLL_TIMEOUT_SEC:
        response = _run_cli(["pipelines", "get-update", pipeline_id, update_id])
        state = response["update"]["state"]

        if state == "COMPLETED":
            return UpdateResult(pipeline_id=pipeline_id, update_id=update_id, state=state)

        if state in ("FAILED", "CANCELED"):
            error_detail = _get_event_log_errors(spark, pipeline_id, update_id)
            raise PipelineUpdateFailedError(
                f"Pipeline update {update_id} (pipeline_id={pipeline_id}) "
                f"ended with state={state}\nevent_log errors:\n{error_detail}"
            )

        time.sleep(_POLL_INTERVAL_SEC)
        elapsed_sec += _POLL_INTERVAL_SEC

    raise TimeoutError(
        f"Pipeline update {update_id} (pipeline_id={pipeline_id}) "
        f"did not finish within {_POLL_TIMEOUT_SEC}s"
    )


@pytest.fixture(scope="session", autouse=True)
def clean_schemas() -> None:
    """E2Eテスト実行前にSilver/Goldスキーマをdrop & recreateする。

    テーブル・MVはLakeflowパイプライン実行時に自動作成されるため、
    ここではスキーマの器のみをクリーンな状態にする。
    """
    _drop_recreate_schema(TEST_CATALOG, TEST_SILVER_SCHEMA)
    _drop_recreate_schema(TEST_CATALOG, TEST_GOLD_SCHEMA)


@pytest.fixture(scope="session")
def silver_update_result(
    clean_schemas: None, spark: SparkSession, silver_pipeline_id: str
) -> UpdateResult:
    """Silverパイプラインを起動し、COMPLETEDになるまで待機した結果を提供する。"""
    update_id = _start_pipeline_update(silver_pipeline_id)
    return _wait_for_update(spark, silver_pipeline_id, update_id)


@pytest.fixture(scope="session")
def gold_update_result(
    silver_update_result: UpdateResult, spark: SparkSession, gold_pipeline_id: str
) -> UpdateResult:
    """Silver完了後にGoldパイプラインを起動し、COMPLETEDになるまで待機した結果を提供する。"""
    update_id = _start_pipeline_update(gold_pipeline_id)
    return _wait_for_update(spark, gold_pipeline_id, update_id)
