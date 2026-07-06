"""Silver層のテーブル定義に関する純粋関数群。"""

from pyspark.sql import DataFrame, SparkSession

from shogi_kif_rag.kif.schemas.shemas import get_spark_schema


def build_positions(spark: SparkSession, csv_path: str) -> DataFrame:
    """analysis.csvを読み込み、Silverテーブル用DataFrameを生成する。

    Args:
        spark: 読み込みに使用するSparkSession。
        csv_path: 読み込み対象のCSVファイルパス。

    Returns:
        get_spark_schema()に基づいて型付けされたDataFrame。
    """
    return spark.read.csv(csv_path, header=True, schema=get_spark_schema())
