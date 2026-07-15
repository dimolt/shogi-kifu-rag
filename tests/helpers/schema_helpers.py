"""Unity Catalogスキーマ操作用ヘルパー関数。

E2Eテストでのスキーマクリーンアップ処理を集約する。
"""
import subprocess

from tests.helpers.databricks_cli import databricks_cli_base_args


def drop_recreate_schema(catalog: str, schema: str) -> None:
    """Unity Catalogスキーマを削除・再作成する。

    MVを含むテーブルはLakeflowパイプライン実行時にタスクとして自動作成されるため、
    ここではスキーマの器のみを用意する。

    Args:
        catalog: 対象カタログ名。
        schema: 対象スキーマ名。
    """
    delete_result = subprocess.run(
        ["databricks", "schemas", "delete", f"{catalog}.{schema}", *databricks_cli_base_args(), "--force"],
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
        ["databricks", "schemas", "create", schema, catalog, *databricks_cli_base_args()],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
