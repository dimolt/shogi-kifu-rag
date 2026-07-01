"""pytest共有フィクスチャ定義"""

from pathlib import Path

import pytest


@pytest.fixture
def sample_kif_content() -> str:
    """プレイヤー名・3手を含む正常なKIF文字列を提供する。"""
    return (
        "手合割：平手\n"
        "先手：先手太郎\n"
        "後手：後手次郎\n"
        "手数----指手---------消費時間--\n"
        "1 ７六歩(77) ( 0:00/00:00:00)\n"
        "2 ３四歩(33) ( 0:00/00:00:00)\n"
        "3 ２六歩(27) ( 0:00/00:00:00)\n"
    )


@pytest.fixture
def sample_kif_content_no_names() -> str:
    """プレイヤー名の記載がないKIF文字列を提供する。"""
    return (
        "手合割：平手\n"
        "手数----指手---------消費時間--\n"
        "1 ７六歩(77) ( 0:00/00:00:00)\n"
    )


@pytest.fixture
def kif_file_utf8(tmp_path: Path, sample_kif_content: str) -> str:
    """UTF-8エンコーディングのKIFファイルを一時パスに生成する。"""
    file_path = tmp_path / "sample_utf8.kif"
    file_path.write_text(sample_kif_content, encoding="utf-8")
    return str(file_path)


@pytest.fixture
def kif_file_cp932(tmp_path: Path, sample_kif_content: str) -> str:
    """CP932（Shift-JIS）エンコーディングのKIFファイルを一時パスに生成する。"""
    file_path = tmp_path / "sample_cp932.kif"
    file_path.write_bytes(sample_kif_content.encode("cp932"))
    return str(file_path)