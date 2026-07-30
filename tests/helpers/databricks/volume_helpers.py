"""Databricks Volume操作の共通ヘルパー関数。"""

import io
import os
from pathlib import Path

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors.platform import NotFound


def _get_workspace_client() -> WorkspaceClient:
    """WorkspaceClientインスタンスを取得する。"""
    profile = os.environ.get("DATABRICKS_CONFIG_PROFILE", "shogi")
    return WorkspaceClient(profile=profile)


def get_test_data_volume_path(catalog: str) -> str:
    """テストデータ用Volumeパスを取得する。

    Args:
        catalog: カタログ名（shogi_dev/shogi_test/shogi）。

    Returns:
        テストデータ用Volumeパス（/Volumes/{catalog}/test/data）。
    """
    return f"/Volumes/{catalog}/test/data"


def get_landing_volume_path(catalog: str, schema: str = "landing") -> str:
    """Landing Volumeパスを取得する。

    Args:
        catalog: カタログ名（shogi_dev/shogi_test/shogi）。
        schema: スキーマ名（デフォルト: "landing"）。

    Returns:
        Landing Volumeパス（/Volumes/{catalog}/{schema}/analyzed）。
    """
    return f"/Volumes/{catalog}/{schema}/analyzed"


def upload_csv_to_volume(local_path: Path, volume_path: str, filename: str) -> None:
    """CSVをUnity Catalog Volumeにアップロードする。

    Args:
        local_path: ローカルのCSVファイルパス。
        volume_path: アップロード先のVolumeディレクトリパス。
        filename: Volume上のファイル名。
    """
    w = _get_workspace_client()
    remote_path = f"{volume_path}/{filename}"
    with local_path.open("rb") as f:
        w.files.upload(remote_path, f, overwrite=True)


def cleanup_volume_files(volume_path: str, pattern: str) -> None:
    """Volume上のテスト用ファイルを削除する。

    Args:
        volume_path: Volumeディレクトリパス。
        pattern: 削除対象のファイルパターン。

    Raises:
        Exception: Volumeが存在しない場合以外の例外は再送出する。
    """
    w = _get_workspace_client()
    try:
        # ページングされたイテレータを先にリスト化して削除中のオフセットずれを防ぐ
        files = list(w.files.list_directory_contents(volume_path))
    except NotFound:
        # Volumeが存在しない場合は何もしない
        return

    for file_info in files:
        if pattern in file_info.path:
            w.files.delete(file_info.path)


def backup_csv_files(volume_path: str) -> dict[str, bytes]:
    """Volume上のCSVファイルをバックアップする。

    Args:
        volume_path: Volumeディレクトリパス。

    Returns:
        ファイルパスと内容のマッピング。

    Raises:
        Exception: Volumeが存在しない場合以外の例外は再送出する。
    """
    w = _get_workspace_client()
    backup: dict[str, bytes] = {}
    try:
        # ページングされたイテレータを先にリスト化してオフセットずれを防ぐ
        files = list(w.files.list_directory_contents(volume_path))
        for file_info in files:
            if file_info.path.endswith(".csv"):
                content = w.files.download(file_info.path).contents.read()
                backup[file_info.path] = content
    except NotFound:
        # Volumeが存在しない場合は空のバックアップを返す
        pass
    return backup


def restore_csv_files(volume_path: str, backup: dict[str, bytes]) -> None:
    """バックアップしたCSVファイルを復元する。

    Args:
        volume_path: Volumeディレクトリパス。
        backup: ファイルパスと内容のマッピング。
    """
    w = _get_workspace_client()
    for file_path, content in backup.items():
        w.files.upload(file_path, io.BytesIO(content), overwrite=True)
