"""Silver Table: analysis.csvから棋譜局面を登録するLakeflowパイプライン定義。"""

from pyspark import pipelines as dp
from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructField,
    StructType,
)

CSV_PATH = "/Volumes/shogi/landing/kif/analysis.csv"


def get_analysis_schema():
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


@dp.table
def positions():
    """Silver Table: analysis.csvから棋譜局面を登録"""
    return spark.read.csv(CSV_PATH, header=True, schema=get_analysis_schema())
