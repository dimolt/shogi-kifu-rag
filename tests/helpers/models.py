"""E2Eパイプライン更新処理で使う共通の型定義。

tests/e2e/conftest.py と tests/e2e/test_e2e_pipeline.py の双方から参照される。
テストコードがconftest.pyから直接importする構造を避けるため、本モジュールに切り出す。
"""

from dataclasses import dataclass


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
