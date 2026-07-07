"""テスト対象のUnity Catalogカタログ・スキーマ定数。

`tests/conftest.py`（FQN組み立て）と `tests/e2e/conftest.py`
（スキーマのdrop & recreate）の両方から参照される。
"""

TEST_CATALOG = "shogi"
TEST_SILVER_SCHEMA = "shogi_silver"
TEST_GOLD_SCHEMA = "shogi_gold"
