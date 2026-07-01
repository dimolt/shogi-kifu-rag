"""local_analyze.py の出力とDatabricks Bronzeレイヤー取り込みで共有するスキーマ定義。

ここを変更した場合は、Databricks側のIngestion処理（StructType定義等）も
合わせて更新すること。
"""

from shogi_kif_rag.kif.parser import PositionRecord

CSV_FIELDNAMES = [
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


class AnalysisRow(PositionRecord):
    """エンジン解析結果を付与した出力行（analysis.csvの1レコード）。

    PositionRecord（KifParserの出力契約）に、やねうら王による
    解析結果フィールドを追加したもの。
    """

    game_id: str
    best_move: str
    score_cp: int
    pv: str