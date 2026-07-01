"""rag.py の rag_query 関数に対するユニットテスト。"""

from shogi_kif_rag.rag import rag_query


def test_rag_query_ドキュメントが見つかった場合_回答と参照ドキュメントを返す(mocker):
    # Arrange
    mock_documents = [{"content": "戦法の解説"}, {"content": "定跡の解説"}]
    mock_retrieve = mocker.patch("shogi_kif_rag.rag.rag.retrieve_relevant_documents")
    mock_retrieve.return_value = mock_documents
    mock_generate = mocker.patch("shogi_kif_rag.rag.rag.generate_response")
    mock_generate.return_value = "これは回答です。"
    mock_chromadb = mocker.Mock()
    mock_llm_client = mocker.Mock()

    # Act
    result = rag_query(
        chromadb=mock_chromadb,
        query="四間飛車とは何ですか？",
        llm_client=mock_llm_client,
    )

    # Assert
    assert result == {"answer": "これは回答です。", "documents": mock_documents}


def test_rag_query_ドキュメントが見つからない場合_デフォルトメッセージを返す(mocker):
    # Arrange
    mocker.patch("shogi_kif_rag.rag.rag.retrieve_relevant_documents", return_value=[])
    mock_chromadb = mocker.Mock()
    mock_llm_client = mocker.Mock()

    # Act
    result = rag_query(
        chromadb=mock_chromadb,
        query="存在しないクエリ",
        llm_client=mock_llm_client,
    )

    # Assert
    assert result == {"answer": "関連する情報が見つかりませんでした。", "documents": []}


def test_rag_query_ドキュメントが見つからない場合_generate_responseを呼び出さない(mocker):
    # Arrange
    mocker.patch("shogi_kif_rag.rag.rag.retrieve_relevant_documents", return_value=[])
    mock_generate = mocker.patch("shogi_kif_rag.rag.rag.generate_response")
    mock_chromadb = mocker.Mock()
    mock_llm_client = mocker.Mock()

    # Act
    rag_query(
        chromadb=mock_chromadb,
        query="存在しないクエリ",
        llm_client=mock_llm_client,
    )

    # Assert
    mock_generate.assert_not_called()


def test_rag_query_llm_clientが指定されない場合_LLMClientを新規生成する(mocker):
    # Arrange
    mocker.patch(
        "shogi_kif_rag.rag.rag.retrieve_relevant_documents",
        return_value=[{"content": "内容"}],
    )
    mocker.patch("shogi_kif_rag.rag.rag.generate_response", return_value="回答")
    mock_llm_client_class = mocker.patch("shogi_kif_rag.rag.rag.LLMClient")
    mock_chromadb = mocker.Mock()

    # Act
    rag_query(chromadb=mock_chromadb, query="クエリ")

    # Assert
    mock_llm_client_class.assert_called_once_with()


def test_rag_query_llm_clientが指定された場合_LLMClientを新規生成しない(mocker):
    # Arrange
    mocker.patch(
        "shogi_kif_rag.rag.rag.retrieve_relevant_documents",
        return_value=[{"content": "内容"}],
    )
    mocker.patch("shogi_kif_rag.rag.rag.generate_response", return_value="回答")
    mock_llm_client_class = mocker.patch("shogi_kif_rag.rag.rag.LLMClient")
    mock_chromadb = mocker.Mock()
    mock_llm_client = mocker.Mock()

    # Act
    rag_query(chromadb=mock_chromadb, query="クエリ", llm_client=mock_llm_client)

    # Assert
    mock_llm_client_class.assert_not_called()


def test_rag_query_引数を指定した場合_retrieve_relevant_documentsに正しく渡す(mocker):
    # Arrange
    mock_retrieve = mocker.patch(
        "shogi_kif_rag.rag.rag.retrieve_relevant_documents",
        return_value=[{"content": "内容"}],
    )
    mocker.patch("shogi_kif_rag.rag.rag.generate_response", return_value="回答")
    mock_chromadb = mocker.Mock()
    mock_llm_client = mocker.Mock()

    # Act
    rag_query(
        chromadb=mock_chromadb,
        query="矢倉の指し方",
        collection_name="floodgate_positions",
        n_results=10,
        llm_client=mock_llm_client,
    )

    # Assert
    mock_retrieve.assert_called_once_with(
        mock_chromadb, "矢倉の指し方", "floodgate_positions", 10
    )


def test_rag_query_ドキュメントが見つかった場合_generate_responseに正しく渡す(mocker):
    # Arrange
    mock_documents = [{"content": "戦法の解説"}]
    mocker.patch(
        "shogi_kif_rag.rag.rag.retrieve_relevant_documents",
        return_value=mock_documents,
    )
    mock_generate = mocker.patch("shogi_kif_rag.rag.rag.generate_response", return_value="回答")
    mock_chromadb = mocker.Mock()
    mock_llm_client = mocker.Mock()

    # Act
    rag_query(chromadb=mock_chromadb, query="四間飛車とは", llm_client=mock_llm_client)

    # Assert
    mock_generate.assert_called_once_with("四間飛車とは", mock_documents, mock_llm_client)
