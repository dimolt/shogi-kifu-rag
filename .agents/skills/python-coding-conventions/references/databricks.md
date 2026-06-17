# Databricks パイプライン コーディング規約

## SparkSession の取得

```python
# ✅ Good: ヘルパー経由 or DI
def process(spark: SparkSession, input_path: str) -> DataFrame:
    return spark.read.format("delta").load(input_path)

# ❌ Bad: パイプライン内で直接ビルド
def process(input_path: str) -> DataFrame:
    spark = SparkSession.builder.getOrCreate()  # テストが困難になる
    ...
```

## DataFrame 変換スタイル

```python
# ✅ Good: 段階的な変数代入（可読性・デバッグ容易）
raw_df = spark.read.format("delta").load(path)
filtered_df = raw_df.filter(F.col("status") == "active")
result_df = filtered_df.withColumn("processed_at", F.current_timestamp())

# ❌ Bad: 長すぎるメソッドチェーン
result_df = (spark.read.format("delta").load(path)
             .filter(F.col("status") == "active")
             .withColumn("processed_at", F.current_timestamp())
             .withColumn(...)
             .withColumn(...))
```

## collect() の使用制限

```python
# ✅ Good: 集計の最終段のみ
summary = result_df.groupBy("status").count().collect()

# ❌ Bad: ループ内での collect
for row in df.collect():  # 大規模データでOOM
    process_row(row)
```

## スキーマ定義

```python
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

ORDER_SCHEMA = StructType([
    StructField("order_id", StringType(), nullable=False),
    StructField("amount", StringType(), nullable=True),
    StructField("created_at", TimestampType(), nullable=False),
])

# ✅ Good: スキーマ明示
df = spark.read.schema(ORDER_SCHEMA).format("csv").load(path)

# ❌ Bad: 本番コードでのスキーマ推論
df = spark.read.format("csv").option("inferSchema", "true").load(path)
```

## Delta Table 操作

```python
# テーブル書き込みは mergeSchema を明示的に制御
df.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", "false") \  # 意図しないスキーマ変更防止
    .saveAsTable("catalog.schema.table")
```

## ロギング

```python
import logging
logger = logging.getLogger(__name__)

# Databricksノートブック内では print も許容するが、
# モジュール・ライブラリコードでは必ず logging を使う
logger.info("処理開始: path=%s, count=%d", path, count)
```