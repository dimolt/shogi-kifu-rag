"""Wikipediaから将棋の戦法解説を取得し、Silverテーブルへ書き込むジョブ。"""

import argparse
import logging
import time

import requests
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StringType,
    StructField,
    StructType,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ===== 定数 =====
API_SLEEP_SEC = 0.5

WIKIPEDIA_HEADERS: dict[str, str] = {
    "User-Agent": "ShogiKifuRAG/1.0 (educational research; contact@example.com)"
}

# Wikipediaから戦法解説を取得する戦法リスト
STRATEGIES = [
    # 振り飛車
    "四間飛車", "三間飛車", "向かい飛車", "中飛車", "ゴキゲン中飛車",
    # 居飛車
    "矢倉囲い", "相掛かり", "角換わり", "横歩取り",
    # 急戦
    "棒銀", "右四間飛車",
    # 囲い
    "美濃囲い", "穴熊", "舟囲い", "金無双",
    # その他
    "一手損角換わり", "石田流", "雁木囲い", "elmo囲い",
    # 戦法概念
    "将棋の戦法", "手筋 (将棋)", "定跡", "終盤 (将棋)",
]


class WikipediaFetchError(Exception):
    """Wikipedia記事の取得失敗。"""


def fetch_wikipedia_content(title: str) -> str:
    """Wikipedia APIから記事本文を取得する。

    Args:
        title: 記事タイトル。

    Returns:
        記事本文。記事が見つからない、または取得に失敗した場合は空文字を返す。
    """
    params: dict[str, str] = {
        "action": "query",
        "titles": title,
        "prop": "extracts",
        "explaintext": "1",
        "exsectionformat": "plain",
        "format": "json",
    }
    try:
        response = requests.get(
            "https://ja.wikipedia.org/w/api.php",
            params=params,
            headers=WIKIPEDIA_HEADERS,
            timeout=10,
        )
    except requests.RequestException as e:
        logger.warning("Wikipedia取得エラー: %s: %s", title, e)
        return ""

    if response.status_code != 200:
        logger.warning("Wikipedia取得失敗: %s HTTP %d", title, response.status_code)
        return ""

    pages = response.json().get("query", {}).get("pages", {})
    for page in pages.values():
        extract = page.get("extract", "")
        if extract:
            return extract

    logger.warning("Wikipedia本文なし: %s", title)
    return ""


def extract_strategy_info(content: str, strategy: str) -> dict:
    """戦法情報を抽出する。

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
    parser.add_argument("--silver_schema", required=True)
    args = parser.parse_args()

    spark = SparkSession.getActiveSession()

    if spark is None:
        raise RuntimeError("SparkSession is not available")

    strategy_data = []

    for strategy in STRATEGIES:
        content = fetch_wikipedia_content(strategy)

        if content:
            strategy_data.append(extract_strategy_info(content, strategy))
            logger.info("✅ %s: %d文字", strategy, len(content))
        else:
            logger.warning("❌ %s: 取得失敗", strategy)

        time.sleep(API_SLEEP_SEC)

    logger.info("取得完了: %d/%d件", len(strategy_data), len(STRATEGIES))

    # DataFrameの作成
    schema = StructType([
        StructField("strategy", StringType(), True),
        StructField("content", StringType(), True),
        StructField("source", StringType(), True),
    ])
    df = spark.createDataFrame(
        strategy_data,
        schema=schema,
    )

    (
        df.write
        .format("delta")
        .mode("overwrite")
        .saveAsTable(
            f"{args.catalog}.{args.silver_schema}.joseki_knowledge"
        )
    )


if __name__ == "__main__":
    main()
