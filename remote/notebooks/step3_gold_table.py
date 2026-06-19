"""Gold Table Construction

Silver TableからGold Tableを構築するノートブック
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    lit,
    when,
    lag,
    abs,
    collect_list,
    struct,
    count,
    max as max_,
    sum as sum_,
    first,
)
from pyspark.sql.window import Window
from pyspark.sql.types import (
    StringType,
    IntegerType,
    BooleanType,
)

# SparkSessionの初期化
spark = SparkSession.builder.getOrCreate()

# Silver Tableの読み込み
silver_df = spark.table("shogi.shogi_silver.positions")

# 特徴量の計算
window = Window.partitionBy("game_id").orderBy("move_number")

# score_from_turn: 手番視点の評価値（後手番は符号反転）
gold_df = silver_df.withColumn(
    "score_from_turn",
    when(col("player") == "white", -col("score_cp")).otherwise(col("score_cp")),
)

# score_delta: 前手からの評価値変化
gold_df = gold_df.withColumn(
    "score_delta",
    col("score_from_turn") - lag("score_from_turn", 0).over(window),
)

# is_best_move: 実際の指し手 = 推奨手かどうか
gold_df = gold_df.withColumn(
    "is_best_move",
    col("move_usi") == col("best_move"),
)

# is_blunder: abs(score_delta) >= 200
gold_df = gold_df.withColumn(
    "is_blunder",
    abs(col("score_delta")) >= 200,
)

# move_quality: start / best / blunder / normal
gold_df = gold_df.withColumn(
    "move_quality",
    when(col("move_number") == 0, lit("start"))
    .when(col("is_best_move"), lit("best"))
    .when(col("is_blunder"), lit("blunder"))
    .otherwise(lit("normal")),
)

# search_text: ChromaDB登録用テキスト
gold_df = gold_df.withColumn(
    "search_text",
    f"局面: {col('sfen')} 指し手: {col('move_usi')} 推奨手: {col('best_move')} 評価値: {col('score_cp')}cp",
)

# position_featuresテーブルの作成
position_features = gold_df.select(
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
    "score_from_turn",
    "score_delta",
    "is_best_move",
    "is_blunder",
    "move_quality",
    "search_text",
)

position_features.write.format("delta").mode("overwrite").saveAsTable(
    "shogi.shogi_gold.position_features"
)

# game_summaryテーブルの作成
game_summary = (
    gold_df.groupBy("game_id")
    .agg(
        first("black_player").alias("black_player"),
        first("white_player").alias("white_player"),
        max_("move_number").alias("total_moves"),
        last("score_cp").alias("final_score_cp"),
        sum_(when((col("player") == "black") & col("is_blunder"), 1).otherwise(0)).alias(
            "black_blunders"
        ),
        sum_(when((col("player") == "white") & col("is_blunder"), 1).otherwise(0)).alias(
            "white_blunders"
        ),
        collect_list(struct("move_number", "score_cp")).alias("score_series"),
    )
)

# score_seriesをJSONに変換
from pyspark.sql.functions import to_json

game_summary = game_summary.withColumn("score_series_json", to_json("score_series")).drop(
    "score_series"
)

game_summary.write.format("delta").mode("overwrite").saveAsTable(
    "shogi.shogi_gold.game_summary"
)

# 確認
print("position_features:")
spark.table("shogi.shogi_gold.position_features").show(5)

print("game_summary:")
spark.table("shogi.shogi_gold.game_summary").show(5)
