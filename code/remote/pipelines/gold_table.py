from pyspark import pipelines as dp
from pyspark.sql.functions import (
    abs,
    col,
    collect_list,
    concat,
    first,
    lag,
    last,
    lit,
    struct,
    to_json,
    when,
)
from pyspark.sql.functions import (
    max as max_,
)
from pyspark.sql.functions import (
    sum as sum_,
)
from pyspark.sql.window import Window


@dp.table
def position_features():
    """Gold Table: 局面特徴量"""
    silver_df = spark.read.table("silver_table")
    
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
        concat(
            lit("局面: "),
            col("sfen"),
            lit(" 指し手: "),
            col("move_usi"),
            lit(" 推奨手: "),
            col("best_move"),
            lit(" 評価値: "),
            col("score_cp").cast("string"),
            lit("cp"),
        ),
    )
    
    return gold_df.select(
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


@dp.table
def game_summary():
    """Gold Table: ゲームサマリー"""
    silver_df = spark.read.table("silver_table")
    
    window = Window.partitionBy("game_id").orderBy("move_number")
    
    # score_from_turn: 手番視点の評価値（後手番は符号反転）
    gold_df = silver_df.withColumn(
        "score_from_turn",
        when(col("player") == "white", -col("score_cp")).otherwise(col("score_cp")),
    )
    
    # is_blunder: abs(score_delta) >= 200
    gold_df = gold_df.withColumn(
        "score_delta",
        col("score_from_turn") - lag("score_from_turn", 0).over(window),
    )
    gold_df = gold_df.withColumn(
        "is_blunder",
        abs(col("score_delta")) >= 200,
    )
    
    game_summary = (
        gold_df.groupBy("game_id")
        .agg(
            first("black_player").alias("black_player"),
            first("white_player").alias("white_player"),
            max_("move_number").alias("total_moves"),
            last("score_cp").alias("final_score_cp"),
            sum_(
                when((col("player") == "black") & col("is_blunder"), 1).otherwise(0)
            ).alias("black_blunders"),
            sum_(
                when((col("player") == "white") & col("is_blunder"), 1).otherwise(0)
            ).alias("white_blunders"),
            collect_list(struct("move_number", "score_cp")).alias("score_series"),
        )
    )
    
    # score_seriesをJSONに変換
    game_summary = game_summary.withColumn(
        "score_series_json", to_json("score_series")
    ).drop("score_series")
    
    return game_summary
