
import pytest
from pytest_mock import MockerFixture

from shogi_kif_rag.rag.llm_client import LLMClient


@pytest.fixture
def sample_context() -> list[dict]:
    """テスト用の関連ドキュメントリストを提供する。"""
    return [
        {"text": "▲7六歩 △3四歩 ▲2六歩", "metadata": {"source": "kif_001"}},
        {"text": "▲2五歩 △8四歩 ▲7八金", "metadata": {"source": "kif_002"}},
    ]


@pytest.fixture
def mock_llm_client(mocker: MockerFixture) -> LLMClient:
    """generateメソッドをモック化したLLMClientを提供する。"""
    client = mocker.Mock(spec=LLMClient)
    client.generate.return_value = "生成された回答です。"
    return client
