"""tasks/bronze/floodgate_raw.py のユニットテスト。"""

from datetime import datetime
from types import SimpleNamespace

import requests

from shogi_kif_rag.tasks.bronze import floodgate_raw


def test_fetch_floodgate_games_日ページとCSAの取得に成功すると棋譜を返す(monkeypatch):
    class FakeDateTime:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 2)

    day_url = "https://wdoor.c.u-tokyo.ac.jp/shogi/x/2024/01/02/"
    filename = "wdoor+floodgate-300-10F+a-vs-b+20240102.csa"
    csa_text = "+7776FU\n"

    responses = {
        day_url: SimpleNamespace(status_code=200, text=f'<a href="{filename}">CSA</a>'),
        f"{day_url}{filename}": SimpleNamespace(status_code=200, text=csa_text),
    }

    def fake_get(url, timeout=None):
        return responses[url]

    monkeypatch.setattr(floodgate_raw, "datetime", FakeDateTime)
    monkeypatch.setattr(floodgate_raw.requests, "get", fake_get)

    result = floodgate_raw.fetch_floodgate_games(days_back=1)

    assert result == [
        {
            "game_id": "wdoor+floodgate-300-10F+a-vs-b+20240102",
            "csa": csa_text,
            "source": f"{day_url}{filename}",
        }
    ]


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
        ok_day_url: SimpleNamespace(status_code=200, text=f'<a href="{filename}">CSA</a>'),
        f"{ok_day_url}{filename}": SimpleNamespace(status_code=200, text=csa_text),
    }

    def fake_get(url, timeout=None):
        return responses[url]

    monkeypatch.setattr(floodgate_raw, "datetime", FakeDateTime)
    monkeypatch.setattr(floodgate_raw.requests, "get", fake_get)

    result = floodgate_raw.fetch_floodgate_games(days_back=2)

    assert result == [
        {
            "game_id": "wdoor+floodgate-300-10F+a-vs-b+20240101",
            "csa": csa_text,
            "source": f"{ok_day_url}{filename}",
        }
    ]


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
            text=f'<a href="{ok_filename}">CSA</a>' f'<a href="{ng_filename}">CSA</a>',
        ),
        f"{day_url}{ok_filename}": SimpleNamespace(status_code=200, text=csa_text),
        f"{day_url}{ng_filename}": SimpleNamespace(status_code=404, text=""),
    }

    def fake_get(url, timeout=None):
        return responses[url]

    monkeypatch.setattr(floodgate_raw, "datetime", FakeDateTime)
    monkeypatch.setattr(floodgate_raw.requests, "get", fake_get)

    result = floodgate_raw.fetch_floodgate_games(days_back=1)

    assert result == [
        {
            "game_id": "wdoor+floodgate-300-10F+a-vs-b+20240102",
            "csa": csa_text,
            "source": f"{day_url}{ok_filename}",
        }
    ]


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

    monkeypatch.setattr(floodgate_raw, "datetime", FakeDateTime)
    monkeypatch.setattr(floodgate_raw.requests, "get", fake_get)

    result = floodgate_raw.fetch_floodgate_games(days_back=1)

    assert len(result) == floodgate_raw.MAX_GAMES_PER_DAY


def test_fetch_floodgate_games_日ページの取得がタイムアウトした日はスキップする(monkeypatch):
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
        return SimpleNamespace(
            status_code=200,
            text=f'<a href="{filename}">CSA</a>' if url == ok_day_url else csa_text,
        )

    monkeypatch.setattr(floodgate_raw, "datetime", FakeDateTime)
    monkeypatch.setattr(floodgate_raw.requests, "get", fake_get)

    result = floodgate_raw.fetch_floodgate_games(days_back=2)

    assert result == [
        {
            "game_id": "wdoor+floodgate-300-10F+a-vs-b+20240101",
            "csa": csa_text,
            "source": f"{ok_day_url}{filename}",
        }
    ]
    assert call_count[0] > 0  # リクエストが実行されたことを確認


def test_fetch_floodgate_games_CSAの取得がタイムアウトした対局はスキップする(monkeypatch):
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
            text=(
                f'<a href="{ok_filename}">CSA</a><a href="{ng_filename}">CSA</a>'
                if url == day_url
                else csa_text
            ),
        )

    monkeypatch.setattr(floodgate_raw, "datetime", FakeDateTime)
    monkeypatch.setattr(floodgate_raw.requests, "get", fake_get)

    result = floodgate_raw.fetch_floodgate_games(days_back=1)

    assert result == [
        {
            "game_id": "wdoor+floodgate-300-10F+a-vs-b+20240102",
            "csa": csa_text,
            "source": f"{day_url}{ok_filename}",
        }
    ]


def test_fetch_floodgate_games_全てのリクエストがタイムアウトしても例外が発生しない(monkeypatch):
    """全てのリクエストがタイムアウトしても例外を握りつぶさず、空リストを返す"""

    class FakeDateTime:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 2)

    def fake_get(url, timeout=None):
        raise requests.Timeout("Connection timeout")

    monkeypatch.setattr(floodgate_raw, "datetime", FakeDateTime)
    monkeypatch.setattr(floodgate_raw.requests, "get", fake_get)

    result = floodgate_raw.fetch_floodgate_games(days_back=2)

    assert result == []
