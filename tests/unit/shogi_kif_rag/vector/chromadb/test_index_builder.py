from __future__ import annotations

import sys
import types
from typing import Any

import pandas as pd


def _install_dependency_stubs() -> None:
    """import時に必要な外部依存をスタブ化する。"""
    if 'chromadb' not in sys.modules:
        chromadb_module = types.ModuleType('chromadb')

        class _FakeClientAPI:
            pass

        chromadb_module.ClientAPI = _FakeClientAPI
        chromadb_module.Collection = object
        chromadb_module.PersistentClient = lambda path: object()
        sys.modules['chromadb'] = chromadb_module


_install_dependency_stubs()

from shogi_kif_rag.vector.chromadb.index_builder import ChromaIndexBuilder  # noqa: E402


class _FakeEmbeddingModel:
    """テスト用のEmbeddingModelスタブ。"""

    def encode(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


class _FakeCollection:
    """テスト用のChromaDB Collectionスタブ。"""

    def __init__(self) -> None:
        self.added: list[dict[str, Any]] = []

    def add(self, **kwargs: Any) -> None:
        self.added.append(kwargs)


class _FakeChromaClient:
    """テスト用のChromaDBクライアントスタブ。"""

    def __init__(
        self,
        existing_collections: dict[str, _FakeCollection] | None = None,
    ) -> None:
        self._collections = existing_collections or {}
        self.created_collections: list[str] = []
        self.deleted_collections: list[str] = []

    def get_collection(self, name: str) -> _FakeCollection:
        if name not in self._collections:
            raise ValueError(f'collection not found: {name}')
        return self._collections[name]

    def create_collection(self, name: str, metadata: dict[str, str]) -> _FakeCollection:
        collection = _FakeCollection()
        self._collections[name] = collection
        self.created_collections.append(name)
        return collection

    def delete_collection(self, name: str) -> None:
        self.deleted_collections.append(name)
        self._collections.pop(name, None)


def test_init_embedding_modelとpersist_pathを保持する() -> None:
    embedding_model = _FakeEmbeddingModel()

    builder = ChromaIndexBuilder(embedding_model=embedding_model, persist_path='/tmp/x')

    assert builder._embedding_model is embedding_model
    assert builder._persist_path == '/tmp/x'


def test_ensure_collection_存在しない場合は新規作成する() -> None:
    builder = ChromaIndexBuilder(embedding_model=_FakeEmbeddingModel(), persist_path='/tmp/x')
    builder._client = _FakeChromaClient(existing_collections={})

    builder.ensure_collection('positions')

    assert builder._client.created_collections == ['positions']


def test_ensure_collection_既存の場合は作成しない() -> None:
    builder = ChromaIndexBuilder(embedding_model=_FakeEmbeddingModel(), persist_path='/tmp/x')
    builder._client = _FakeChromaClient(existing_collections={'positions': _FakeCollection()})

    builder.ensure_collection('positions')

    assert builder._client.created_collections == []


def test_collection_exists_クライアント未初期化の場合はFalseを返す() -> None:
    builder = ChromaIndexBuilder(embedding_model=_FakeEmbeddingModel(), persist_path='/tmp/x')

    assert builder.collection_exists('positions') is False


def test_collection_exists_存在する場合はTrueを返す() -> None:
    client = _FakeChromaClient(existing_collections={'positions': _FakeCollection()})
    builder = ChromaIndexBuilder(embedding_model=_FakeEmbeddingModel(), persist_path='/tmp/x')
    builder._client = client

    assert builder.collection_exists('positions') is True


def test_clean_position_features_空白_nan_空文字を除外して有効な行のみ返す() -> None:
    df = pd.DataFrame({'search_text': ['valid', '  ', 'nan', 'None', None, 'また有効']})

    result = ChromaIndexBuilder.clean_position_features(df)

    assert list(result['search_text']) == ['valid', 'また有効']
