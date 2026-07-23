

def get_secret(scope: str, key: str) -> str | None:
    """Databricks Secretsからシークレットを取得

    Args:
        scope: スコープ名
        key: キー名

    Returns:
        シークレット値
    """
    try:
        from databricks.sdk import WorkspaceClient

        client = WorkspaceClient()
        return client.secrets.get(scope=scope, key=key).value  # type: ignore[attr-defined]
    except Exception:
        # ローカル実行時は環境変数から取得
        import os

        return os.getenv(f"{scope}_{key}")


def get_gemini_api_key() -> str | None:
    """Gemini APIキーを取得

    Returns:
        Gemini APIキー
    """
    return get_secret("llm", "gemini_api_key")


def get_groq_api_key() -> str | None:
    """Groq APIキーを取得

    Returns:
        Groq APIキー
    """
    return get_secret("llm", "groq_api_key")
