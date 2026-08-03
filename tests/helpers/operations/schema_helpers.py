"""Unity Catalogスキーマ操作用ヘルパー関数。

E2Eテストでのスキーマクリーンアップ処理を集約する。
"""

from pyspark.sql import SparkSession


def drop_tables_in_schema(spark: SparkSession, catalog: str, schema: str) -> None:
    """指定スキーマ内の全テーブル・Materialized Viewを削除する。

    LakeflowパイプラインのテーブルはMaterialized Viewとして実装されるため、
    DROP MATERIALIZED VIEWを使用して削除する。

    Args:
        spark: SparkSession
        catalog: カタログ名
        schema: スキーマ名
    """
    tables = spark.sql(f"SHOW TABLES IN {catalog}.{schema}")
    for row in tables.collect():
        table_name = row.tableName
        is_temp_view = row.isTemporary

        if not is_temp_view:
            # LakeflowパイプラインのテーブルはMaterialized Viewとして実装される
            spark.sql(f"DROP MATERIALIZED VIEW IF EXISTS {catalog}.{schema}.{table_name}")
        else:
            spark.sql(f"DROP TABLE IF EXISTS {catalog}.{schema}.{table_name}")
