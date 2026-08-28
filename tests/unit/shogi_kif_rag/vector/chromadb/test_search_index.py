from __future__ import annotations

import sys
import types
from typing import Any

from shogi_kif_rag.vector.chromadb.serach_index import ChromaSearchIndex


def _install_dependency_stubs() -> None:
    """import時に必要な外部依存をスタブ化する。

    `shogi_kif_rag.vector.chromadb` パッケージの `__init__.py` が
    `adapter.py`（pyspark依存）を経由してimportされるため、
    本テストの対象外であるpyspark等もスタブ化しておく必要がある。
    """
    if 'chromadb' not in sys.modules:
        chromadb_module = types.ModuleType('chromadb')

        class _FakeClientAPI:
            pass

        chromadb_module.ClientAPI = _FakeClientAPI
        chromadb_module.Collection = object
        chromadb_module.PersistentClient = lambda path: object()
        sys.modules['chromadb'] = chromadb_module

    if 'pyspark' not in sys.modules:
        pyspark_module = types.ModuleType('pyspark')
        pyspark_sql_module = types.ModuleType('pyspark.sql')

        class _FakeSparkSession:
            @staticmethod
            def getActiveSession() -> None:
                return None

        pyspark_module.sql = pyspark_sql_module
        pyspark_sql_module.SparkSession = _FakeSparkSession
        sys.modules['pyspark'] = pyspark_module
        sys.modules['pyspark.sql'] = pyspark_sql_module

    if 'shogi_kif_rag.vector.embedding' not in sys.modules:
        embedding_module = types.ModuleType('shogi_kif_rag.vector.embedding')

        class _FakeSentenceTransformerEmbedding:
            def __init__(self, *args: object, **kwargs: object) -> None:
                pass

        embedding_module.SentenceTransformerEmbedding = _FakeSentenceTransformerEmbedding
        embedding_module.EmbeddingModel = object
        embedding_module.DatabricksEmbedding = object
        sys.modules['shogi_kif_rag.vector.embedding'] = embedding_module


_install_dependency_stubs()


class _FakeEmbeddingModel:
    """テスト用のEmbeddingModelスタブ。"""

    def encode(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


class _FakeCollection:
    """テスト用のChromaDB Collectionスタブ。"""

    def __init__(self, query_result: dict[str, Any] | None = None) -> None:
        self._query_result = query_result

    def query(self, query_embeddings: list[list[float]], n_results: int) -> dict[str, Any]:
        if self._query_result is None:
            raise RuntimeError('query failed')
        return self._query_result


class _FakeChromaClient:
    """テスト用のChromaDBクライアントスタブ。"""

    def __init__(
        self,
        existing_collections: dict[str, _FakeCollection] | None = None,
    ) -> None:
        self._collections = existing_collections or {}
        self.created_collections: list[str] = []

    def get_collection(self, name: str) -> _FakeCollection:
        if name not in self._collections:
            raise ValueError(f'collection not found: {name}')
        return self._collections[name]

    def create_collection(self, name: str, metadata: dict[str, str]) -> _FakeCollection:
        collection = _FakeCollection()
        self._collections[name] = collection
        self.created_collections.append(name)
        return collection


def _make_query_result() -> dict[str, Any]:
    return {
        'ids': [['pos_1', 'pos_2']],
        'documents': [['position 1 text', 'position 2 text']],
        'metadatas': [[{'game_id': 'g1'}, {'game_id': 'g2'}]],
        'distances': [[0.1, 0.3]],
    }


def test_search_正常系で検索結果をスコア順で返す() -> None:
    index = ChromaSearchIndex(collection_name='positions',
        persist_path='/tmp/chromadb',
        embedding_model=_FakeEmbeddingModel())
    collection = _FakeCollection(query_result=_make_query_result())
    index._client = _FakeChromaClient(existing_collections={'positions': collection})
    results = index.search('position query', top_k=2)

    assert [r['document']['id'] for r in results] == ['pos_1', 'pos_2']
    assert [r['score'] for r in results] == [0.1, 0.3]


def test_search_chromadbが例外を送出した場合は空リストを返す() -> None:
    index = ChromaSearchIndex(collection_name='positions',
        persist_path='/tmp/chromadb',
        embedding_model=_FakeEmbeddingModel())
    collection = _FakeCollection(query_result=None)  # query()がRuntimeErrorを送出
    index._client = _FakeChromaClient(existing_collections={'positions': collection})

    results = index.search('position query')

    assert results == []
