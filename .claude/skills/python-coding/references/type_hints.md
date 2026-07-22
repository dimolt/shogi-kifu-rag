# 型ヒント（Type Hints）

**すべての関数シグネチャに型ヒントを付けること（必須）。**

```python
# ✅ Good
def fetch_orders(source_path: str, limit: int = 100) -> list[dict]:
    ...

# ❌ Bad
def fetch_orders(source_path, limit=100):
    ...
```

- `Optional[X]` の代わりに `X | None` を使う（Python 3.10+）
- コレクション型は組み込み小文字で書く: `list[str]`, `dict[str, int]`
- 複雑な型は `TypeAlias` または `TypedDict` で名前をつける

```python
from typing import TypedDict

class OrderRecord(TypedDict):
    order_id: str
    amount: float
    status: str
```
