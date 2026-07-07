"""Gold Table: 局面特徴量・ゲームサマリーを生成するLakeflowパイプライン定義。"""

from gold_transforms import build_game_summary, build_position_features
from pyspark import pipelines as dp

catalog = spark.conf.get("catalog")
silver_schema = spark.conf.get("silver_schema")


@dp.table
@dp.expect("valid_move_quality", "move_quality IN ('start', 'best', 'blunder', 'normal')")  #noqa: E501
def position_features():
    """Gold Table: 局面特徴量"""
    silver_df = spark.read.table(f"{catalog}.{silver_schema}.positions")
    return build_position_features(silver_df)


@dp.table
@dp.expect("final_score_not_null", "final_score_cp IS NOT NULL")
@dp.expect("valid_players", "black_player IS NOT NULL AND white_player IS NOT NULL")
def game_summary():
    """Gold Table: ゲームサマリー"""
    silver_df = spark.read.table(f"{catalog}.{silver_schema}.positions")
    return build_game_summary(silver_df)
