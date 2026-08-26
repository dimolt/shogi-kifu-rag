import sys
import types


def _install_dependency_stubs() -> None:
    """import時に必要な外部依存をスタブ化する。"""
    sentence_transformers_module = types.ModuleType("sentence_transformers")

    class _FakeArray:
        """numpy配列のスタブ。tolist()メソッドを提供する。"""

        def __init__(self, data: list[list[float]] | list[float]) -> None:
            self._data = data

        def tolist(self) -> list[list[float]] | list[float]:
            return self._data

    class _FakeSentenceTransformer:
        def __init__(self, model_name: str) -> None:
            self.model_name = model_name

        def encode(self, texts, batch_size=None, show_progress_bar=False):
            if isinstance(texts, list):
                return _FakeArray([[0.0] for _ in texts])
            return _FakeArray([0.0])

    sentence_transformers_module.SentenceTransformer = _FakeSentenceTransformer
    sys.modules.setdefault("sentence_transformers", sentence_transformers_module)


_install_dependency_stubs()


def test_sentence_transformer_embedding_encode_single_text() -> None:
    """単一テキストのエンコードが正常に動作することを確認する。"""
    from shogi_kif_rag.vector.embedding import SentenceTransformerEmbedding

    embedding_model = SentenceTransformerEmbedding()
    result = embedding_model.encode("テストテキスト")

    assert isinstance(result, list)
    assert all(isinstance(x, float) for x in result)


def test_sentence_transformer_embedding_encode_batch() -> None:
    """バッチエンコードが正常に動作することを確認する。"""
    from shogi_kif_rag.vector.embedding import SentenceTransformerEmbedding

    embedding_model = SentenceTransformerEmbedding()
    texts = ["テスト1", "テスト2", "テスト3"]
    result = embedding_model.encode_batch(texts)

    assert isinstance(result, list)
    assert len(result) == len(texts)
    assert all(isinstance(embedding, list) for embedding in result)
    assert all(isinstance(x, float) for embedding in result for x in embedding)


def test_sentence_transformer_embedding_custom_batch_size() -> None:
    """カスタムバッチサイズを指定して初期化できることを確認する。"""
    from shogi_kif_rag.vector.embedding import SentenceTransformerEmbedding

    embedding_model = SentenceTransformerEmbedding(batch_size=64)
    texts = ["テスト1", "テスト2"]
    result = embedding_model.encode_batch(texts)

    assert isinstance(result, list)
    assert len(result) == len(texts)


def test_sentence_transformer_embedding_lazy_initialization() -> None:
    """遅延初期化が正常に動作することを確認する。"""
    from shogi_kif_rag.vector.embedding import SentenceTransformerEmbedding

    embedding_model = SentenceTransformerEmbedding()
    # 初期化前に_modelはNoneであることを確認
    assert embedding_model._model is None

    # encodeを呼ぶと初期化される
    embedding_model.encode("テスト")
    assert embedding_model._model is not None


def test_databricks_embedding_type_checking() -> None:
    """DatabricksEmbeddingが型チェック用にインポートできることを確認する。"""
    from shogi_kif_rag.vector.embedding import DatabricksEmbedding

    # 実際の初期化はDatabricks依存があるため行わない
    assert DatabricksEmbedding is not None
