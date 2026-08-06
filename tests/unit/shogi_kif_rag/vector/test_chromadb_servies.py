import sys
import types

import pandas as pd
import pytest

from shogi_kif_rag.vector import chromadb_service


def _install_dependency_stubs() -> None:
    """import時に必要な外部依存をスタブ化する。"""
    chromadb_module = types.ModuleType("chromadb")

    class _FakeClientAPI:
        pass

    chromadb_module.ClientAPI = _FakeClientAPI
    chromadb_module.PersistentClient = lambda path: object()
    chromadb_module.Collection = object
    sys.modules.setdefault("chromadb", chromadb_module)

    sentence_transformers_module = types.ModuleType("sentence_transformers")

    class _FakeSentenceTransformer:
        def __init__(self, model_name: str) -> None:
            self.model_name = model_name

        def encode(self, texts, batch_size=None, show_progress_bar=False):
            if isinstance(texts, list):
                return [[0.0] for _ in texts]
            return [0.0]

    sentence_transformers_module.SentenceTransformer = _FakeSentenceTransformer
    sys.modules.setdefault("sentence_transformers", sentence_transformers_module)

    pyspark_module = types.ModuleType("pyspark")
    pyspark_sql_module = types.ModuleType("pyspark.sql")

    class _FakeSparkSession:
        @staticmethod
        def getActiveSession():
            return None

    pyspark_module.sql = pyspark_sql_module
    pyspark_sql_module.SparkSession = _FakeSparkSession
    sys.modules.setdefault("pyspark", pyspark_module)
    sys.modules.setdefault("pyspark.sql", pyspark_sql_module)


_install_dependency_stubs()


@pytest.fixture(autouse=True)
def reset_singleton() -> None:
    """シングルトン状態を各テスト前に初期化する。"""
    chromadb_service._instance = None
    yield
    chromadb_service._instance = None


def test_get_instance_初回呼び出しで同一インスタンスを返す() -> None:
    """get_instance が同じインスタンスを返すことを確認する。"""
    service_a = chromadb_service.ChromadbService.get_instance()

    service_b = chromadb_service.ChromadbService.get_instance()

    assert service_a is service_b


def test_ensure_未初期化時にモデルとクライアントを初期化し再構築を実行する(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ensure が初期化と再構築を行うことを確認する。"""
    service = chromadb_service.ChromadbService()
    fake_client = object()
    fake_spark = object()
    fake_model = object()
    rebuild_calls: list[tuple[object, str]] = []

    monkeypatch.setattr(
        chromadb_service.chromadb_lib,
        "PersistentClient",
        lambda path: fake_client,
    )
    monkeypatch.setattr(chromadb_service, "SentenceTransformer", lambda model_name: fake_model)
    monkeypatch.setattr(
        chromadb_service.SparkSession,
        "getActiveSession",
        staticmethod(lambda: fake_spark),
    )
    monkeypatch.setattr(service, "_collection_exists", lambda name: False)
    monkeypatch.setattr(service, "rebuild_collections", lambda spark=None, catalog='shogi': rebuild_calls.append((spark, catalog)))

    service.ensure()

    assert service._client is fake_client
    assert service._model is fake_model
    assert rebuild_calls == [(fake_spark, 'shogi')]


def test_clean_position_features_空白_nan_空文字を除外して有効な行のみ返す() -> None:
    """_clean_position_features が無効な検索文字列を取り除くことを確認する。"""
    service = chromadb_service.ChromadbService()
    df = pd.DataFrame({"search_text": ["  foo  ", "", "nan", "   ", None, "bar"]})

    result = service._clean_position_features(df)

    assert result["search_text"].tolist() == ["foo", "bar"]


def test_ensure_catalog引数を渡して再構築を実行する(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ensure にcatalog引数を渡した場合、正しいcatalogがrebuild_collectionsに渡されることを確認する。"""
    service = chromadb_service.ChromadbService()
    fake_client = object()
    fake_spark = object()
    fake_model = object()
    rebuild_calls: list[tuple[object, str]] = []

    monkeypatch.setattr(
        chromadb_service.chromadb_lib,
        "PersistentClient",
        lambda path: fake_client,
    )
    monkeypatch.setattr(chromadb_service, "SentenceTransformer", lambda model_name: fake_model)
    monkeypatch.setattr(
        chromadb_service.SparkSession,
        "getActiveSession",
        staticmethod(lambda: fake_spark),
    )
    monkeypatch.setattr(service, "_collection_exists", lambda name: False)
    monkeypatch.setattr(service, "rebuild_collections", lambda spark=None, catalog='shogi': rebuild_calls.append((spark, catalog)))

    service.ensure(catalog='test_catalog')

    assert service._client is fake_client
    assert service._model is fake_model
    assert rebuild_calls == [(fake_spark, 'test_catalog')]


def test_rebuild_collections_相互再帰が解消されている(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """rebuild_collections が ensure を呼ばず、_initialize のみを呼ぶことを確認する。"""
    service = chromadb_service.ChromadbService()
    fake_client = object()
    fake_spark = object()
    fake_model = object()
    initialize_calls: list[object] = []
    ensure_calls: list[object] = []

    monkeypatch.setattr(
        chromadb_service.chromadb_lib,
        "PersistentClient",
        lambda path: fake_client,
    )
    monkeypatch.setattr(chromadb_service, "SentenceTransformer", lambda model_name: fake_model)
    monkeypatch.setattr(
        chromadb_service.SparkSession,
        "getActiveSession",
        staticmethod(lambda: fake_spark),
    )
    monkeypatch.setattr(service, "_initialize", lambda: initialize_calls.append(None))
    monkeypatch.setattr(service, "ensure", lambda catalog='shogi': ensure_calls.append(catalog))
    monkeypatch.setattr(service, "_rebuild_positions", lambda spark, catalog: None)
    monkeypatch.setattr(service, "_rebuild_floodgate", lambda spark, catalog: None)
    monkeypatch.setattr(service, "_rebuild_joseki", lambda spark, catalog: None)

    service.rebuild_collections(fake_spark, 'test_catalog')

    assert initialize_calls == [None]
    assert ensure_calls == []


def test_initialize_初期化済みの場合は何もしない(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_initialize が初期化済みの場合は何もしないことを確認する。"""
    service = chromadb_service.ChromadbService()
    fake_client = object()
    fake_model = object()

    monkeypatch.setattr(
        chromadb_service.chromadb_lib,
        "PersistentClient",
        lambda path: fake_client,
    )
    monkeypatch.setattr(chromadb_service, "SentenceTransformer", lambda model_name: fake_model)

    service._initialize()
    assert service._client is fake_client
    assert service._model is fake_model

    # 2回目は初期化されない
    service._initialize()
    # 同じオブジェクトであることを確認（再初期化されていない）
    assert service._client is fake_client
    assert service._model is fake_model
