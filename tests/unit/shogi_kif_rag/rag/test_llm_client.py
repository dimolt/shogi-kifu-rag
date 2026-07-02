"""LLMClientのユニットテスト。"""

import sys
from unittest.mock import MagicMock

import pytest

from shogi_kif_rag.rag.llm_client import LLMClient


@pytest.fixture
def mock_secrets(mocker):
    """secrets取得関数をモック化する。"""
    mocker.patch("shogi_kif_rag.rag.llm_client.get_gemini_api_key", return_value="dummy-gemini-key")
    mocker.patch("shogi_kif_rag.rag.llm_client.get_groq_api_key", return_value="dummy-groq-key")


@pytest.fixture
def mock_genai_module(mocker):
    """google.generativeaiモジュールをモック化する。"""
    mock_module = MagicMock()
    mocker.patch.dict(sys.modules, {"google.generativeai": mock_module})
    return mock_module


@pytest.fixture
def mock_groq_module(mocker):
    """groqモジュールをモック化する。"""
    mock_module = MagicMock()
    mocker.patch.dict(sys.modules, {"groq": mock_module})
    return mock_module


class TestLLMClientInit:
    """__init__メソッドのテスト。"""

    def test___init___APIキーが取得できる場合_インスタンス変数に設定される(self, mock_secrets):
        # Act
        client = LLMClient()

        # Assert
        assert client.gemini_api_key == "dummy-gemini-key"

    def test___init___初期状態では_use_geminiがTrueである(self, mock_secrets):
        # Act
        client = LLMClient()

        # Assert
        assert client.use_gemini is True


class TestLLMClientGenerate:
    """generateメソッドのテスト。"""

    def test_generate_Geminiが正常応答する場合_Geminiの生成結果を返す(
        self, mock_secrets, mock_genai_module
    ):
        # Arrange
        mock_response = MagicMock()
        mock_response.text = "Geminiの応答"
        mock_genai_module.GenerativeModel.return_value.generate_content.return_value = (
            mock_response
        )
        client = LLMClient()

        # Act
        result = client.generate("テストプロンプト")

        # Assert
        assert result == "Geminiの応答"

    def test_generate_Geminiが正常応答する場合_APIキー付きでconfigureが呼ばれる(
        self, mock_secrets, mock_genai_module
    ):
        # Arrange
        mock_response = MagicMock()
        mock_response.text = "応答"
        mock_genai_module.GenerativeModel.return_value.generate_content.return_value = (
            mock_response
        )
        client = LLMClient()

        # Act
        client.generate("テストプロンプト")

        # Assert
        mock_genai_module.configure.assert_called_once_with(api_key="dummy-gemini-key")

    def test_generate_Geminiが正常応答する場合_Groqは呼ばれない(
        self, mock_secrets, mock_genai_module, mock_groq_module
    ):
        # Arrange
        mock_response = MagicMock()
        mock_response.text = "Geminiの応答"
        mock_genai_module.GenerativeModel.return_value.generate_content.return_value = (
            mock_response
        )
        client = LLMClient()

        # Act
        client.generate("テストプロンプト")

        # Assert
        mock_groq_module.Groq.assert_not_called()

    def test_generate_Geminiキーがない場合_Groqにフォールバックする(self, mocker, mock_groq_module):
        # Arrange
        mocker.patch("shogi_kif_rag.rag.llm_client.get_gemini_api_key", return_value=None)
        mocker.patch(
            "shogi_kif_rag.rag.llm_client.get_groq_api_key", return_value="dummy-groq-key"
        )
        mock_groq_module.Groq.return_value.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="Groqの応答"))
        ]
        client = LLMClient()

        # Act
        result = client.generate("テストプロンプト")

        # Assert
        assert result == "Groqの応答"

    def test_generate_Geminiでエラー発生時_Groqにフォールバックする(
        self, mock_secrets, mock_genai_module, mock_groq_module
    ):
        # Arrange
        mock_genai_module.GenerativeModel.return_value.generate_content.side_effect = Exception(
            "Gemini API error"
        )
        mock_groq_module.Groq.return_value.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="Groqの応答"))
        ]
        client = LLMClient()

        # Act
        result = client.generate("テストプロンプト")

        # Assert
        assert result == "Groqの応答"

    def test_generate_Geminiでエラー発生時_use_geminiがFalseに変更される(
        self, mock_secrets, mock_genai_module, mock_groq_module
    ):
        # Arrange
        mock_genai_module.GenerativeModel.return_value.generate_content.side_effect = Exception(
            "Gemini API error"
        )
        mock_groq_module.Groq.return_value.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="Groqの応答"))
        ]
        client = LLMClient()

        # Act
        client.generate("テストプロンプト")

        # Assert
        assert client.use_gemini is False

    def test_generate_Groqの応答contentがNoneの場合_失敗メッセージを返す(
        self, mocker, mock_groq_module
    ):
        # Arrange
        mocker.patch("shogi_kif_rag.rag.llm_client.get_gemini_api_key", return_value=None)
        mocker.patch(
            "shogi_kif_rag.rag.llm_client.get_groq_api_key", return_value="dummy-groq-key"
        )
        mock_groq_module.Groq.return_value.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=None))
        ]
        client = LLMClient()

        # Act
        result = client.generate("テストプロンプト")

        # Assert
        assert result == "LLM generation failed"

    def test_generate_GroqでAPIエラーが発生する場合_失敗メッセージを返す(
        self, mocker, mock_groq_module
    ):
        # Arrange
        mocker.patch("shogi_kif_rag.rag.llm_client.get_gemini_api_key", return_value=None)
        mocker.patch(
            "shogi_kif_rag.rag.llm_client.get_groq_api_key", return_value="dummy-groq-key"
        )
        mock_groq_module.Groq.return_value.chat.completions.create.side_effect = Exception(
            "Groq API error"
        )
        client = LLMClient()

        # Act
        result = client.generate("テストプロンプト")

        # Assert
        assert result == "LLM generation failed"

    def test_generate_両方のAPIキーがない場合_失敗メッセージを返す(self, mocker):
        # Arrange
        mocker.patch("shogi_kif_rag.rag.llm_client.get_gemini_api_key", return_value=None)
        mocker.patch("shogi_kif_rag.rag.llm_client.get_groq_api_key", return_value=None)
        client = LLMClient()

        # Act
        result = client.generate("テストプロンプト")

        # Assert
        assert result == "LLM generation failed"
