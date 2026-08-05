"""Silver Table: wikipedia_rawから定跡知識を登録するLakeflowパイプライン定義。"""

from pyspark import pipelines as dp

from dbx_bundle.transforms.joseki import (
    build_joseki_features,
    build_joseki_knowledge,
)

catalog = spark.conf.get("bundle.catalog")
bronze_schema = spark.conf.get("bundle.bronze_schema")
silver_schema = spark.conf.get("bundle.silver_schema")
gold_schema = spark.conf.get("bundle.gold_schema")


@dp.table
def joseki_knowledge():
    """Silver Table: wikipedia_rawから定跡知識を登録"""
    bronze_df = spark.read.table(f"{catalog}.{bronze_schema}.wikipedia_raw")
    return build_joseki_knowledge(bronze_df)


@dp.table(name=f"{catalog}.{gold_schema}.joseki_features")
def joseki_features():
    """Gold Table: 定跡特徴量"""
    silver_df = spark.read.table(f"{catalog}.{silver_schema}.joseki_knowledge")
    return build_joseki_features(silver_df)
