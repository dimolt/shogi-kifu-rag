from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Databricks関連のimportは依存関係を避けるためTYPE_CHECKINGのみ
    from databricks.sdk import WorkspaceClient



class DatabricksEmbedding:
    """Databricks AI Search/MLflow Model Servingを使用したEmbeddingModel実装。

    Databricks Foundational ModelsまたはMLflow Model Servingに対応する。
    """

    def __init__(
        self,
        endpoint_name: str,
        databricks_client: WorkspaceClient | None = None,
    ) -> None:
        """DatabricksEmbeddingを初期化する。

        Args:
            endpoint_name: Databricks Model Servingのエンドポイント名。
            databricks_client: Databricks WorkspaceClientインスタンス。
                省略時はデフォルト設定で初期化される。
        """
        self._endpoint_name = endpoint_name
        self._client: WorkspaceClient | None = databricks_client

    def _ensure_client(self) -> WorkspaceClient:
        """Databricksクライアントが初期化されていることを確認する。

        Returns:
            WorkspaceClientインスタンス。
        """
        if self._client is None:
            from databricks.sdk import WorkspaceClient

            self._client = WorkspaceClient()
        return self._client

    def encode(self, text: str) -> list[float]:
        """単一テキストをEmbeddingベクトルに変換する。

        Args:
            text: エンコード対象のテキスト。

        Returns:
            Embeddingベクトル（floatのリスト）。
        """
        client = self._ensure_client()
        response = client.serving_endpoints.invoke(
            endpoint=self._endpoint_name,
            inputs={'input': [text]},
        )
        # レスポンス形式はendpointによって異なる可能性があるため、
        # 実際のendpointに合わせて調整が必要
        return response.as_dict()['predictions'][0]['embedding']

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """テキストリストをEmbeddingベクトルのリストに変換する。

        Args:
            texts: エンコード対象のテキストリスト。

        Returns:
            Embeddingベクトルのリスト。
        """
        client = self._ensure_client()
        response = client.serving_endpoints.invoke(
            endpoint=self._endpoint_name,
            inputs={'input': texts},
        )
        # レスポンス形式はendpointによって異なる可能性があるため、
        # 実際のendpointに合わせて調整が必要
        predictions = response.as_dict()['predictions']
        return [pred['embedding'] for pred in predictions]
