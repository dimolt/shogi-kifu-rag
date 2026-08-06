"""Silver Table: floodgate_rawから対局棋譜局面を登録するLakeflowパイプライン定義。"""

from pyspark import pipelines as dp

from dbx_bundle.transforms.floodgate import (
    build_floodgate_features,
    build_floodgate_positions,
)

catalog = spark.conf.get("bundle.catalog")
bronze_schema = spark.conf.get("bundle.bronze_schema")
silver_schema = spark.conf.get("bundle.silver_schema")
gold_schema = spark.conf.get("bundle.gold_schema")


@dp.table
def floodgate_positions():
    """Silver Table: floodgate_rawから棋譜局面を登録"""
    bronze_df = spark.read.table(f"{catalog}.{bronze_schema}.floodgate_raw")
    return build_floodgate_positions(spark, bronze_df)


@dp.table(name=f"{catalog}.{gold_schema}.floodgate_position_features")
def floodgate_position_features():
    """Gold Table: floodgate局面特徴量"""
    silver_df = spark.read.table(f"{catalog}.{silver_schema}.floodgate_positions")
    return build_floodgate_features(silver_df)
