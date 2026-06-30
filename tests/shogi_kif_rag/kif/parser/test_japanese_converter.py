"""japanese_converter モジュールのユニットテスト"""

import pytest
import shogi

from shogi_kif_rag.kif.parser.japanese_converter import (
    InvalidUsiMoveError,
    usi_to_japanese,
)


@pytest.fixture
def initial_board() -> shogi.Board:
    """平手初期局面のBoardを提供する。"""
    return shogi.Board()


def test_usi_to_japanese_歩を一マス進めると_座標が一致する日本語表記を返す(
    initial_board: shogi.Board,
) -> None:
    # Arrange
    usi_move = "2g2f"

    # Act
    result = usi_to_japanese(usi_move, initial_board)

    # Assert
    assert result == "2六歩"


def test_usi_to_japanese_角を成る指し手を渡すと_成の接尾辞付きで返す() -> None:
    # Arrange
    board = shogi.Board()
    for usi_move in ("2g2f", "3c3d", "2f2e", "3d3e"):
        board.push_usi(usi_move)

    # Act
    result = usi_to_japanese("8h2b+", board)

    # Assert
    assert result == "2二角成"


def test_usi_to_japanese_歩を打つ指し手を渡すと_打の接尾辞付きで返す(
    initial_board: shogi.Board,
) -> None:
    # Arrange
    usi_move = "P*5e"

    # Act
    result = usi_to_japanese(usi_move, initial_board)

    # Assert
    assert result == "5五歩打"


def test_usi_to_japanese_不正なUSI形式を渡すと_InvalidUsiMoveErrorを送出する(
    initial_board: shogi.Board,
) -> None:
    # Arrange
    invalid_usi_move = "xxxx"

    # Act & Assert
    with pytest.raises(InvalidUsiMoveError) as exc_info:
        usi_to_japanese(invalid_usi_move, initial_board)

    assert exc_info.value.usi_move == invalid_usi_move


def test_usi_to_japanese_盤面に存在しない駒の移動元を渡すと_InvalidUsiMoveErrorを送出する(
    initial_board: shogi.Board,
) -> None:
    # Arrange
    # 5五には初期局面で駒が存在しないため、移動元として不正な指し手になる
    usi_move = "5e5d"

    # Act & Assert
    with pytest.raises(InvalidUsiMoveError):
        usi_to_japanese(usi_move, initial_board)
