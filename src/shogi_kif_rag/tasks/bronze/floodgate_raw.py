"""Floodgateから棋譜を取得し、Bronzeテーブルへ書き込むジョブ。"""

import argparse
import logging
import re
from datetime import datetime, timedelta

import requests
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StringType,
    StructField,
    StructType,
    TimestampType,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

FLOODGATE_BASE = "https://wdoor.c.u-tokyo.ac.jp/shogi/x"
MAX_GAMES_PER_DAY = 10
DEFAULT_DAYS_BACK = 3


def fetch_floodgate_games(days_back: int = DEFAULT_DAYS_BACK) -> list[dict]:
    """Floodgateから指定日数分の棋譜（生CSA）を取得する。

    Args:
        days_back: 取得する日数。

    Returns:
        棋譜リスト（各要素は game_id / csa / source を持つ辞書）。
    """
    games: list[dict] = []

    for i in range(days_back):
        date = datetime.now() - timedelta(days=i)
        day_url = f"{FLOODGATE_BASE}/{date.year}/{date.month:02d}/{date.day:02d}/"

        try:
            day_response = requests.get(day_url, timeout=10)
        except requests.RequestException as e:
            logger.warning("Floodgate日ページ取得エラー: %s: %s", day_url, e)
            continue
        if day_response.status_code != 200:
            continue

        filenames = re.findall(r'(wdoor\+floodgate[^\s"]+\.csa)', day_response.text)
        urls = [f"{day_url}{fname}" for fname in filenames][:MAX_GAMES_PER_DAY]

        for url in urls:
            try:
                game_response = requests.get(url, timeout=15)
            except requests.RequestException as e:
                logger.warning("Floodgate棋譜取得エラー: %s: %s", url, e)
                continue
            if game_response.status_code != 200:
                continue
            game_id = url.split("/")[-1].rsplit(".", 1)[0]
            games.append({"game_id": game_id, "csa": game_response.text, "source": url})

    return games


def main() -> None:
    """Floodgate棋譜を取得しBronzeテーブルへ書き込むエントリポイント。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--bronze_schema", required=True)
    parser.add_argument("--days_back", type=int, default=DEFAULT_DAYS_BACK)
    args = parser.parse_args()

    spark = SparkSession.getActiveSession()
    if spark is None:
        raise RuntimeError("SparkSession is not available")

    games = fetch_floodgate_games(days_back=args.days_back)
    logger.info("取得完了: %d件", len(games))

    fetched_at = datetime.now()
    rows = [
        {
            "game_id": g["game_id"],
            "csa": g["csa"],
            "fetched_at": fetched_at,
            "source": g["source"],
        }
        for g in games
    ]

    schema = StructType([
        StructField("game_id", StringType(), True),
        StructField("csa", StringType(), True),
        StructField("fetched_at", TimestampType(), True),
        StructField("source", StringType(), True),
    ])
    df = spark.createDataFrame(rows, schema=schema)

    (
        df.write
        .format("delta")
        .mode("append")
        .saveAsTable(f"{args.catalog}.{args.bronze_schema}.floodgate_raw")
    )


if __name__ == "__main__":
    main()
