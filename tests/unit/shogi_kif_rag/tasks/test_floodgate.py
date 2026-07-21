import sys
import types
from datetime import datetime
from types import SimpleNamespace

import requests

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


def test_parse_csa_コメントと対局者名と手番を正しく抽出する():
    csa_text = "' comment\nN+先手\nN-後手\n+7776FU\n-3334FU\n"

    result = floodgate.parse_csa(csa_text)

    assert result == {
        "moves": [
            {"move_usi": "7776FU", "player": "black"},
            {"move_usi": "3334FU", "player": "white"},
        ],
        "black_player": "先手",
        "white_player": "後手",
    }


def test_analyze_game_棋譜から局面レコードを生成する():
    game = {
        "id": "game-1",
        "csa": "N+先手\nN-後手\n+7776FU\n-3334FU\n",
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


def test_fetch_floodgate_games_日ページとCSAの取得に成功すると棋譜を返す(monkeypatch):
    class FakeDateTime:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 2)

    day_url = "https://wdoor.c.u-tokyo.ac.jp/shogi/x/2024/01/02/"
    filename = "wdoor+floodgate-300-10F+a-vs-b+20240102.csa"
    csa_text = "+7776FU\n"

    responses = {
        day_url: SimpleNamespace(
            status_code=200, text=f'<a href="{filename}">CSA</a>'
        ),
        f"{day_url}{filename}": SimpleNamespace(status_code=200, text=csa_text),
    }

    def fake_get(url, timeout=None):
        return responses[url]

    monkeypatch.setattr(floodgate, "datetime", FakeDateTime)
    monkeypatch.setattr(floodgate.requests, "get", fake_get)

    result = floodgate.fetch_floodgate_games(days_back=1)

    assert result == [{"id": "wdoor+floodgate-300-10F+a-vs-b+20240102", "csa": csa_text}]


def test_fetch_floodgate_games_日ページの取得に失敗した日はスキップする(monkeypatch):
    class FakeDateTime:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 2)

    ok_day_url = "https://wdoor.c.u-tokyo.ac.jp/shogi/x/2024/01/01/"
    ng_day_url = "https://wdoor.c.u-tokyo.ac.jp/shogi/x/2024/01/02/"
    filename = "wdoor+floodgate-300-10F+a-vs-b+20240101.csa"
    csa_text = "+7776FU\n"

    responses = {
        ng_day_url: SimpleNamespace(status_code=404, text=""),
        ok_day_url: SimpleNamespace(
            status_code=200, text=f'<a href="{filename}">CSA</a>'
        ),
        f"{ok_day_url}{filename}": SimpleNamespace(status_code=200, text=csa_text),
    }

    def fake_get(url, timeout=None):
        return responses[url]

    monkeypatch.setattr(floodgate, "datetime", FakeDateTime)
    monkeypatch.setattr(floodgate.requests, "get", fake_get)

    result = floodgate.fetch_floodgate_games(days_back=2)

    assert result == [{"id": "wdoor+floodgate-300-10F+a-vs-b+20240101", "csa": csa_text}]


def test_fetch_floodgate_games_CSAの取得に失敗した対局はスキップする(monkeypatch):
    class FakeDateTime:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 2)

    day_url = "https://wdoor.c.u-tokyo.ac.jp/shogi/x/2024/01/02/"
    ok_filename = "wdoor+floodgate-300-10F+a-vs-b+20240102.csa"
    ng_filename = "wdoor+floodgate-300-10F+c-vs-d+20240102.csa"
    csa_text = "+7776FU\n"

    responses = {
        day_url: SimpleNamespace(
            status_code=200,
            text=f'<a href="{ok_filename}">CSA</a>'
            f'<a href="{ng_filename}">CSA</a>',
        ),
        f"{day_url}{ok_filename}": SimpleNamespace(status_code=200, text=csa_text),
        f"{day_url}{ng_filename}": SimpleNamespace(status_code=404, text=""),
    }

    def fake_get(url, timeout=None):
        return responses[url]

    monkeypatch.setattr(floodgate, "datetime", FakeDateTime)
    monkeypatch.setattr(floodgate.requests, "get", fake_get)

    result = floodgate.fetch_floodgate_games(days_back=1)

    assert result == [{"id": "wdoor+floodgate-300-10F+a-vs-b+20240102", "csa": csa_text}]


def test_fetch_floodgate_games_1日あたりの取得数はMAX_GAMES_PER_DAYで制限される(monkeypatch):
    class FakeDateTime:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 2)

    day_url = "https://wdoor.c.u-tokyo.ac.jp/shogi/x/2024/01/02/"
    filenames = [f"wdoor+floodgate-300-10F+g{i}-vs-h{i}+20240102.csa" for i in range(12)]
    day_html = "".join(f'<a href="{name}">CSA</a>' for name in filenames)

    responses = {day_url: SimpleNamespace(status_code=200, text=day_html)}
    for name in filenames:
        responses[f"{day_url}{name}"] = SimpleNamespace(status_code=200, text="+7776FU\n")

    def fake_get(url, timeout=None):
        return responses[url]

    monkeypatch.setattr(floodgate, "datetime", FakeDateTime)
    monkeypatch.setattr(floodgate.requests, "get", fake_get)

    result = floodgate.fetch_floodgate_games(days_back=1)

    assert len(result) == floodgate.MAX_GAMES_PER_DAY


def test_fetch_floodgate_games_日ページの取得がタイムアウトした日はスキップする(monkeypatch):
    """日ページの取得がタイムアウトした場合、その日をスキップして処理を継続する"""
    class FakeDateTime:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 2)

    ok_day_url = "https://wdoor.c.u-tokyo.ac.jp/shogi/x/2024/01/01/"
    ng_day_url = "https://wdoor.c.u-tokyo.ac.jp/shogi/x/2024/01/02/"
    filename = "wdoor+floodgate-300-10F+a-vs-b+20240101.csa"
    csa_text = "+7776FU\n"

    call_count = [0]

    def fake_get(url, timeout=None):
        call_count[0] += 1
        if url == ng_day_url:
            raise requests.Timeout("Connection timeout")
        return SimpleNamespace(status_code=200, text=f'<a href="{filename}">CSA</a>' if url == ok_day_url else csa_text)

    monkeypatch.setattr(floodgate, "datetime", FakeDateTime)
    monkeypatch.setattr(floodgate.requests, "get", fake_get)

    result = floodgate.fetch_floodgate_games(days_back=2)

    assert result == [{"id": "wdoor+floodgate-300-10F+a-vs-b+20240101", "csa": csa_text}]
    assert call_count[0] > 0  # リクエストが実行されたことを確認


def test_fetch_floodgate_games_CSAの取得がタイムアウトした対局はスキップする(monkeypatch):
    """CSAファイルの取得がタイムアウトした場合、その対局をスキップして処理を継続する"""
    class FakeDateTime:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 2)

    day_url = "https://wdoor.c.u-tokyo.ac.jp/shogi/x/2024/01/02/"
    ok_filename = "wdoor+floodgate-300-10F+a-vs-b+20240102.csa"
    ng_filename = "wdoor+floodgate-300-10F+c-vs-d+20240102.csa"
    csa_text = "+7776FU\n"

    def fake_get(url, timeout=None):
        if url == f"{day_url}{ng_filename}":
            raise requests.Timeout("Read timeout")
        return SimpleNamespace(
            status_code=200,
            text=f'<a href="{ok_filename}">CSA</a><a href="{ng_filename}">CSA</a>' if url == day_url else csa_text
        )

    monkeypatch.setattr(floodgate, "datetime", FakeDateTime)
    monkeypatch.setattr(floodgate.requests, "get", fake_get)

    result = floodgate.fetch_floodgate_games(days_back=1)

    assert result == [{"id": "wdoor+floodgate-300-10F+a-vs-b+20240102", "csa": csa_text}]


def test_fetch_floodgate_games_全てのリクエストがタイムアウトしても例外が発生しない(monkeypatch):
    """全てのリクエストがタイムアウトしても例外を握りつぶさず、空リストを返す"""
    class FakeDateTime:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 2)

    def fake_get(url, timeout=None):
        raise requests.Timeout("Connection timeout")

    monkeypatch.setattr(floodgate, "datetime", FakeDateTime)
    monkeypatch.setattr(floodgate.requests, "get", fake_get)

    result = floodgate.fetch_floodgate_games(days_back=2)

    assert result == []
