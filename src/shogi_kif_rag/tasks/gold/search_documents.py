"""Goldテーブル群からSearch Documents Delta Tableを作成するジョブ。"""

import argparse
import logging

from pyspark.sql import SparkSession

from shogi_kif_rag.transforms.search_documents import build_search_documents

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Search Documents Delta Tableを作成するエントリポイント。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--gold_schema", required=True)
    args = parser.parse_args()

    spark = SparkSession.getActiveSession()
    if spark is None:
        raise RuntimeError("SparkSession is not available")

    logger.info("Goldテーブルからデータを読み込み開始")
    positions_df = spark.read.table(f"{args.catalog}.{args.gold_schema}.position_features") #noqa: E501
    floodgate_df = spark.read.table(f"{args.catalog}.{args.gold_schema}.floodgate_position_features")    #noqa: E501
    joseki_df = spark.read.table(f"{args.catalog}.{args.gold_schema}.joseki_features")

    logger.info("Search Documents DataFrameを生成開始")
    search_docs_df = build_search_documents(positions_df, floodgate_df, joseki_df)

    logger.info("Delta Tableに書き込み開始")
    (
        search_docs_df.write
            .format("delta")
            .mode("overwrite")
            .saveAsTable(f"{args.catalog}.{args.gold_schema}.search_documents")
    )

    logger.info("Search Documents Delta Table作成完了")


if __name__ == "__main__":
    main()
