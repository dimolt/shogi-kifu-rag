from unittest.mock import MagicMock

import pytest

from shogi_kif_rag.rag.retriever import retrieve_relevant_documents


@pytest.fixture
def mock_chromadb(mocker) -> MagicMock:
    """ChromadbService のモックを提供する。"""
    return mocker.MagicMock()


def test_retrieve_relevant_documents_正常に取得できると_text_metadata_distanceを持つ辞書のリストを返す(
    mock_chromadb: MagicMock,
) -> None:
    # Arrange
    mock_chromadb.encode_query.return_value = [0.1, 0.2, 0.3]
    mock_collection = mock_chromadb.get_collection.return_value
    mock_collection.query.return_value = {
        'documents': [['doc1', 'doc2']],
        'metadatas': [[{'kif_id': 'A'}, {'kif_id': 'B'}]],
        'distances': [[0.1, 0.2]],
    }

    # Act
    result = retrieve_relevant_documents(mock_chromadb, 'テストクエリ')

    # Assert
    assert result == [
        {'text': 'doc1', 'metadata': {'kif_id': 'A'}, 'distance': 0.1},
        {'text': 'doc2', 'metadata': {'kif_id': 'B'}, 'distance': 0.2},
    ]


def test_retrieve_relevant_documents_呼び出し前に_ensureとencode_queryが呼ばれる(
    mock_chromadb: MagicMock,
) -> None:
    # Arrange
    mock_chromadb.encode_query.return_value = [0.1, 0.2, 0.3]
    mock_collection = mock_chromadb.get_collection.return_value
    mock_collection.query.return_value = {
        'documents': [[]],
        'metadatas': [[]],
        'distances': [[]],
    }

    # Act
    retrieve_relevant_documents(mock_chromadb, 'テストクエリ')

    # Assert
    mock_chromadb.ensure.assert_called_once()
    mock_chromadb.encode_query.assert_called_once_with('テストクエリ')


def test_retrieve_relevant_documents_collection_nameとn_resultsを指定すると_get_collectionとqueryに正しく渡す(
    mock_chromadb: MagicMock,
) -> None:
    # Arrange
    mock_chromadb.encode_query.return_value = [0.1, 0.2, 0.3]
    mock_collection = mock_chromadb.get_collection.return_value
    mock_collection.query.return_value = {
        'documents': [[]],
        'metadatas': [[]],
        'distances': [[]],
    }

    # Act
    retrieve_relevant_documents(
        mock_chromadb,
        'テストクエリ',
        collection_name='joseki_knowledge',
        n_results=10,
    )

    # Assert
    mock_chromadb.get_collection.assert_called_once_with('joseki_knowledge')
    mock_collection.query.assert_called_once_with(
        query_embeddings=[[0.1, 0.2, 0.3]],
        n_results=10,
    )


def test_retrieve_relevant_documents_検索結果が0件のとき_空リストを返す(
    mock_chromadb: MagicMock,
) -> None:
    # Arrange
    mock_chromadb.encode_query.return_value = [0.1, 0.2, 0.3]
    mock_collection = mock_chromadb.get_collection.return_value
    mock_collection.query.return_value = {
        'documents': [[]],
        'metadatas': [[]],
        'distances': [[]],
    }

    # Act
    result = retrieve_relevant_documents(mock_chromadb, 'テストクエリ')

    # Assert
    assert result == []


def test_retrieve_relevant_documents_get_collectionが例外を送出すると_空リストを返す(
    mock_chromadb: MagicMock,
) -> None:
    # Arrange
    mock_chromadb.encode_query.return_value = [0.1, 0.2, 0.3]
    mock_chromadb.get_collection.side_effect = RuntimeError('コレクションが存在しません')

    # Act
    result = retrieve_relevant_documents(mock_chromadb, 'テストクエリ')

    # Assert
    assert result == []


def test_retrieve_relevant_documents_collection_queryが例外を送出すると_空リストを返す(
    mock_chromadb: MagicMock,
) -> None:
    # Arrange
    mock_chromadb.encode_query.return_value = [0.1, 0.2, 0.3]
    mock_collection = mock_chromadb.get_collection.return_value
    mock_collection.query.side_effect = ValueError('クエリに失敗しました')

    # Act
    result = retrieve_relevant_documents(mock_chromadb, 'テストクエリ')

    # Assert
    assert result == []
