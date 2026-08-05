"""joseki_to_silver.pyのユニットテスト。"""

from datetime import datetime

from dbx_bundle.transforms.joseki import (
    build_joseki_features,
    build_joseki_knowledge,
)


def test_build_joseki_knowledge_fetched_at最大の1行のみ抽出される(spark) -> None:
    # Arrange: 同じstrategyで複数のfetched_atを持つデータ
    data = [
        ("四間飛車", "content1", datetime(2024, 1, 1), "source1"),
        ("四間飛車", "content2", datetime(2024, 1, 2), "source2"),  # 最新
        ("四間飛車", "content3", datetime(2024, 1, 1, 12, 0), "source3"),
    ]
    schema = "strategy STRING, raw_content STRING, fetched_at TIMESTAMP, source STRING"
    df = spark.createDataFrame(data, schema=schema)

    # Act
    result_df = build_joseki_knowledge(df)

    # Assert
    assert result_df.count() == 1
    row = result_df.first()
    assert row["strategy"] == "四間飛車"
    assert row["content"] == "content2"  # 最新のfetched_atのcontent
    assert row["source"] == "source2"


def test_build_joseki_knowledge_異なるstrategyはそれぞれ1行ずつ残る(spark) -> None:
    # Arrange: 異なるstrategyのデータ
    data = [
        ("四間飛車", "content1", datetime(2024, 1, 1), "source1"),
        ("三間飛車", "content2", datetime(2024, 1, 2), "source2"),
        ("四間飛車", "content3", datetime(2024, 1, 2), "source3"),  # 四間飛車の最新
    ]
    schema = "strategy STRING, raw_content STRING, fetched_at TIMESTAMP, source STRING"
    df = spark.createDataFrame(data, schema=schema)

    # Act
    result_df = build_joseki_knowledge(df)

    # Assert
    assert result_df.count() == 2
    strategies = {row["strategy"] for row in result_df.collect()}
    assert strategies == {"四間飛車", "三間飛車"}


def test_build_joseki_knowledge_出力列が仕様通りである(spark) -> None:
    # Arrange
    data = [("四間飛車", "content1", datetime(2024, 1, 1), "source1")]
    schema = "strategy STRING, raw_content STRING, fetched_at TIMESTAMP, source STRING"
    df = spark.createDataFrame(data, schema=schema)

    # Act
    result_df = build_joseki_knowledge(df)

    # Assert
    expected_columns = {"strategy", "content", "source"}
    assert set(result_df.columns) == expected_columns


def test_build_joseki_knowledge_raw_contentがcontentにリネームされる(spark) -> None:
    # Arrange
    data = [("四間飛車", "original_content", datetime(2024, 1, 1), "source1")]
    schema = "strategy STRING, raw_content STRING, fetched_at TIMESTAMP, source STRING"
    df = spark.createDataFrame(data, schema=schema)

    # Act
    result_df = build_joseki_knowledge(df)

    # Assert
    assert result_df.first()["content"] == "original_content"


# --- build_joseki_features --------------------------------------------------


def test_build_joseki_features_Silverの列がそのままGoldに引き継がれる(spark) -> None:
    # Arrange
    data = [("四間飛車", "content1", "source1")]
    schema = "strategy STRING, content STRING, source STRING"
    df = spark.createDataFrame(data, schema=schema)

    # Act
    result_df = build_joseki_features(df)

    # Assert
    row = result_df.first()
    assert row["strategy"] == "四間飛車"
    assert row["content"] == "content1"
    assert row["source"] == "source1"


def test_build_joseki_features_search_textはcontentと同じ内容になる(spark) -> None:
    # Arrange
    data = [("四間飛車", "test_content", "source1")]
    schema = "strategy STRING, content STRING, source STRING"
    df = spark.createDataFrame(data, schema=schema)

    # Act
    result_df = build_joseki_features(df)

    # Assert
    assert result_df.first()["search_text"] == "test_content"


def test_build_joseki_features_出力列が仕様通りの4列になる(spark) -> None:
    # Arrange
    data = [("四間飛車", "content1", "source1")]
    schema = "strategy STRING, content STRING, source STRING"
    df = spark.createDataFrame(data, schema=schema)

    # Act
    result_df = build_joseki_features(df)

    # Assert
    expected_columns = {"strategy", "content", "source", "search_text"}
    assert set(result_df.columns) == expected_columns


def test_build_joseki_features_空データ時でもエラーにならない(spark) -> None:
    # Arrange: 空のDataFrame
    data = []
    schema = "strategy STRING, content STRING, source STRING"
    df = spark.createDataFrame(data, schema=schema)

    # Act
    result_df = build_joseki_features(df)

    # Assert
    assert result_df.count() == 0
    assert set(result_df.columns) == {"strategy", "content", "source", "search_text"}
