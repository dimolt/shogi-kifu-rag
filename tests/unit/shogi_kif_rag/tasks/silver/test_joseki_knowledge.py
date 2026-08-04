from shogi_kif_rag.tasks.silver import joseki_knowledge


def test_extract_strategy_info_戦法名と本文をまとめて返す():
    """戦法名と本文から辞書を作成する。"""

    result = joseki_knowledge.extract_strategy_info("本文", "矢倉")

    assert result == {
        "strategy": "矢倉",
        "content": "本文",
        "source": "ja.wikipedia.org/wiki/矢倉",
    }
