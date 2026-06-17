---
name: python-coding-conventions
description: |
  Pythonコードを書く・レビューする・修正するすべての場面で必ず参照するコーディング規約。
  新規コード生成時、既存コードの修正・リファクタリング時、コードレビューのフィードバック時に適用する。
  Databricksパイプライン、pytest、汎用Pythonスクリプトが主な対象。
  ユーザーがPythonコードの生成・修正・レビューを依頼した場合は常にこのスキルを使うこと。
---

# Python コーディング規約

ベース: **Google Python Style Guide** + プロジェクト固有ルール  
対象: Databricksパイプライン / pytest / 汎用Pythonスクリプト  
docstring言語: **日本語**

---

## 1. 命名規則

| 対象 | スタイル | 例 |
|------|----------|----|
| 変数・関数 | `snake_case` | `order_count`, `fetch_records()` |
| クラス | `PascalCase` | `OrderProcessor`, `DataIngestionError` |
| 定数 | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT = 3` |
| プライベート | 先頭アンダースコア | `_internal_state` |
| モジュール | `snake_case` | `data_ingestion.py` |

**ルール:**
- 意味のある名前を使う。`x`, `tmp`, `data2` は原則禁止
- 略語は広く知られたもの（`df`, `config`, `msg`）のみ許可
- bool変数は `is_`, `has_`, `can_` プレフィックスを付ける（例: `is_valid`, `has_error`）

---

## 2. 型ヒント（Type Hints）

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

---

## 3. docstring形式

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

---

## 4. エラーハンドリング

### 4-1. bare except 禁止

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

### 4-2. カスタム例外クラス

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

---

## 5. import 順序

`isort` の標準ルールに従い、以下の順序でグループ分けしブランクラインで区切る。

```python
# 1. 標準ライブラリ
import os
from pathlib import Path

# 2. サードパーティ
import pyspark.sql.functions as F
from pyspark.sql import DataFrame

# 3. ローカル / プロジェクト内
from myproject.exceptions import DataIngestionError
from myproject.utils import load_config
```

**ルール:**
- `import X` と `from X import Y` は混在しない（同グループ内では `from` を後にまとめる）
- ワイルドカードインポート（`from x import *`）は禁止

---

## 6. Databricksパイプライン固有ルール

詳細は `references/databricks.md` を参照。要点:

- SparkセッションはDIで注入するか `get_spark()` ヘルパー経由で取得（直接 `SparkSession.builder` は避ける）
- DataFrame変換は関数チェーンより**段階的な変数代入**で可読性を保つ
- `collect()` はテスト・集計の最終段のみ許可。ループ内禁止
- スキーマは `StructType` で明示定義（スキーマ推論は開発時のみ）

---

## 7. テストコード規約（pytest）

詳細は `references/testing.md` を参照。要点:

- テスト関数名: `test_<対象関数名（英語）>_<状況（日本語）>_<期待結果（日本語）>` 形式
  - 例: `test_process_order_空のIDを渡すと_ValidationErrorを送出する`
- 1テスト1アサーション（複数アサートはAAAパターンで整理）
- フィクスチャは `conftest.py` に集約
- モックは `pytest-mock` の `mocker` フィクスチャを使用

---

## 8. その他の一般ルール

- 行長: **最大100文字**（Google Styleの88より少し広め）
- インデント: スペース4つ（タブ禁止）
- 文字列: シングルクォート統一（ただしdocstringはトリプルダブルクォート）
- `print()` はスクリプトの最終出力のみ許可。それ以外は `logging` を使う
- マジックナンバーは定数化する
- 関数は1つのことだけやる。30行を超えたら分割を検討

---

## クイックリファレンス（チェックリスト）

コードを書いたら以下を確認:

- [ ] 全関数に型ヒントがある
- [ ] docstringが日本語で書かれている
- [ ] `bare except` がない
- [ ] カスタム例外を使っている（組み込み以外）
- [ ] import が3グループに整理されている
- [ ] bool変数に `is_` / `has_` プレフィックスがある
- [ ] マジックナンバーが定数化されている