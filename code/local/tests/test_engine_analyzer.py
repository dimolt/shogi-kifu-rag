"""やねうら王エンジン連携のテスト"""

import pytest
from unittest.mock import Mock, patch


def test_yaneuraou_analyzer_initialization():
    """YaneuraOuAnalyzerの初期化が正しくできること"""
    # Arrange & Act
    from engine_analyzer.analyzer import YaneuraOuAnalyzer
    analyzer = YaneuraOuAnalyzer("YaneuraOu_nnue.exe", "USI_Hash 1024")

    # Assert
    assert analyzer.engine_path == "YaneuraOu_nnue.exe"
    assert analyzer.options == "USI_Hash 1024"
    assert analyzer.process is None


def test_yaneuraou_analyzer_start_stop():
    """エンジンの起動と停止が正しくできること"""
    # Arrange
    from engine_analyzer.analyzer import YaneuraOuAnalyzer
    analyzer = YaneuraOuAnalyzer("YaneuraOu_nnue.exe")

    # Act & Assert
    with patch("subprocess.Popen") as mock_popen:
        mock_process = Mock()
        mock_popen.return_value = mock_process

        analyzer.start()
        assert analyzer.process == mock_process
        mock_popen.assert_called_once()

        analyzer.stop()
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()
        assert analyzer.process is None


def test_yaneuraou_analyzer_analyze_position():
    """局面の解析が正しくできること"""
    # Arrange
    from engine_analyzer.analyzer import YaneuraOuAnalyzer
    analyzer = YaneuraOuAnalyzer("YaneuraOu_nnue.exe")
    analyzer.process = Mock()
    analyzer.process.stdin = Mock()

    # Act
    result = analyzer.analyze_position(
        "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1",
        depth=20,
        nodes=1000000,
    )

    # Assert
    assert "best_move" in result
    assert "score_cp" in result
    assert "pv" in result
