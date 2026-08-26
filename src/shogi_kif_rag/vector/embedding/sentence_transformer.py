from __future__ import annotations

from sentence_transformers import SentenceTransformer


class SentenceTransformerEmbedding:
    """SentenceTransformerを使用したEmbeddingModel実装。

    既存のSentenceTransformer使用をラップし、共通インターフェースを提供する。
    """

    DEFAULT_MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
    DEFAULT_BATCH_SIZE = 32

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        """SentenceTransformerEmbeddingを初期化する。

        Args:
            model_name: 使用するモデル名。デフォルトは'all-MiniLM-L6-v2'。
            batch_size: バッチ処理時のバッチサイズ。デフォルトは32。
        """
        self._model_name = model_name
        self._batch_size = batch_size
        self._model: SentenceTransformer | None = None

    def _ensure_model(self) -> None:
        """モデルが初期化されていることを確認する。

        未初期化の場合はモデルをロードする。
        """
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)

    def encode(self, text: str) -> list[float]:
        """単一テキストをEmbeddingベクトルに変換する。

        Args:
            text: エンコード対象のテキスト。

        Returns:
            Embeddingベクトル（floatのリスト）。
        """
        self._ensure_model()
        if self._model is None:
            raise RuntimeError('Model initialization failed')
        return self._model.encode(text).tolist()

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """テキストリストをEmbeddingベクトルのリストに変換する。

        Args:
            texts: エンコード対象のテキストリスト。

        Returns:
            Embeddingベクトルのリスト。
        """
        self._ensure_model()
        if self._model is None:
            raise RuntimeError('Model initialization failed')
        return self._model.encode(
            texts,
            batch_size=self._batch_size,
            show_progress_bar=False,
        ).tolist()
