"""pytest共有フィクスチャ。"""

import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark() -> SparkSession:
    """unitテスト用SparkSessionを提供する。"""
    return (
        SparkSession.builder.master("local[1]")
        .appName("shogi_kif_rag_test")
        .getOrCreate()
    )
