from datetime import datetime

from pyspark.sql import SparkSession


def test_dedupロジック_fetched_at最大の1行のみ抽出する():
    """Bronzeテーブルからfetched_at最大の1行のみを抽出するdedupロジックを検証する。

    Arrange:
        ローカルSparkSessionでBronze相当のDataFrameを作成。
        同一strategyに対して複数のfetched_atを持つデータを準備。
    Act:
        ROW_NUMBER()ウィンドウ関数でdedupを実行。
    Assert:
        strategyごとにfetched_at最大の1行のみが抽出されること。
        raw_contentがcontentにリネームされていること。
        strategy/sourceが保持されていること。
    """
    spark = SparkSession.builder.master("local[1]").appName("test").getOrCreate()

    # Bronze相当のDataFrameを作成
    bronze_data = [
        ("矢倉", "本文1", datetime(2026, 1, 1, 10, 0, 0), "ja.wikipedia.org/wiki/矢倉"),
        ("矢倉", "本文2", datetime(2026, 1, 2, 10, 0, 0), "ja.wikipedia.org/wiki/矢倉"),  # 最新
        ("四間飛車", "本文3", datetime(2026, 1, 1, 10, 0, 0), "ja.wikipedia.org/wiki/四間飛車"),
        ("四間飛車", "本文4", datetime(2026, 1, 3, 10, 0, 0), "ja.wikipedia.org/wiki/四間飛車"),  # 最新
    ]
    bronze_df = spark.createDataFrame(
        bronze_data,
        schema=["strategy", "raw_content", "fetched_at", "source"]
    )

    # 一時ビューを作成
    bronze_df.createOrReplaceTempView("wikipedia_raw")

    # dedupロジックを実行
    dedup_df = spark.sql("""
        WITH ranked AS (
            SELECT *,
                ROW_NUMBER() OVER (PARTITION BY strategy ORDER BY fetched_at DESC) as rn
            FROM wikipedia_raw
        )
        SELECT strategy, raw_content as content, source
        FROM ranked WHERE rn = 1
    """)

    # 結果を検証
    result = dedup_df.collect()
    assert len(result) == 2, "2つのstrategyが残るはず"

    # 矢倉の最新データが選ばれていること
    yagura_row = next(row for row in result if row.strategy == "矢倉")
    assert yagura_row.content == "本文2", "矢倉は最新の本文2が選ばれるべき"
    assert yagura_row.source == "ja.wikipedia.org/wiki/矢倉"

    # 四間飛車の最新データが選ばれていること
    shikenbisha_row = next(row for row in result if row.strategy == "四間飛車")
    assert shikenbisha_row.content == "本文4", "四間飛車は最新の本文4が選ばれるべき"
    assert shikenbisha_row.source == "ja.wikipedia.org/wiki/四間飛車"

    spark.stop()
