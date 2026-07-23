"""Databricks Volume操作の共通ヘルパー関数。"""

import os
from pathlib import Path

from databricks.sdk import WorkspaceClient


def get_test_data_volume_path(catalog: str) -> str:
    """テストデータ用Volumeパスを取得する。

    Args:
        catalog: カタログ名（shogi_dev/shogi_test/shogi）。

    Returns:
        テストデータ用Volumeパス（/Volumes/{catalog}/test/data）。
    """
    return f"/Volumes/{catalog}/test/data"


def get_landing_volume_path(catalog: str) -> str:
    """Landing Volumeパスを取得する。

    Args:
        catalog: カタログ名（shogi_dev/shogi_test/shogi）。

    Returns:
        Landing Volumeパス（/Volumes/{catalog}/landing/analyzed）。
    """
    return f"/Volumes/{catalog}/landing/analyzed"


def upload_csv_to_volume(local_path: Path, volume_path: str, filename: str) -> None:
    """CSVをUnity Catalog Volumeにアップロードする。

    Args:
        local_path: ローカルのCSVファイルパス。
        volume_path: アップロード先のVolumeディレクトリパス。
        filename: Volume上のファイル名。
    """
    w = WorkspaceClient(profile=os.environ.get("DATABRICKS_CONFIG_PROFILE", "shogi"))
    remote_path = f"{volume_path}/{filename}"
    with local_path.open("rb") as f:
        w.files.upload(remote_path, f, overwrite=True)


def cleanup_volume_files(volume_path: str, pattern: str) -> None:
    """Volume上のテスト用ファイルを削除する。

    Args:
        volume_path: Volumeディレクトリパス。
        pattern: 削除対象のファイルパターン。
    """
    w = WorkspaceClient(profile=os.environ.get("DATABRICKS_CONFIG_PROFILE", "shogi"))
    try:
        files = w.files.list(volume_path)
        for file_info in files:
            if pattern in file_info.path:
                w.files.delete(file_info.path)
    except Exception:
        # Volumeが存在しない場合は無視
        pass
