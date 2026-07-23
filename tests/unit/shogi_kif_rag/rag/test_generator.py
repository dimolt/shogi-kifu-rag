
from shogi_kif_rag.rag.generator import generate_response
from shogi_kif_rag.rag.llm_client import LLMClient


def test_generate_response_有効なクエリとコンテキストを渡すと_LLMクライアントの生成結果を返す(
    mock_llm_client: LLMClient,
    sample_context: list[dict],
) -> None:
    # Arrange
    query = "居飛車の定跡を教えてください"

    # Act
    result = generate_response(query, sample_context, mock_llm_client)

    # Assert
    assert result == "生成された回答です。"


def test_generate_response_呼び出し時にLLMクライアントのgenerateを1回だけ呼び出す(
    mock_llm_client: LLMClient,
    sample_context: list[dict],
) -> None:
    # Arrange
    query = "居飛車の定跡を教えてください"

    # Act
    generate_response(query, sample_context, mock_llm_client)

    # Assert
    mock_llm_client.generate.assert_called_once()


def test_generate_response_プロンプトに質問文が含まれる(
    mock_llm_client: LLMClient,
    sample_context: list[dict],
) -> None:
    # Arrange
    query = "居飛車の定跡を教えてください"

    # Act
    generate_response(query, sample_context, mock_llm_client)

    # Assert
    sent_prompt = mock_llm_client.generate.call_args[0][0]
    assert query in sent_prompt


def test_generate_response_プロンプトに全ドキュメントのテキストとメタデータが含まれる(
    mock_llm_client: LLMClient,
    sample_context: list[dict],
) -> None:
    # Arrange
    query = "居飛車の定跡を教えてください"

    # Act
    generate_response(query, sample_context, mock_llm_client)

    # Assert
    sent_prompt = mock_llm_client.generate.call_args[0][0]
    is_all_documents_included = all(
        doc["text"] in sent_prompt and str(doc["metadata"]) in sent_prompt
        for doc in sample_context
    )
    assert is_all_documents_included


def test_generate_response_コンテキストが空リストの場合_ドキュメントなしのプロンプトを生成する(
    mock_llm_client: LLMClient,
) -> None:
    # Arrange
    query = "居飛車の定跡を教えてください"
    empty_context: list[dict] = []

    # Act
    generate_response(query, empty_context, mock_llm_client)

    # Assert
    sent_prompt = mock_llm_client.generate.call_args[0][0]
    assert "ドキュメント 1:" not in sent_prompt


def test_generate_response_コンテキストが1件の場合_ドキュメント番号1のみを含むプロンプトを生成する(
    mock_llm_client: LLMClient,
) -> None:
    # Arrange
    query = "居飛車の定跡を教えてください"
    single_context = [{"text": "▲7六歩 △3四歩", "metadata": {"source": "kif_001"}}]

    # Act
    generate_response(query, single_context, mock_llm_client)

    # Assert
    sent_prompt = mock_llm_client.generate.call_args[0][0]
    assert "ドキュメント 1:" in sent_prompt and "ドキュメント 2:" not in sent_prompt
