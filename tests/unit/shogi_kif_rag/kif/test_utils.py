"""kif.utilsのユニットテスト。"""

from pathlib import Path

import pytest

from shogi_kif_rag.kif.utils import resolve_csv_paths


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
