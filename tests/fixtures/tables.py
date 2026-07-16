"""Silver/Gold テーブルをDataFrameとして提供するfixture群。

各テーブルのfixtureは同一パターン（table_registry.fqn()でFQNを求め、
`spark.table()` で読み込む）の繰り返しになるため、個別に関数を書く代わりに
table_registry.ALL_TABLES から動的に生成する。

テーブル一覧そのものは tests/table_registry.py が単一のソース。
新規テーブルを追加する場合は table_registry.py に1行追加するだけでよく、
本ファイルの変更は不要。
"""
import pytest
from pyspark.sql import DataFrame, SparkSession

from tests.helpers.table_registry import ALL_TABLES, fqn


def _make_table_df_fixture(table_name: str):
    """指定したテーブル名に対応する、テーブル全件読み込みのDataFrame fixtureを生成する。

    Args:
        table_name: table_registry.ALL_TABLESに登録済みのテーブル名。

    Returns:
        session scopeのDataFrame fixture関数。
    """

    @pytest.fixture(scope="session")
    def _table_df(spark: SparkSession) -> DataFrame:
        return spark.table(fqn(table_name))

    return _table_df


for _table_name in ALL_TABLES:
    globals()[f"{_table_name}_df"] = _make_table_df_fixture(_table_name)

del _table_name
