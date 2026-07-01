import sys
import types
from datetime import datetime
from types import SimpleNamespace

from shogi_kif_rag.tasks import floodgate

pyspark_module = types.ModuleType("pyspark")
pyspark_sql_module = types.ModuleType("pyspark.sql")
pyspark_sql_types_module = types.ModuleType("pyspark.sql.types")


class _SparkSession:
    @staticmethod
    def getActiveSession():
        return None


pyspark_module.sql = pyspark_sql_module
pyspark_sql_module.SparkSession = _SparkSession
pyspark_sql_module.types = pyspark_sql_types_module
pyspark_sql_types_module.IntegerType = lambda: None
pyspark_sql_types_module.StringType = lambda: None

sys.modules.setdefault("pyspark", pyspark_module)
sys.modules.setdefault("pyspark.sql", pyspark_sql_module)
sys.modules.setdefault("pyspark.sql.types", pyspark_sql_types_module)


def test_parse_csa_コメントと手番を正しく抽出する():
    csa_text = "' comment\n+7776FU\n-3334FU\n"

    result = floodgate.parse_csa(csa_text)

    assert result == {
        "moves": [
            {"move_usi": "7776FU", "player": "black"},
            {"move_usi": "3334FU", "player": "white"},
        ]
    }


def test_analyze_game_棋譜から局面レコードを生成する():
    game = {
        "id": "game-1",
        "black_player": "先手",
        "white_player": "後手",
        "csa": "+7776FU\n-3334FU\n",
    }

    result = floodgate.analyze_game(game)

    assert len(result) == 2
    assert result[0]["game_id"] == "game-1"
    assert result[0]["move_number"] == 0
    assert result[0]["move_usi"] == "7776FU"
    assert result[0]["player"] == "black"
    assert result[0]["black_player"] == "先手"
    assert result[0]["white_player"] == "後手"
    assert result[1]["move_usi"] == "3334FU"
    assert result[1]["player"] == "white"


def test_fetch_floodgate_games_成功した結果のみを返す(monkeypatch):
    class FakeDateTime:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 2)

    responses = [
        SimpleNamespace(status_code=200, json=lambda: [{"id": "a"}]),
        SimpleNamespace(status_code=404, json=lambda: [{"id": "b"}]),
    ]

    def fake_get(url):
        return responses.pop(0)

    monkeypatch.setattr(floodgate, "datetime", FakeDateTime)
    monkeypatch.setattr(floodgate.requests, "get", fake_get)

    result = floodgate.fetch_floodgate_games(days_back=2)

    assert result == [{"id": "a"}]
