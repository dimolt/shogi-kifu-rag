# docstring形式

Google Styleに従い、**日本語**で記述する。

```python
def process_order(order_id: str, retry: int = 3) -> dict:
    """注文データを処理して結果を返す。

    指定された注文IDに対して検証・変換・書き込みを行う。
    リトライ回数を超えた場合は OrderProcessingError を送出する。

    Args:
        order_id: 処理対象の注文ID。
        retry: リトライ最大回数。デフォルトは3。

    Returns:
        処理結果を含む辞書。キーは "status", "processed_at"。

    Raises:
        OrderProcessingError: 処理が失敗しリトライ上限に達した場合。
        ValueError: order_id が空文字の場合。
    """
```

**ルール:**
- 1行サマリーは命令形（「返す」「処理する」「取得する」）
- `Args:`, `Returns:`, `Raises:` セクションは必要な場合のみ記載
- クラスには必ずクラスdocstringを書く（`__init__` には書かない）
