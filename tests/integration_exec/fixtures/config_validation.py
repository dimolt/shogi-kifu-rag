"""Configuration系異常系テスト（Issue #211）用の共通ヘルパー。

`databricks bundle validate`を任意のtargetで実行し、解決済み変数を取得するための
薄いラッパーを提供する。Issue #209はデプロイを伴わない設計に変更したため、
既存の`job_id`/`workspace_client`フィクスチャ（tests/integration_exec/fixtures/job_execution.py）
をそのまま利用し、本モジュールには依存しない。
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from tests.helpers.databricks.cli import databricks_cli_base_args


def run_bundle_validate_json(target: str, cwd: Path | None = None) -> dict:
    """`databricks bundle validate --output json`を実行し、解決済み設定を返す。

    成功する前提のコマンド（Issue #211: 環境別の変数解決確認）で使用する。

    Args:
        target: 検証対象のBundle target。
        cwd: 実行ディレクトリ。Noneの場合はカレントディレクトリ（プロジェクトルート想定）。

    Returns:
        dict: `bundle validate`のJSON出力全体（`resources`, `variables`等を含む）。

    Raises:
        subprocess.CalledProcessError: コマンドが失敗した場合。
    """
    args = [
        "databricks",
        "bundle",
        "validate",
        "-t",
        target,
        "--output",
        "json",
        *databricks_cli_base_args(),
    ]
    result = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(result.stdout)
