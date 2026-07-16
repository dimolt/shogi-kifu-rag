"""テスト対象のUnity Catalogカタログ・スキーマ定数。

[tests/conftest.py](cci:7://file:///c:/shogi-kif-rag/tests/conftest.py:0:0-0:0)（FQN組み立て）
[tests/e2e/conftest.py](cci:7://file:///c:/shogi-kif-rag/tests/e2e/conftest.py:0:0-0:0)（スキーマのdrop & recreate）
の両方から参照される。
"""
import os

TEST_CATALOG = os.environ.get("TEST_CATALOG", "shogi_test")
TEST_SILVER_SCHEMA = "shogi_silver"
TEST_GOLD_SCHEMA = "shogi_gold"
