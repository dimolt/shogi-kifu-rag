"""Silver Table Registration

analysis.csvをshogi.shogi_silver.positionsテーブルに登録するノートブック
"""

from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructField,
    StructType,
)

# スキーマ定義
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

# CSVファイルの読み込み
df = spark.read.csv(
    "/Volumes/shogi/landing/kif/analysis.csv",
    header=True,
    schema=schema,
)

# Silver Tableへの書き込み
df.write.format("delta").mode("append").saveAsTable("shogi.shogi_silver.positions")
