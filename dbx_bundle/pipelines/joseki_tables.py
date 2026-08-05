"""Silver Table: wikipedia_rawから定跡知識を登録するLakeflowパイプライン定義。"""

from pyspark import pipelines as dp

from dbx_bundle.transforms.joseki_to_silver import build_joseki_knowledge

catalog = spark.conf.get("bundle.catalog")
bronze_schema = spark.conf.get("bundle.bronze_schema")
silver_schema = spark.conf.get("bundle.silver_schema")


@dp.table(name=f"{catalog}.{silver_schema}.joseki_knowledge")
def joseki_knowledge():
    """Silver Table: wikipedia_rawから定跡知識を登録"""
    bronze_df = spark.read.table(f"{catalog}.{bronze_schema}.wikipedia_raw")
    return build_joseki_knowledge(bronze_df)
