"""Bronze層のwikipedia_rawからSilver層のjoseki_knowledgeへ変換するジョブ。"""

import argparse
import logging

from pyspark.sql import SparkSession

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def extract_strategy_info(content: str, strategy: str) -> dict:
    """戦法情報を抽出する（BronzeからSilverへの変換用）。

    Args:
        content: Wikipedia記事内容。
        strategy: 戦法名。

    Returns:
        戦法情報。
    """
    return {
        "strategy": strategy,
        "content": content,
        "source": f"ja.wikipedia.org/wiki/{strategy}",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--bronze_schema", required=True)
    parser.add_argument("--silver_schema", required=True)
    args = parser.parse_args()

    spark = SparkSession.getActiveSession()
    if spark is None:
        raise RuntimeError("SparkSession is not available")

    bronze_table = f"{args.catalog}.{args.bronze_schema}.wikipedia_raw"
    silver_table = f"{args.catalog}.{args.silver_schema}.joseki_knowledge"

    # dedup: fetched_at最大の1行のみ抽出
    dedup_df = spark.sql(f"""
        WITH ranked AS (
            SELECT *,
                ROW_NUMBER() OVER (PARTITION BY strategy ORDER BY fetched_at DESC) as rn
            FROM {bronze_table}
        )
        SELECT strategy, raw_content as content, source
        FROM ranked WHERE rn = 1
    """)

    logger.info("Silverテーブルへの書き込みを開始します: %s", silver_table)

    (
        dedup_df.write
        .format("delta")
        .mode("overwrite")
        .saveAsTable(silver_table)
    )

    logger.info("Silverテーブルへの書き込みが完了しました")


if __name__ == "__main__":
    main()
