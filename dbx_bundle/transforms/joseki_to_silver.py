"""Bronze層のwikipedia_rawからSilver層のjoseki_knowledgeへ変換する純粋関数。"""

from pyspark.sql import DataFrame


def build_joseki_knowledge(bronze_df: DataFrame) -> DataFrame:
    """Bronzeテーブルから定跡知識（Silver: joseki_knowledge）を生成する。

    fetched_at最大の1行のみを抽出し、重複排除を行う。

    Args:
        bronze_df: Bronzeテーブルのwikipedia_rawデータ。

    Returns:
        strategy, content, source列を持つSilver DataFrame。
    """
    bronze_df.createOrReplaceTempView("wikipedia_raw_temp")

    result_df = bronze_df.sqlCtx.sql("""
        WITH ranked AS (
            SELECT *,
                ROW_NUMBER() OVER (PARTITION BY strategy ORDER BY fetched_at DESC) as rn
            FROM wikipedia_raw_temp
        )
        SELECT strategy, raw_content as content, source
        FROM ranked WHERE rn = 1
    """)

    return result_df
