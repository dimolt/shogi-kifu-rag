"""csv_utilsのユニットテスト。"""

from pathlib import Path

import pytest

from dbx_bundle.utils.csv_utils import resolve_csv_paths


def test_resolve_csv_paths_ワイルドカードなしの単一ファイルパスをそのまま返す(tmp_path: Path) -> None:
    # Arrange
    csv_path = str(tmp_path / "single.csv")

    # Act
    result = resolve_csv_paths(csv_path)

    # Assert
    assert result == csv_path


def test_resolve_csv_paths_ワイルドカードなしのディレクトリパスをそのまま返す(tmp_path: Path) -> None:
    # Arrange
    dir_path = str(tmp_path)

    # Act
    result = resolve_csv_paths(dir_path)

    # Assert
    assert result == dir_path


def test_resolve_csv_paths_ワイルドカードで一致するファイルをソートして返す(tmp_path: Path) -> None:
    # Arrange
    (tmp_path / "file_02.csv").touch()
    (tmp_path / "file_01.csv").touch()
    (tmp_path / "file_03.csv").touch()
    csv_path = str(tmp_path / "file_*.csv")

    # Act
    result = resolve_csv_paths(csv_path)

    # Assert
    assert isinstance(result, list)
    assert len(result) == 3
    assert result == [
        str(tmp_path / "file_01.csv"),
        str(tmp_path / "file_02.csv"),
        str(tmp_path / "file_03.csv"),
    ]


def test_resolve_csv_paths_ワイルドカードで一致するファイルがない場合_FileNotFoundError(tmp_path: Path) -> None:
    # Arrange
    csv_path = str(tmp_path / "nonexistent_*.csv")

    # Act & Assert
    with pytest.raises(FileNotFoundError, match="No files matched:"):
        resolve_csv_paths(csv_path)


def test_resolve_csv_paths_ワイルドカードでディレクトリは除外される(tmp_path: Path) -> None:
    # Arrange
    (tmp_path / "data.csv").touch()
    (tmp_path / "data_dir").mkdir()
    csv_path = str(tmp_path / "data*")

    # Act
    result = resolve_csv_paths(csv_path)

    # Assert
    assert isinstance(result, list)
    assert len(result) == 1
    assert result == [str(tmp_path / "data.csv")]


def test_resolve_csv_paths_クエスチョンマークワイルドカードを展開する(tmp_path: Path) -> None:
    # Arrange
    (tmp_path / "file_a.csv").touch()
    (tmp_path / "file_b.csv").touch()
    csv_path = str(tmp_path / "file_?.csv")

    # Act
    result = resolve_csv_paths(csv_path)

    # Assert
    assert isinstance(result, list)
    assert len(result) == 2
    assert result == [
        str(tmp_path / "file_a.csv"),
        str(tmp_path / "file_b.csv"),
    ]


# ---------------------------------------------------------------------------
# /Volumes/ で始まるパス（Databricks Volumeパス）
# ---------------------------------------------------------------------------


def test_resolve_csv_paths_Volumesパスの場合_ワイルドカードを含んでいても展開せずそのまま返す() -> None:
    # Arrange
    # Databricks Volumeパスはローカルファイルシステム上に存在しないため、
    # ワイルドカード展開をスキップしてSparkに処理を委ねる仕様を検証する。
    csv_path = "/Volumes/shogi/landing/analyzed/*.csv"

    # Act
    result = resolve_csv_paths(csv_path)

    # Assert
    assert result == csv_path


def test_resolve_csv_paths_Volumesパスの場合_ワイルドカードなしでもそのまま返す() -> None:
    # Arrange
    csv_path = "/Volumes/shogi/landing/analyzed/single.csv"

    # Act
    result = resolve_csv_paths(csv_path)

    # Assert
    assert result == csv_path


def test_resolve_csv_paths_Volumesパスの場合_ローカルに一致ファイルが存在しなくてもFileNotFoundErrorを送出しない() -> None:
    # Arrange
    # ローカルファイルシステムには存在しないVolumesパスでも、
    # ワイルドカード展開自体をスキップするため例外は発生しないことを確認する。
    csv_path = "/Volumes/nonexistent_catalog/nonexistent_schema/nonexistent_volume/*.csv"

    # Act
    result = resolve_csv_paths(csv_path)

    # Assert
    assert result == csv_path


def test_resolve_csv_paths_Volumesパスの場合_戻り値は文字列でありリストにならない() -> None:
    # Arrange
    csv_path = "/Volumes/shogi/landing/analyzed/*.csv"

    # Act
    result = resolve_csv_paths(csv_path)

    # Assert
    # 通常のワイルドカードパスはlist[str]を返しうるが、
    # Volumesパスは常に単一文字列のまま返る（Spark側でワイルドカード解決される）。
    assert isinstance(result, str)
