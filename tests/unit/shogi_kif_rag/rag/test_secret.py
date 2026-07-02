"""secrets.py のユニットテスト。"""

import sys
from types import ModuleType
from typing import Callable, Optional

from pytest_mock import MockerFixture

from shogi_kif_rag.rag.secrets import get_gemini_api_key, get_groq_api_key, get_secret


class _FakeSecretValue:
    """WorkspaceClient.secrets.get() の戻り値を模したスタブ。"""

    def __init__(self, value: Optional[str]) -> None:
        self.value = value


class _FakeSecretsAPI:
    """WorkspaceClient.secrets を模したスタブ。"""

    def __init__(self, value: Optional[str]) -> None:
        self._value = value

    def get(self, scope: str, key: str) -> _FakeSecretValue:
        return _FakeSecretValue(self._value)


class _FakeWorkspaceClient:
    """databricks.sdk.WorkspaceClient を模したスタブ。"""

    def __init__(self, value: Optional[str] = "dummy-secret") -> None:
        self.secrets = _FakeSecretsAPI(value)


def _inject_databricks_sdk_module(
    mocker: MockerFixture, workspace_client_factory: Callable[[], object]
) -> None:
    """databricks.sdk モジュールをsys.modulesに注入する。

    `get_secret` 内の `from databricks.sdk import WorkspaceClient` は
    関数ローカルimportのため、使用箇所を直接 `mocker.patch` することができない。
    そのため、importが解決される `sys.modules` にフェイクモジュールを
    差し込むことでモック化する。

    Args:
        mocker: pytest-mockのmockerフィクスチャ。
        workspace_client_factory: WorkspaceClient() 呼び出し時に実行される callable。
    """
    fake_sdk_module = ModuleType("databricks.sdk")
    fake_sdk_module.WorkspaceClient = workspace_client_factory  # type: ignore[attr-defined]
    fake_package_module = ModuleType("databricks")
    mocker.patch.dict(
        sys.modules,
        {"databricks": fake_package_module, "databricks.sdk": fake_sdk_module},
    )


def test_get_secret_Databricks接続成功時_シークレット値を返す(mocker: MockerFixture) -> None:
    # Arrange
    _inject_databricks_sdk_module(mocker, lambda: _FakeWorkspaceClient("dummy-secret"))

    # Act
    result = get_secret("llm", "gemini_api_key")

    # Assert
    assert result == "dummy-secret"


def test_get_secret_Databricks接続失敗時_環境変数から取得して返す(mocker: MockerFixture) -> None:
    # Arrange
    def _raise_connection_error() -> None:
        raise RuntimeError("接続失敗")

    _inject_databricks_sdk_module(mocker, _raise_connection_error)
    mock_getenv = mocker.patch("os.getenv")
    mock_getenv.return_value = "env-secret"

    # Act
    result = get_secret("llm", "gemini_api_key")

    # Assert
    assert result == "env-secret"


def test_get_secret_Databricksも環境変数も失敗時_Noneを返す(mocker: MockerFixture) -> None:
    # Arrange
    def _raise_connection_error() -> None:
        raise RuntimeError("接続失敗")

    _inject_databricks_sdk_module(mocker, _raise_connection_error)
    mock_getenv = mocker.patch("os.getenv")
    mock_getenv.return_value = None

    # Act
    result = get_secret("llm", "gemini_api_key")

    # Assert
    assert result is None


def test_get_secret_Databricks接続失敗時_環境変数キーはscopeとkeyを結合した形式で参照する(
    mocker: MockerFixture,
) -> None:
    # Arrange
    def _raise_connection_error() -> None:
        raise RuntimeError("接続失敗")

    _inject_databricks_sdk_module(mocker, _raise_connection_error)
    mock_getenv = mocker.patch("os.getenv")
    mock_getenv.return_value = "env-secret"

    # Act
    get_secret("llm", "gemini_api_key")

    # Assert
    mock_getenv.assert_called_once_with("llm_gemini_api_key")


def test_get_gemini_api_key_呼び出し時_get_secretをllmスコープとgemini_api_keyキーで呼び出す(
    mocker: MockerFixture,
) -> None:
    # Arrange
    mock_get_secret = mocker.patch("shogi_kif_rag.rag.secrets.get_secret")
    mock_get_secret.return_value = "gemini-key"

    # Act
    result = get_gemini_api_key()

    # Assert
    mock_get_secret.assert_called_once_with("llm", "gemini_api_key")
    assert result == "gemini-key"


def test_get_groq_api_key_呼び出し時_get_secretをllmスコープとgroq_api_keyキーで呼び出す(
    mocker: MockerFixture,
) -> None:
    # Arrange
    mock_get_secret = mocker.patch("shogi_kif_rag.rag.secrets.get_secret")
    mock_get_secret.return_value = "groq-key"

    # Act
    result = get_groq_api_key()

    # Assert
    mock_get_secret.assert_called_once_with("llm", "groq_api_key")
    assert result == "groq-key"
