"""KIFパーサモジュール"""

import chardet
import shogi
import shogi.KIF


def detect_encoding(file_path: str) -> str:
    """ファイルのエンコーディングを検出する

    Args:
        file_path: ファイルパス

    Returns:
        エンコーディング名（cp932または検出結果）
    """
    with open(file_path, "rb") as f:
        raw = f.read()
    enc = chardet.detect(raw).get("encoding", "utf-8") or "utf-8"
    # cp1006はcp932のエイリアスとして扱う
    if enc.lower() in ("shift_jis", "shift-jis", "sjis", "cp1006"):
        return "cp932"
    return enc


def kif_to_positions(kif_content: str) -> list[dict]:
    """KIF形式の棋譜をパースして局面リストを生成する

    Args:
        kif_content: KIF形式の棋譜文字列

    Returns:
        局面情報の辞書リスト
    """
    kif = shogi.KIF.Parser.parse_str(kif_content)[0]
    names = kif.get("names", [])
    black_player = names[0] if len(names) > 0 else "先手"
    white_player = names[1] if len(names) > 1 else "後手"
    moves = kif.get("moves", [])

    board = shogi.Board()
    records = []
    records.append({
        "move_number": 0,
        "sfen": board.sfen(),
        "prev_sfen": board.sfen(),
        "move_usi": "",
        "player": "black",
        "black_player": black_player,
        "white_player": white_player,
    })

    for i, move in enumerate(moves):
        if isinstance(move, str):
            move_usi = move
            try:
                move_int = shogi.Move.from_usi(move_usi)
            except Exception:
                break
        else:
            move_int = move
            try:
                move_usi = shogi.move_to_usi(move_int)
            except Exception:
                move_usi = str(move)

        player = "black" if board.turn == shogi.BLACK else "white"
        prev_sfen = board.sfen()

        try:
            board.push(move_int)
        except Exception:
            break

        records.append({
            "move_number": i + 1,
            "sfen": board.sfen(),
            "prev_sfen": prev_sfen,
            "move_usi": move_usi,
            "player": player,
            "black_player": black_player,
            "white_player": white_player,
        })

    return records
