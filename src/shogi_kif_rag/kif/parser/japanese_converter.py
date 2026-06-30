"""日本語表記変換モジュール"""

import shogi

from shogi_kif_rag.exceptions import AppBaseError


class InvalidUsiMoveError(AppBaseError):
    """USI形式の指し手文字列が不正な場合に送出される例外。"""

    def __init__(self, usi_move: str) -> None:
        self.usi_move = usi_move
        super().__init__(f"不正なUSI形式の指し手です: {usi_move}")


BOARD_SIZE = 9

_JAPANESE_RANK_NUMBERS = ("", "一", "二", "三", "四", "五", "六", "七", "八", "九")

# python-shogi が提供する駒種 -> 日本語表記の対応表
# 例: PIECE_JAPANESE_SYMBOLS[shogi.PAWN] == "歩"
_PIECE_JAPANESE_SYMBOLS = shogi.PIECE_JAPANESE_SYMBOLS

# board.piece_type_at() が駒の存在しないマスに対して返す値
_NO_PIECE = 0


def usi_to_japanese(usi_move: str, board: shogi.Board) -> str:
    """USI形式の指し手を日本語表記に変換する。

    盤面情報を参照し、移動する駒の種類を判定して日本語の指し手表記
    （例: "２六歩"）を生成する。打ち駒や成りにも対応する。

    Args:
        usi_move: USI形式の指し手（例: "2g2f"、打ち駒の場合は "P*5e"）。
        board: 指し手が指される直前の盤面状態。移動元の駒種判定に使用する。

    Returns:
        日本語表記の指し手（例: "２六歩"、"５五歩打"、"８八角成"）。

    Raises:
        InvalidUsiMoveError: usi_move がUSI形式として不正な場合。
    """
    try:
        move = shogi.Move.from_usi(usi_move)
    except ValueError as e:
        raise InvalidUsiMoveError(usi_move) from e

    to_file, to_rank = _square_to_japanese_position(move.to_square)
    piece_name = _resolve_piece_name(move, board)
    suffix = _resolve_suffix(move)

    return f"{to_file}{_JAPANESE_RANK_NUMBERS[to_rank]}{piece_name}{suffix}"


def _square_to_japanese_position(square: int) -> tuple[int, int]:
    """マス番号を日本語の筋・段に変換する。

    Args:
        square: shogiライブラリのマス番号（0-80、0=9一、80=1九）。

    Returns:
        (筋, 段) のタプル。筋は9-1、段は1-9の整数。

    Note:
        shogiライブラリのマス番号は81マスを9マスごとの段（0=一段目）で
        区切り、各段内は9筋から1筋の順に並んでいる
        （例: 0=9一, 8=1一, 9=9二, ..., 80=1九）。
        そのため段は `square // BOARD_SIZE`、筋は
        `BOARD_SIZE - (square % BOARD_SIZE)` で求める。
    """
    rank_number = (square // BOARD_SIZE) + 1
    file_number = BOARD_SIZE - (square % BOARD_SIZE)
    return file_number, rank_number


def _resolve_piece_name(move: shogi.Move, board: shogi.Board) -> str:
    """指し手から移動・打ち駒の駒名（日本語）を取得する。

    Args:
        move: 対象の指し手。
        board: 移動元の駒種判定に使用する盤面状態。

    Returns:
        駒の日本語名（例: "歩", "角"）。

    Raises:
        InvalidUsiMoveError: 盤面上に該当する駒が存在しない場合。
    """
    if move.drop_piece_type is not None:
        piece_type = move.drop_piece_type
    else:
        piece_type = board.piece_type_at(move.from_square)

    if piece_type is None or piece_type == _NO_PIECE:
        raise InvalidUsiMoveError(move.usi())

    return _PIECE_JAPANESE_SYMBOLS[piece_type]


def _resolve_suffix(move: shogi.Move) -> str:
    """成り・打ちを示す接尾辞を返す。

    Args:
        move: 対象の指し手。

    Returns:
        成りの場合は "成"、打ち駒の場合は "打"、どちらでもなければ空文字。
    """
    if move.promotion:
        return "成"
    if move.drop_piece_type is not None:
        return "打"
    return ""
