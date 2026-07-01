"""ローカルPCで実行。やねうら王でKIFを解析してCSVを出力する。"""

import csv
import sys
from pathlib import Path

# local/srcモジュールをパスに追加
local_src_path = Path(__file__).parent
sys.path.insert(0, str(local_src_path))

# sharedモジュールをパスに追加
shared_path = Path(__file__).parent.parent.parent.parent / "shared" / "src"
sys.path.insert(0, str(shared_path))

from config.settings import LocalSettings  # noqa: E402
from engine.usi_engine_client import UsiEngineClient  # noqa: E402
from kif_parser.parser import kif_to_positions  # noqa: E402
from shared.src.kif_parser.parser import detect_encoding  # noqa: E402, type: ignore


def main():
    kif_path = sys.argv[1] if len(sys.argv) > 1 else "data/kif_files/sample.kif"
    out_csv = sys.argv[2] if len(sys.argv) > 2 else "data/output/analysis.csv"

    # 設定を読み込み
    settings = LocalSettings()

    # KIFファイル名からgame_idを生成
    game_id = Path(kif_path).stem

    print(f"解析開始: {kif_path}")
    print(f"game_id : {game_id}")

    # KIFファイルを読み込んでパース
    encoding = detect_encoding(kif_path)
    with open(kif_path, encoding=encoding, errors="replace") as f:
        content = f.read()

    positions = kif_to_positions(content)
    print(f"局面数: {len(positions)}")

    rows = []

    # エンジンを1回だけ起動して再利用
    analyzer = UsiEngineClient(
        settings.yaneuraou_path, settings.yaneuraou_options
    )
    analyzer.start()
    analyzer.initialize_usi(usi_hash=256)

    try:
        for i, pos in enumerate(positions):
            result = analyzer.analyze_position_reusable(
                pos["sfen"],
                think_time=3.0,
            )
            row = {
                "game_id": game_id,
                **pos,
                "best_move": result["best_move"],
                "score_cp": result["score_cp"],
                "pv": result["pv"],
            }
            rows.append(row)
            print(
                f"  手数{pos['move_number']:>3} | {pos['move_usi']:>8} | "
                f"推奨:{result['best_move']:>8} | {result['score_cp']:>6}cp"
            )
    finally:
        analyzer.stop()

    # CSV出力
    output_dir = Path(out_csv).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "game_id",
        "move_number",
        "sfen",
        "prev_sfen",
        "move_usi",
        "player",
        "black_player",
        "white_player",
        "best_move",
        "score_cp",
        "pv",
    ]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV出力完了: {out_csv}")


if __name__ == "__main__":
    main()
