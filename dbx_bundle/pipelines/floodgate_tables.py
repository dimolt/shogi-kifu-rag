"""Silver Table: floodgate_rawから対局棋譜局面を登録するLakeflowパイプライン定義。"""

from pyspark import pipelines as dp

from dbx_bundle.transforms.floodgate import build_floodgate_positions

catalog = spark.conf.get("bundle.catalog")
bronze_schema = spark.conf.get("bundle.bronze_schema")
silver_schema = spark.conf.get("bundle.silver_schema")


@dp.table
def floodgate_positions():
    """Silver Table: floodgate_rawから棋譜局面を登録"""
    bronze_df = spark.read.table(f"{catalog}.{bronze_schema}.floodgate_raw")
    return build_floodgate_positions(spark, bronze_df)
