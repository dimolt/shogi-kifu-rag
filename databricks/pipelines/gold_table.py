"""Gold Table: 局面特徴量・ゲームサマリーを生成するLakeflowパイプライン定義。"""

from pyspark import pipelines as dp

from .gold_transforms import build_game_summary, build_position_features

catalog = spark.conf.get("catalog")
silver_schema = spark.conf.get("silver_schema")


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
