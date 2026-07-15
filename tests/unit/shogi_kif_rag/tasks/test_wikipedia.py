import requests

from shogi_kif_rag.tasks import wikipedia


class FakeResponse:
    """requests.Response の簡易フェイク。"""

    def __init__(self, status_code: int = 200, json_data: dict | None = None) -> None:
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self) -> dict:
        return self._json_data


def test_fetch_wikipedia_content_正常系のとき_extractを返す(monkeypatch):
    """APIレスポンスにextractが含まれる場合、その本文を返す。"""

    def fake_get(url, params=None, headers=None, timeout=None):
        assert url == "https://ja.wikipedia.org/w/api.php"
        assert params["titles"] == "矢倉"
        assert params["action"] == "query"
        assert params["prop"] == "extracts"
        assert params["explaintext"] == "1"
        assert headers == wikipedia.WIKIPEDIA_HEADERS
        assert timeout == 10
        return FakeResponse(
            status_code=200,
            json_data={"query": {"pages": {"123": {"extract": "本文1\n本文2"}}}},
        )

    monkeypatch.setattr(wikipedia.requests, "get", fake_get)

    result = wikipedia.fetch_wikipedia_content("矢倉")

    assert result == "本文1\n本文2"


def test_fetch_wikipedia_content_HTTPステータスが200以外のとき_空文字を返す(monkeypatch):
    """HTTPステータスが200以外の場合、空文字を返す。"""

    def fake_get(url, params=None, headers=None, timeout=None):
        return FakeResponse(status_code=404)

    monkeypatch.setattr(wikipedia.requests, "get", fake_get)

    result = wikipedia.fetch_wikipedia_content("存在しない戦法")

    assert result == ""


def test_fetch_wikipedia_content_本文が存在しないとき_空文字を返す(monkeypatch):
    """該当ページはあるがextractが空の場合、空文字を返す。"""

    def fake_get(url, params=None, headers=None, timeout=None):
        return FakeResponse(
            status_code=200,
            json_data={"query": {"pages": {"-1": {"missing": ""}}}},
        )

    monkeypatch.setattr(wikipedia.requests, "get", fake_get)

    result = wikipedia.fetch_wikipedia_content("矢倉")

    assert result == ""


def test_fetch_wikipedia_content_通信エラー時は空文字を返す(monkeypatch):
    """通信エラー時は例外を送出せず、空文字を返す。"""

    def fake_get(url, params=None, headers=None, timeout=None):
        raise requests.RequestException("network error")

    monkeypatch.setattr(wikipedia.requests, "get", fake_get)

    result = wikipedia.fetch_wikipedia_content("矢倉")

    assert result == ""


def test_extract_strategy_info_戦法名と本文をまとめて返す():
    """戦法名と本文から辞書を作成する。"""

    result = wikipedia.extract_strategy_info("本文", "矢倉")

    assert result == {
        "strategy": "矢倉",
        "content": "本文",
        "source": "ja.wikipedia.org/wiki/矢倉",
    }
