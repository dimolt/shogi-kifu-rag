"""ローカルPCで実行。やねうら王でKIFを解析してCSVを出力する。"""

import csv
import logging
import sys
from pathlib import Path

from shogi_kif_rag.kif.config.local_analyze_settings import LocalAnalyzeSettings
from shogi_kif_rag.kif.engine.usi_engine_client import UsiEngineClient
from shogi_kif_rag.kif.parser import KifParser, PositionRecord
from shogi_kif_rag.kif.schemas.shemas import CSV_FIELDNAMES, AnalysisRow

logger = logging.getLogger(__name__)

# --- 定数 -------------------------------------------------------------
DEFAULT_KIF_PATH = "data/kif_files/sample.kif"
DEFAULT_OUTPUT_CSV = "data/output/analysis.csv"
USI_HASH_SIZE_MB = 256
THINK_TIME_SECONDS = 3.0


class AnalyzeError(Exception):
    """局面解析処理の失敗。"""


def _parse_args(argv: list[str]) -> tuple[Path, Path]:
    """コマンドライン引数からKIFパスと出力先CSVパスを取得する。

    Args:
        argv: sys.argv 相当のリスト。

    Returns:
        (kif_path, out_csv) のタプル。
    """
    kif_path = Path(argv[1]) if len(argv) > 1 else Path(DEFAULT_KIF_PATH)
    out_csv = Path(argv[2]) if len(argv) > 2 else Path(DEFAULT_OUTPUT_CSV)
    return kif_path, out_csv


def _load_positions(kif_path: Path) -> list[PositionRecord]:
    """KIFファイルを読み込み局面リストを取得する。

    Args:
        kif_path: 解析対象のKIFファイルパス。

    Returns:
        局面レコードのリスト。

    Raises:
        AnalyzeError: KIFファイルの読み込み・パースに失敗した場合。
    """
    if not kif_path.exists():
        raise AnalyzeError(f"KIFファイルが見つかりません: {kif_path}")

    try:
        parser = KifParser(str(kif_path))
        positions = parser.load_file()
    except Exception as e:
        raise AnalyzeError(f"KIFファイルのパースに失敗しました: {kif_path}") from e

    return positions


def _analyze_positions(
    analyzer: UsiEngineClient,
    positions: list[PositionRecord],
    game_id: str,
) -> list[AnalysisRow]:
    """各局面をエンジンで解析し、結果行のリストを作成する。

    Args:
        analyzer: 起動済みのUSIエンジンクライアント。
        positions: 解析対象の局面レコードのリスト。
        game_id: 対局を一意に識別するID。

    Returns:
        エンジン解析結果を含む出力行のリスト。

    Raises:
        AnalyzeError: いずれかの局面でエンジン解析に失敗した場合。
    """
    rows: list[AnalysisRow] = []

    for pos in positions:
        try:
            result = analyzer.analyze_position_reusable(
                pos["sfen"],
                think_time=THINK_TIME_SECONDS,
            )
        except Exception as e:
            raise AnalyzeError(
                f"局面の解析に失敗しました（手数{pos['move_number']}）"
            ) from e

        row: AnalysisRow = {
            "game_id": game_id,
            **pos,
            "best_move": result["best_move"],
            "score_cp": result["score_cp"],
            "pv": result["pv"],
        }
        rows.append(row)

        logger.info(
            "手数%3d | %8s | 推奨:%8s | %6dcp",
            pos["move_number"],
            pos["move_usi"],
            result["best_move"],
            result["score_cp"],
        )

    return rows


def _write_csv(rows: list[AnalysisRow], out_csv: Path) -> None:
    """解析結果をCSVファイルに書き出す。

    Args:
        rows: 書き出す出力行のリスト。
        out_csv: 出力先CSVファイルパス。
    """
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """KIFファイルをやねうら王で解析しCSVを出力するエントリポイント。"""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    kif_path, out_csv = _parse_args(sys.argv)
    game_id = kif_path.stem

    logger.info("解析開始: %s", kif_path)
    logger.info("game_id : %s", game_id)

    positions = _load_positions(kif_path)
    logger.info("局面数: %d", len(positions))

    settings = LocalAnalyzeSettings()
    analyzer = UsiEngineClient(settings.yaneuraou_path, settings.yaneuraou_options)
    analyzer.start()
    analyzer.initialize_usi(usi_hash=USI_HASH_SIZE_MB)

    try:
        rows = _analyze_positions(analyzer, positions, game_id)
    finally:
        analyzer.stop()

    _write_csv(rows, out_csv)

    print(f"CSV出力完了: {out_csv}")


if __name__ == "__main__":
    main()
