# 命名規則

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
