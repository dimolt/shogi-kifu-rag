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


def build_joseki_features(silver_df: DataFrame) -> DataFrame:
    """Silverテーブルから定跡特徴量（Gold: joseki_features）を生成する。

    Silverのstrategy/content/sourceをそのまま横流しし、search_text列を追加する。
    search_textは既存の_rebuild_josekiと同様、contentをそのまま使う。

    Args:
        silver_df: Silverテーブルのjoseki_knowledgeデータ。

    Returns:
        strategy, content, source, search_text列を持つGold DataFrame。
    """
    featured_df = silver_df.withColumn(
        "search_text",
        F.col("content"),
    )

    return featured_df.select(
        "strategy",
        "content",
        "source",
        "search_text",
    )
