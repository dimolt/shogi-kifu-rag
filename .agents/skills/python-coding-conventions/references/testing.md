# テストコード規約（pytest）

## テスト関数の命名

```
test_<対象関数名>_<状況（日本語）>_<期待結果（日本語）>
```

- 対象関数名: 英語（実装の関数名そのまま）
- 状況・期待結果: 日本語で仕様として記述する

```python
# ✅ Good
def test_process_order_有効なIDを渡すと_処理結果の辞書を返す():
def test_process_order_空のIDを渡すと_ValidationErrorを送出する():
def test_fetch_records_パスが存在しないと_DataIngestionErrorを送出する():

# ❌ Bad
def test_process():          # 状況・期待結果がない
def test_error_case():       # 対象関数名がない
def test_process_order_when_valid_id_returns_success_dict():  # 状況・期待結果が英語
```

## AAAパターン（Arrange / Act / Assert）

```python
def test_calculate_total_when_discount_applied_returns_correct_amount():
    # Arrange
    items = [{"price": 1000}, {"price": 500}]
    discount_rate = 0.1

    # Act
    result = calculate_total(items, discount_rate)

    # Assert
    assert result == 1350
```

- コメント（# Arrange 等）は複雑なテストにのみ付ける
- 1テスト1アサートを基本とする（複数必要な場合はAAAで整理）

## フィクスチャ

```python
# conftest.py に集約
import pytest
from pyspark.sql import SparkSession

@pytest.fixture(scope="session")
def spark() -> SparkSession:
    """テスト用SparkSessionを提供する。"""
    return SparkSession.builder \
        .master("local[1]") \
        .appName("test") \
        .getOrCreate()

@pytest.fixture
def sample_order() -> dict:
    """テスト用注文データを提供する。"""
    return {"order_id": "ORD-001", "amount": 1000.0, "status": "active"}
```

## モック（pytest-mock）

```python
def test_fetch_orders_calls_storage_once(mocker):
    # Arrange
    mock_storage = mocker.patch("mymodule.storage.read")
    mock_storage.return_value = [{"order_id": "ORD-001"}]

    # Act
    result = fetch_orders("/path/to/data")

    # Assert
    mock_storage.assert_called_once_with("/path/to/data")
    assert len(result) == 1
```

## 例外のテスト

```python
import pytest
from myproject.exceptions import ValidationError

def test_process_order_when_empty_id_raises_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        process_order(order_id="")

    assert exc_info.value.field == "order_id"
```

## Databricks (PySpark) テスト

```python
def test_filter_active_orders_returns_only_active(spark):
    # Arrange
    data = [("ORD-001", "active"), ("ORD-002", "cancelled")]
    df = spark.createDataFrame(data, schema=["order_id", "status"])

    # Act
    result_df = filter_active_orders(df)

    # Assert
    assert result_df.count() == 1
    assert result_df.first()["order_id"] == "ORD-001"
```

## ディレクトリ構成

```
tests/
├── conftest.py          # 共有フィクスチャ
├── unit/
│   ├── test_processor.py
│   └── test_validator.py
└── integration/
    └── test_pipeline.py
```