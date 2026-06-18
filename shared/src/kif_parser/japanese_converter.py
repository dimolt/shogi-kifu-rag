"""日本語表記変換モジュール"""

import shogi


def usi_to_japanese(usi_move: str) -> str:
    """USI形式の指し手を日本語表記に変換する

    Args:
        usi_move: USI形式の指し手（例: "2g2f"）

    Returns:
        日本語表記の指し手（例: "４八歩"）
    """
    # Boardを使用して座標変換
    move = shogi.Move.from_usi(usi_move)

    # 移動先の座標を取得
    to_square = move.to_square

    # shogiの座標系: 0-80 (0=9一, 80=1九)
    # 日本語: 列9-1, 行一-九
    to_file = 9 - (to_square // 9)  # ファイル（9-1）
    to_rank = (to_square % 9) + 1   # ランク（1-9）

    # 日本語表記の数字
    japanese_numbers = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"]

    # 駒の種類を簡易判定（とりあえず歩）
    piece_name = "歩"

    return f"{to_file}{japanese_numbers[to_rank]}{piece_name}"
