import pytest
import requests

from shogi_kif_rag.tasks import wikipedia


def test_fetch_wikipedia_content_正常なHTMLを渡すと本文を返す(monkeypatch):
    """正常なHTMLを受け取った場合、不要な要素を取り除いた本文を返す。"""

    class FakeResponse:
        status_code = 200
        content = (
            '<div class="mw-parser-output"><sup>1</sup><ref>ref</ref>'
            '<p>本文1</p><p>本文2</p></div>'
        ).encode("utf-8")

    def fake_get(url: str):
        assert url == "https://ja.wikipedia.org/wiki/矢倉"
        return FakeResponse()

    monkeypatch.setattr(wikipedia.requests, "get", fake_get)

    result = wikipedia.fetch_wikipedia_content("矢倉")

    assert result == "本文1\n本文2"


def test_fetch_wikipedia_content_通信エラー時は例外を送出する(monkeypatch):
    """通信エラー時は例外を送出する。"""

    def fake_get(url: str):
        raise requests.RequestException("network error")

    monkeypatch.setattr(wikipedia.requests, "get", fake_get)

    with pytest.raises(requests.RequestException):
        wikipedia.fetch_wikipedia_content("矢倉")


def test_extract_strategy_info_戦法名と本文をまとめて返す():
    """戦法名と本文から辞書を作成する。"""

    result = wikipedia.extract_strategy_info("本文", "矢倉")

    assert result == {
        "strategy": "矢倉",
        "content": "本文",
        "source": "ja.wikipedia.org/wiki/矢倉",
    }
