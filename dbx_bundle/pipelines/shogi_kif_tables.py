""" csvから棋譜局面を登録するLakeflowパイプライン定義。"""

from pyspark import pipelines as dp

from shogi_kif_rag.transforms.csv_to_positions import build_positions
from shogi_kif_rag.transforms.positions import (
    build_game_summary,
    build_position_features,
)

catalog = spark.conf.get("bundle.catalog")
silver_schema = spark.conf.get("bundle.silver_schema")
gold_schema = spark.conf.get("bundle.gold_schema")
landing_schema = spark.conf.get("bundle.landing_schema")
CSV_PATH = f"/Volumes/{catalog}/{landing_schema}/analyzed/*.csv"


# ---------------------------------------------------------------------------
# silver tables
# ---------------------------------------------------------------------------
@dp.table
@dp.expect("valid_game_id", "game_id IS NOT NULL")
@dp.expect("valid_move_number", "move_number >= 0")
@dp.expect("valid_player", "player IN ('black', 'white')")
def positions():
    """Silver Table: analysis.csvから棋譜局面を登録"""
    return build_positions(spark, CSV_PATH)


# ---------------------------------------------------------------------------
# gold tables
# ---------------------------------------------------------------------------
@dp.table(name=f"{catalog}.{gold_schema}.position_features")
@dp.expect("valid_move_quality", "move_quality IN ('start', 'best', 'blunder', 'normal')")  #noqa: E501
def position_features():
    """Gold Table: 局面特徴量"""
    silver_df = spark.read.table(f"{catalog}.{silver_schema}.positions")
    return build_position_features(silver_df)


@dp.table(name=f"{catalog}.{gold_schema}.game_summary")
@dp.expect("final_score_not_null", "final_score_cp IS NOT NULL")
@dp.expect("valid_players", "black_player IS NOT NULL AND white_player IS NOT NULL")
def game_summary():
    """Gold Table: ゲームサマリー"""
    silver_df = spark.read.table(f"{catalog}.{silver_schema}.positions")
    return build_game_summary(silver_df)
