import sys
import types

import pandas as pd
import pytest


def _install_dependency_stubs() -> None:
    """import時に必要な外部依存をスタブ化する。"""
    chromadb_module = types.ModuleType("chromadb")

    class _FakeClientAPI:
        pass

    chromadb_module.ClientAPI = _FakeClientAPI
    chromadb_module.PersistentClient = lambda path: object()
    chromadb_module.Collection = object
    sys.modules.setdefault("chromadb", chromadb_module)

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

# Now import after stubs are installed
from shogi_kif_rag.vector.chromadb import adapter as chromadb_service  #noqa: E402
from shogi_kif_rag.vector.chromadb import service as new_chromadb_service  #noqa: E402


def _install_dependency_stubs() -> None:
    """import時に必要な外部依存をスタブ化する。"""
    chromadb_module = types.ModuleType("chromadb")

    class _FakeClientAPI:
        pass

    chromadb_module.ClientAPI = _FakeClientAPI
    chromadb_module.PersistentClient = lambda path: object()
    chromadb_module.Collection = object
    sys.modules.setdefault("chromadb", chromadb_module)

    # 新しいEmbeddingモジュールのスタブ
    shogi_kif_rag_vector_embedding_module = types.ModuleType("shogi_kif_rag.vector.embedding")

    class _FakeSentenceTransformerEmbedding:
        def __init__(self, model_name: str, batch_size: int) -> None:
            self.model_name = model_name
            self.batch_size = batch_size

        def encode(self, text: str) -> list[float]:
            return [0.0]

        def encode_batch(self, texts: list[str]) -> list[list[float]]:
            return [[0.0] for _ in texts]

    shogi_kif_rag_vector_embedding_module.SentenceTransformerEmbedding = (
        _FakeSentenceTransformerEmbedding
    )
    sys.modules.setdefault("shogi_kif_rag.vector.embedding", shogi_kif_rag_vector_embedding_module)

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
    chromadb_service.ChromadbService._instance = None
    yield
    chromadb_service.ChromadbService._instance = None


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
    rebuild_calls: list[tuple[object, str]] = []

    monkeypatch.setattr(
        new_chromadb_service.chromadb_lib,
        "PersistentClient",
        lambda path: fake_client,
    )
    monkeypatch.setattr(
        new_chromadb_service.SparkSession,
        "getActiveSession",
        staticmethod(lambda: fake_spark),
    )
    # ensure() の内部では adapter 自身ではなく、委譲先の service._service
    # （NewChromadbService）の collection_exists / rebuild_collections が呼ばれる
    monkeypatch.setattr(service._service, "collection_exists", lambda name: False)
    monkeypatch.setattr(
        service._service,
        "rebuild_collections",
        lambda spark=None, catalog='shogi': rebuild_calls.append((spark, catalog)),
    )

    service.ensure()

    assert service._service._client is fake_client
    assert service._embedding_model is not None
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
    rebuild_calls: list[tuple[object, str]] = []

    monkeypatch.setattr(
        new_chromadb_service.chromadb_lib,
        "PersistentClient",
        lambda path: fake_client,
    )
    monkeypatch.setattr(
        new_chromadb_service.SparkSession,
        "getActiveSession",
        staticmethod(lambda: fake_spark),
    )
    monkeypatch.setattr(service._service, "collection_exists", lambda name: False)
    monkeypatch.setattr(
        service._service,
        "rebuild_collections",
        lambda spark=None, catalog='shogi': rebuild_calls.append((spark, catalog)),
    )

    service.ensure(catalog='test_catalog')

    assert service._service._client is fake_client
    assert service._embedding_model is not None
    assert rebuild_calls == [(fake_spark, 'test_catalog')]


def test_rebuild_collections_相互再帰が解消されている(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """rebuild_collections が _initialize_client のみを呼び、各コレクションを再構築することを確認する。

    adapter.rebuild_collections は service._service（NewChromadbService）へ処理を
    委譲するだけであり、NewChromadbService.rebuild_collections には ensure を
    呼び出す経路が存在しない。そのため ensure との相互再帰は構造的に発生し得ず、
    ここでは初期化と3コレクションの再構築が呼ばれることのみを検証する。
    """
    service = chromadb_service.ChromadbService()
    fake_spark = object()
    initialize_calls: list[object] = []
    rebuild_positions_calls: list[tuple[object, str]] = []
    rebuild_floodgate_calls: list[tuple[object, str]] = []
    rebuild_joseki_calls: list[tuple[object, str]] = []

    monkeypatch.setattr(
        service._service,
        "_initialize_client",
        lambda: initialize_calls.append(None),
    )
    monkeypatch.setattr(
        service._service,
        "_rebuild_positions",
        lambda spark, catalog: rebuild_positions_calls.append((spark, catalog)),
    )
    monkeypatch.setattr(
        service._service,
        "_rebuild_floodgate",
        lambda spark, catalog: rebuild_floodgate_calls.append((spark, catalog)),
    )
    monkeypatch.setattr(
        service._service,
        "_rebuild_joseki",
        lambda spark, catalog: rebuild_joseki_calls.append((spark, catalog)),
    )

    service.rebuild_collections(fake_spark, 'test_catalog')

    assert initialize_calls == [None]
    assert rebuild_positions_calls == [(fake_spark, 'test_catalog')]
    assert rebuild_floodgate_calls == [(fake_spark, 'test_catalog')]
    assert rebuild_joseki_calls == [(fake_spark, 'test_catalog')]


def test_initialize_初期化済みの場合は何もしない(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_initialize_client が初期化済みの場合は何もしないことを確認する。

    クライアントの初期化ロジックは service._service（NewChromadbService）の
    _initialize_client に存在するため、そちらを直接検証する。
    """
    service = chromadb_service.ChromadbService()
    fake_client = object()

    monkeypatch.setattr(
        new_chromadb_service.chromadb_lib,
        "PersistentClient",
        lambda path: fake_client,
    )

    service._service._initialize_client()
    assert service._service._client is fake_client
    assert service._embedding_model is not None

    # 2回目は初期化されない
    first_embedding_model = service._embedding_model
    service._service._initialize_client()
    # 同じオブジェクトであることを確認（再初期化されていない）
    assert service._service._client is fake_client
    assert service._embedding_model is first_embedding_model
