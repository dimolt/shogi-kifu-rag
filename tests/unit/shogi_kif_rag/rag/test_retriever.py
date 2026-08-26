from unittest.mock import MagicMock

import pytest

from shogi_kif_rag.rag.retriever import retrieve_relevant_documents
from shogi_kif_rag.vector import VectorStore


@pytest.fixture
def mock_vector_store(mocker) -> MagicMock:
    """VectorStore のモックを提供する。"""
    return mocker.MagicMock(spec=VectorStore)


def test_retrieve_relevant_documents_正常に取得できると_text_metadata_scoreを持つ辞書のリストを返す(
    mock_vector_store: MagicMock,
) -> None:
    # Arrange
    mock_vector_store.search.return_value = [
        {
            'document': {
                'id': 'doc1',
                'text': 'doc1',
                'metadata': {'kif_id': 'A'},
            },
            'score': 0.1,
        },
        {
            'document': {
                'id': 'doc2',
                'text': 'doc2',
                'metadata': {'kif_id': 'B'},
            },
            'score': 0.2,
        },
    ]

    # Act
    result = retrieve_relevant_documents(mock_vector_store, 'テストクエリ')

    # Assert
    assert result == [
        {'text': 'doc1', 'metadata': {'kif_id': 'A'}, 'score': 0.1},
        {'text': 'doc2', 'metadata': {'kif_id': 'B'}, 'score': 0.2},
    ]


def test_retrieve_relevant_documents_n_resultsを指定すると_searchに正しく渡す(
    mock_vector_store: MagicMock,
) -> None:
    # Arrange
    mock_vector_store.search.return_value = []

    # Act
    retrieve_relevant_documents(mock_vector_store, 'テストクエリ', n_results=10)

    # Assert
    mock_vector_store.search.assert_called_once_with('テストクエリ', top_k=10)


def test_retrieve_relevant_documents_検索結果が0件のとき_空リストを返す(
    mock_vector_store: MagicMock,
) -> None:
    # Arrange
    mock_vector_store.search.return_value = []

    # Act
    result = retrieve_relevant_documents(mock_vector_store, 'テストクエリ')

    # Assert
    assert result == []


def test_retrieve_relevant_documents_searchが例外を送出すると_空リストを返す(
    mock_vector_store: MagicMock,
) -> None:
    # Arrange
    mock_vector_store.search.side_effect = RuntimeError('検索に失敗しました')

    # Act
    result = retrieve_relevant_documents(mock_vector_store, 'テストクエリ')

    # Assert
    assert result == []


def test_retrieve_relevant_documents_デフォルト引数でtop_kが5になる(
    mock_vector_store: MagicMock,
) -> None:
    # Arrange
    mock_vector_store.search.return_value = []

    # Act
    retrieve_relevant_documents(mock_vector_store, 'テストクエリ')

    # Assert
    mock_vector_store.search.assert_called_once_with('テストクエリ', top_k=5)
