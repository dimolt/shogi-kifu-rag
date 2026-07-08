"""Databricks CLI呼び出し用の共通ヘルパー。

tests/conftest.py と tests/e2e/conftest.py の双方から参照される。
conftest.py同士の直接import（モジュール名"conftest"の衝突による循環import）を
避けるため、本モジュールに切り出している。
"""
import os


def databricks_cli_base_args() -> list[str]:
    """環境に応じてdatabricks CLIの認証引数を決定する。

    ローカル実行時はDATABRICKS_CONFIG_PROFILE環境変数で指定したプロファイルを使用し、
    CI/CD（サービスプリンシパル認証）ではプロファイル指定なしで環境変数ベースの
    デフォルト認証チェーンに委ねる。

    Returns:
        list[str]: `--profile`引数のリスト。DATABRICKS_CONFIG_PROFILE未設定時は
        空リスト。
    """
    profile = os.environ.get("DATABRICKS_CONFIG_PROFILE")
    if profile:
        return ["--profile", profile]
    return []
