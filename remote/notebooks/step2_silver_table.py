"""Silver Table Registration

analysis.csvをshogi.shogi_silver.positionsテーブルに登録するノートブック
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StringType,
    IntegerType,
    StructType,
    StructField,
)

# SparkSessionの初期化
spark = SparkSession.builder.getOrCreate()

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

# データの確認
print(f"Total rows: {df.count()}")
df.show(5)

# Silver Tableへの書き込み
df.write.format("delta").mode("overwrite").saveAsTable("shogi.shogi_silver.positions")

# 確認
spark.table("shogi.shogi_silver.positions").show(5)
