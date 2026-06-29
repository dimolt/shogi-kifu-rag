from pyspark import pipelines as dp
from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructField,
    StructType,
)


@dp.table
def positions():
    """Silver Table: analysis.csvから棋譜局面を登録"""
    schema = StructType([
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

    return spark.read.csv(
        "/Volumes/shogi/landing/kif/analysis.csv",
        header=True,
        schema=schema,
    )
