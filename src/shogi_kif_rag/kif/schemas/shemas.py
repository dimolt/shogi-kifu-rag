"""local_analyze.py の出力とDatabricks Bronzeレイヤー取り込みで共有するスキーマ定義。

ここを変更した場合は、Databricks側のIngestion処理（StructType定義等）も
合わせて更新すること。
"""

from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructField,
    StructType,
)

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


def get_analysis_schema() -> StructType:
    """AnalysisRowに対応するSpark StructTypeを返す。

    Returns:
        analysis.csvのカラム定義に対応したStructType。
    """
    return StructType([
        StructField("game_id", StringType(), True),
        StructField("move_number", IntegerType(), True),
        StructField("sfen", StringType(), True),
        StructField("prev_sfen", StringType(), True),
        StructField("move_usi", StringType(), True),
        StructField("player", StringType(), True),
        StructField("black_player", StringType(), True),
        StructField("white_player", StringType(), True),
        StructField("best_move", StringType(), True),
        StructField("score_cp", IntegerType(), True),
        StructField("pv", StringType(), True),
    ])
