"""LocalAnalyzeSettings のユニットテスト"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from shogi_kif_rag.kif.config.local_analyze_settings import (
    DEFAULT_ANALYSIS_DEPTH,
    DEFAULT_ANALYSIS_NODES,
    DEFAULT_CSV_OUTPUT_DIR,
    DEFAULT_KIF_INPUT_DIR,
    DEFAULT_YANEURAOU_PATH,
    LocalAnalyzeSettings,
)


@pytest.fixture
def clear_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """設定関連の環境変数をクリアする。"""
    for key in (
        "YANEURAOU_PATH",
        "YANEURAOU_OPTIONS",
        "KIF_INPUT_DIR",
        "CSV_OUTPUT_DIR",
        "ANALYSIS_DEPTH",
        "ANALYSIS_NODES",
    ):
        monkeypatch.delenv(key, raising=False)


def test_local_analyze_settings_環境変数未設定だと_デフォルト値を返す(
    clear_env_vars: None, tmp_path: Path
) -> None:
    # Arrange
    non_existent_env_file = tmp_path / ".env.local_analyze"

    # Act
    settings = LocalAnalyzeSettings(_env_file=non_existent_env_file)

    # Assert
    assert settings.yaneuraou_path == DEFAULT_YANEURAOU_PATH
    assert settings.yaneuraou_options == ""
    assert settings.kif_input_dir == DEFAULT_KIF_INPUT_DIR
    assert settings.csv_output_dir == DEFAULT_CSV_OUTPUT_DIR
    assert settings.analysis_depth == DEFAULT_ANALYSIS_DEPTH
    assert settings.analysis_nodes == DEFAULT_ANALYSIS_NODES


def test_local_analyze_settings_kif_input_dirに文字列を渡すと_Path型に変換される(
    clear_env_vars: None, tmp_path: Path
) -> None:
    # Arrange
    non_existent_env_file = tmp_path / ".env.local_analyze"

    # Act
    settings = LocalAnalyzeSettings(
        _env_file=non_existent_env_file, kif_input_dir="custom/kif"
    )

    # Assert
    assert settings.kif_input_dir == Path("custom/kif")


def test_local_analyze_settings_envファイルに値があると_その値を読み込む(
    clear_env_vars: None, tmp_path: Path
) -> None:
    # Arrange
    env_file = tmp_path / ".env.local_analyze"
    env_file.write_text(
        "yaneuraou_path=custom_engine.exe\nanalysis_depth=30\n", encoding="utf-8"
    )

    # Act
    settings = LocalAnalyzeSettings(_env_file=env_file)

    # Assert
    assert settings.yaneuraou_path == "custom_engine.exe"
    assert settings.analysis_depth == 30


def test_local_analyze_settings_未定義の環境変数があると_無視する(
    clear_env_vars: None, tmp_path: Path
) -> None:
    # Arrange
    env_file = tmp_path / ".env.local_analyze"
    env_file.write_text("unknown_setting=some_value\n", encoding="utf-8")

    # Act
    settings = LocalAnalyzeSettings(_env_file=env_file)

    # Assert
    assert settings.yaneuraou_path == DEFAULT_YANEURAOU_PATH


def test_local_analyze_settings_analysis_depthに0を渡すと_ValidationErrorを送出する(
    clear_env_vars: None, tmp_path: Path
) -> None:
    # Arrange
    non_existent_env_file = tmp_path / ".env.local_analyze"

    # Act & Assert
    with pytest.raises(ValidationError):
        LocalAnalyzeSettings(_env_file=non_existent_env_file, analysis_depth=0)


def test_local_analyze_settings_analysis_nodesに負の値を渡すと_ValidationErrorを送出する(
    clear_env_vars: None, tmp_path: Path
) -> None:
    # Arrange
    non_existent_env_file = tmp_path / ".env.local_analyze"

    # Act & Assert
    with pytest.raises(ValidationError):
        LocalAnalyzeSettings(_env_file=non_existent_env_file, analysis_nodes=-1)


def test_local_analyze_settings_analysis_depthに正の整数を渡すと_その値を保持する(
    clear_env_vars: None, tmp_path: Path
) -> None:
    # Arrange
    non_existent_env_file = tmp_path / ".env.local_analyze"

    # Act
    settings = LocalAnalyzeSettings(_env_file=non_existent_env_file, analysis_depth=1)

    # Assert
    assert settings.analysis_depth == 1
