import sys
import types
from pathlib import Path

import pandas as pd
import pytest

from shogi_kif_rag.vector import chromadb_service

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


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
    rebuild_calls: list[object] = []

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
    monkeypatch.setattr(service, "rebuild_collections", lambda spark=None: rebuild_calls.append(spark))

    service.ensure()

    assert service._client is fake_client
    assert service._model is fake_model
    assert rebuild_calls == [fake_spark]


def test_clean_position_features_空白_nan_空文字を除外して有効な行のみ返す() -> None:
    """_clean_position_features が無効な検索文字列を取り除くことを確認する。"""
    service = chromadb_service.ChromadbService()
    df = pd.DataFrame({"search_text": ["  foo  ", "", "nan", "   ", None, "bar"]})

    result = service._clean_position_features(df)

    assert result["search_text"].tolist() == ["foo", "bar"]
