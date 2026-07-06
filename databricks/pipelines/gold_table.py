"""Gold Table: 局面特徴量・ゲームサマリーを生成するLakeflowパイプライン定義。"""

from pyspark import pipelines as dp
from pyspark.sql.functions import abs as abs_
from pyspark.sql.functions import (
    col,
    collect_list,
    concat,
    first,
    lag,
    last,
    lit,
    sort_array,
    struct,
    to_json,
    when,
)
from pyspark.sql.functions import max as max_
from pyspark.sql.functions import sum as sum_
from pyspark.sql.window import Window

catalog = spark.conf.get("catalog")
silver_schema = spark.conf.get("silver_schema")

BLUNDER_THRESHOLD_CP = 200


def _add_turn_score_columns(silver_df):
    """手番視点の評価値・差分・悪手判定列を付与する。

    position_features / game_summary で共通利用する列を生成する。

    Args:
        silver_df: Silverテーブルの局面データ。

    Returns:
        score_from_turn, score_delta, is_blunder列を追加したDataFrame。
    """
    window = Window.partitionBy("game_id").orderBy("move_number")

    scored_df = silver_df.withColumn(
        "score_from_turn",
        when(col("player") == "white", -col("score_cp")).otherwise(col("score_cp")),
    )
    scored_df = scored_df.withColumn(
        "score_delta",
        col("score_from_turn") - lag("score_from_turn", 1).over(window),
    )
    scored_df = scored_df.withColumn(
        "is_blunder",
        abs_(col("score_delta")) >= BLUNDER_THRESHOLD_CP,
    )
    return scored_df


def build_position_features(silver_df):
    """Silverテーブルから局面特徴量（Gold: position_features）を生成する。

    Args:
        silver_df: Silverテーブルの局面データ。

    Returns:
        局面ごとの特徴量列を持つGold DataFrame。
    """
    scored_df = _add_turn_score_columns(silver_df)

    featured_df = scored_df.withColumn(
        "is_best_move",
        col("move_usi") == col("best_move"),
    )
    featured_df = featured_df.withColumn(
        "move_quality",
        when(col("move_number") == 0, lit("start"))
        .when(col("is_best_move"), lit("best"))
        .when(col("is_blunder"), lit("blunder"))
        .otherwise(lit("normal")),
    )
    featured_df = featured_df.withColumn(
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

    return featured_df.select(
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


def build_game_summary(silver_df):
    """Silverテーブルからゲームサマリー（Gold: game_summary）を生成する。

    Args:
        silver_df: Silverテーブルの局面データ。

    Returns:
        対局ごとの集計結果を持つGold DataFrame。
    """
    scored_df = _add_turn_score_columns(silver_df)

    order_window = Window.partitionBy("game_id").orderBy("move_number").rowsBetween(
        Window.unboundedPreceding, Window.unboundedFollowing
    )
    scored_df = scored_df.withColumn(
        "final_score_cp",
        last("score_cp", ignorenulls=True).over(order_window),
    )

    summary_df = scored_df.groupBy("game_id").agg(
        first("black_player").alias("black_player"),
        first("white_player").alias("white_player"),
        max_("move_number").alias("total_moves"),
        first("final_score_cp").alias("final_score_cp"),
        sum_(
            when((col("player") == "black") & col("is_blunder"), 1).otherwise(0)
        ).alias("black_blunders"),
        sum_(
            when((col("player") == "white") & col("is_blunder"), 1).otherwise(0)
        ).alias("white_blunders"),
        sort_array(
            collect_list(struct("move_number", "score_cp"))
        ).alias("score_series"),
    )

    summary_df = summary_df.withColumn(
        "score_series_json", to_json("score_series")
    ).drop("score_series")

    return summary_df


@dp.table
def position_features():
    """Gold Table: 局面特徴量"""
    silver_df = spark.read.table(f"{catalog}.{silver_schema}.positions")
    return build_position_features(silver_df)


@dp.table
def game_summary():
    """Gold Table: ゲームサマリー"""
    silver_df = spark.read.table(f"{catalog}.{silver_schema}.positions")
    return build_game_summary(silver_df)
