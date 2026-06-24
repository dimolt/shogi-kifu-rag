import requests
from bs4 import BeautifulSoup
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StringType,
    StructField,
    StructType,
)

# Wikipediaから戦法解説を取得する戦法リスト
STRATEGIES = [
    "矢倉",
    "美濃囲い",
    "穴熊",
    "振り飛車",
    "居飛車",
    "四間飛車",
    "三間飛車",
    "中飛車",
    "向かい飛車",
    "角交換",
    "相掛かり",
    "腰掛け銀",
    "袖飛車",
    "雁木",
    "右玉",
    "左美濃",
    "ダイヤモンド美濃",
    "ツノ銀",
    "銀冠",
    "金銀美濃",
    "箱入り娘",
    "端美濃",
    "片美濃",
    "木村美濃",
    "堂々美濃",
    "四角美濃",
]


def fetch_wikipedia_content(title: str) -> str:
    """Wikipediaから記事を取得する
    Args:
        title: 記事タイトル
    Returns:
        記事内容
    """

    url = f"https://ja.wikipedia.org/wiki/{title}"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        content_div = soup.find("div", {"class": "mw-parser-output"})
        if content_div:
            # 不要な要素を削除
            for tag in content_div.find_all(["sup", "ref", "style"]):
                tag.decompose()
            return content_div.get_text(separator="\n", strip=True)
    return ""


def extract_strategy_info(content: str, strategy: str) -> dict:
    """戦法情報を抽出する
    Args:
        content: Wikipedia記事内容
        strategy: 戦法名

    Returns:
        戦法情報
    """
    return {
        "strategy": strategy,
        "content": content,
        "source": f"ja.wikipedia.org/wiki/{strategy}",
    }


def main():
    spark = SparkSession.getActiveSession()

    if spark is None:
        raise RuntimeError("SparkSession is not available")

    strategy_data = []

    for strategy in STRATEGIES:
        content = fetch_wikipedia_content(strategy)

        if content:
            strategy_data.append(
                extract_strategy_info(content, strategy)
            )

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
            "shogi.shogi_silver.joseki_knowledge"
        )
    )
