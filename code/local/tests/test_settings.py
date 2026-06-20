"""ローカル設定管理のテスト"""

import pytest
from pydantic import ValidationError


def test_local_settings_default_values():
    """デフォルト値が正しく設定されること"""
    # Arrange & Act
    from config.settings import LocalSettings
    settings = LocalSettings(env_file=None)

    # Assert
    # Note: yaneuraou_path and yaneuraou_options may be set from environment variables
    # We focus on checking the folder-related paths that changed due to folder reorganization
    assert settings.yaneuraou_path != ""
    assert settings.kif_input_dir == "data/kif_files"
    assert settings.csv_output_dir == "data/output"
    assert settings.analysis_depth == 20
    assert settings.analysis_nodes == 1000000


def test_local_settings_from_env():
    """環境変数から設定を読み込めること"""
    # Arrange
    import os
    os.environ["YANEURAOU_PATH"] = "custom_engine.exe"
    os.environ["ANALYSIS_DEPTH"] = "30"

    # Act
    from config.settings import LocalSettings
    settings = LocalSettings()

    # Assert
    assert settings.yaneuraou_path == "custom_engine.exe"
    assert settings.analysis_depth == 30

    # Cleanup
    del os.environ["YANEURAOU_PATH"]
    del os.environ["ANALYSIS_DEPTH"]
