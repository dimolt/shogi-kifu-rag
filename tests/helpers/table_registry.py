"""Unity Catalog上のSilver/Goldテーブル一覧（単一のソース）。

テーブルの追加・削除は本ファイルの SILVER_TABLES / GOLD_TABLES を更新するだけでよい。
このレジストリを起点に、以下がすべて導出される。

- fqn(table_name)  : FQN文字列を返す通常の関数（fixtureではない）
                      event_log() TVF等、FQN文字列そのものを直接必要とするテストから
                      直接importして使う。
- {table_name}_df  : tests/integration/integration_fixtures/tables.py で自動生成される
                      DataFrame fixture。内部でfqn()を呼ぶだけ。

FQNをfixture化しなかった理由:
FQNの算出はスキーマ名+テーブル名の文字列結合のみであり、setup/teardownや
scopeによるキャッシュを必要とするリソースではないため、fixtureにする意味がない。
普通の関数としてimportする方が呼び出し側もシンプルになる。
"""
from tests.helpers.constants import TEST_CATALOG, TEST_GOLD_SCHEMA, TEST_SILVER_SCHEMA

# テーブル名 -> スキーマ
SILVER_TABLES: dict[str, str] = {
    "positions": TEST_SILVER_SCHEMA,
    "floodgate_positions": TEST_SILVER_SCHEMA,
    "joseki_knowledge": TEST_SILVER_SCHEMA,
}

GOLD_TABLES: dict[str, str] = {
    "position_features": TEST_GOLD_SCHEMA,
    "game_summary": TEST_GOLD_SCHEMA,
}

# {table_name}_df fixtureの自動生成対象、およびfqn()の参照先。
ALL_TABLES: dict[str, str] = {**SILVER_TABLES, **GOLD_TABLES}


def fqn(table_name: str) -> str:
    """登録済みテーブルのFQN（catalog.schema.table）を返す。

    Args:
        table_name: ALL_TABLESに登録済みのテーブル名。

    Returns:
        str: テーブルのFQN。

    Raises:
        KeyError: table_nameがALL_TABLESに未登録の場合。
    """
    schema_name = ALL_TABLES[table_name]
    return f"{TEST_CATALOG}.{schema_name}.{table_name}"
