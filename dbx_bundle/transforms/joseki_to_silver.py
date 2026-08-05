"""Bronze層のwikipedia_rawからSilver層のjoseki_knowledgeへ変換する純粋関数。"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F  #noqa: N812
from pyspark.sql.window import Window


def build_joseki_knowledge(bronze_df: DataFrame) -> DataFrame:
    """Bronzeテーブルから定跡知識（Silver: joseki_knowledge）を生成する。

    fetched_at最大の1行のみを抽出し、重複排除を行う。

    Args:
        bronze_df: Bronzeテーブルのwikipedia_rawデータ。

    Returns:
        strategy, content, source列を持つSilver DataFrame。
    """

    window = Window.partitionBy("strategy").orderBy(F.col("fetched_at").desc())

    return (
        bronze_df
        .withColumn("rn", F.row_number().over(window))
        .filter(F.col("rn") == 1)
        .select(
            "strategy",
            F.col("raw_content").alias("content"),
            "source",
        )
    )
