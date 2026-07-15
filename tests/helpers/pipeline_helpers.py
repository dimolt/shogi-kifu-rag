"""パイプライン操作用ヘルパー関数。

E2Eテストでのパイプライン起動・待機処理を集約する。
"""
import time

from helpers.databricks_cli import run_cli
from helpers.expectations import get_event_log_errors
from helpers.models import PipelineUpdateFailedError, UpdateResult
from pyspark.sql import SparkSession

# ポーリング設定
_POLL_INTERVAL_SEC = 15
_POLL_TIMEOUT_SEC = 900


def start_pipeline_update(pipeline_id: str) -> str:
    """パイプライン更新を起動する。

    Args:
        pipeline_id: 対象パイプラインのID。

    Returns:
        起動したupdateのID。
    """
    response = run_cli(["pipelines", "start-update", pipeline_id])
    return response["update_id"]


def wait_for_update(
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
        response = run_cli(["pipelines", "get-update", pipeline_id, update_id])
        state = response["update"]["state"]

        if state == "COMPLETED":
            return UpdateResult(pipeline_id=pipeline_id, update_id=update_id, state=state)

        if state in ("FAILED", "CANCELED"):
            error_detail = get_event_log_errors(spark, pipeline_id, update_id)
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
