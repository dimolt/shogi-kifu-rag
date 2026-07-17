"""CSVファイル操作のテストヘルパー関数。"""

from pathlib import Path

CSV_HEADER = (
    "game_id,move_number,sfen,prev_sfen,move_usi,player,black_player,"
    "white_player,best_move,score_cp,pv\n"
)


def write_analysis_csv(path: Path, body: str) -> str:
    """テスト用analysis.csvファイルを書き出しパスを返す。

    Args:
        path: 書き出し先のパス。
        body: ヘッダーを除く本文。

    Returns:
        書き出したファイルのパス文字列。
    """
    path.write_text(CSV_HEADER + body, encoding="utf-8")
    return str(path)
