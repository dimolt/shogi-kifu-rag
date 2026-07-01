# エラーハンドリング

## bare except 禁止

```python
# ❌ 絶対禁止
try:
    process()
except:
    pass

# ❌ これも禁止
try:
    process()
except Exception:
    pass  # 握り潰し

# ✅ Good
try:
    process()
except ValueError as e:
    logger.warning("入力値エラー: %s", e)
    raise
```

## カスタム例外クラス

プロジェクト内で一貫した例外階層を定義する。

```python
# exceptions.py に集約する
class AppBaseError(Exception):
    """アプリケーション基底例外。"""

class DataIngestionError(AppBaseError):
    """データ取り込み処理の失敗。"""

class ValidationError(AppBaseError):
    """入力データの検証失敗。"""
    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"{field}: {reason}")
```

**ルール:**
- 組み込み例外を直接 `raise` するのは `ValueError`, `TypeError`, `NotImplementedError` のみ許可
- それ以外はカスタム例外を使う
- 例外を再送出する場合は `raise` のみ（`raise e` は避ける）
- `except X as e: raise Y(msg) from e` でチェーンを保持する
