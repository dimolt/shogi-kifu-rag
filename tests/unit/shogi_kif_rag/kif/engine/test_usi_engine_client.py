"""usi_engine_client モジュールのユニットテスト"""

import subprocess
from unittest.mock import MagicMock, call, patch

import pytest

from shogi_kif_rag.kif.engine.usi_engine_client import UsiEngineClient


@pytest.fixture
def mock_process() -> MagicMock:
    """モック化された subprocess.Popen プロセスを提供する。"""
    process = MagicMock(spec=subprocess.Popen)
    process.stdin = MagicMock()
    process.stdout = MagicMock()
    process.stderr = MagicMock()
    return process


@pytest.fixture
def client() -> UsiEngineClient:
    """テスト用 UsiEngineClient インスタンスを提供する。"""
    return UsiEngineClient(engine_path="/path/to/engine", options="Threads=1")


def test_init_エンジンパスとオプションを渡すと_正しく初期化される() -> None:
    # Act
    client = UsiEngineClient(engine_path="/path/to/engine", options="Threads=1")

    # Assert
    assert client.engine_path == "/path/to/engine"
    assert client.options == "Threads=1"
    assert client.process is None


def test_start_プロセスが未起動の場合と_Popenが呼ばれプロセスが設定される(
    client: UsiEngineClient,
) -> None:
    # Arrange
    mock_process = MagicMock(spec=subprocess.Popen)
    mock_process.stdin = MagicMock()
    mock_process.stdout = MagicMock()
    mock_process.stderr = MagicMock()
    with patch("shogi_kif_rag.kif.engine.usi_engine_client.subprocess.Popen", return_value=mock_process):
        # Act
        client.start()

        # Assert
        assert client.process is mock_process


def test_start_プロセスが既に起動している場合と_RuntimeErrorを送出する(
    client: UsiEngineClient, mock_process: MagicMock
) -> None:
    # Arrange
    client.process = mock_process

    # Act & Assert
    with pytest.raises(RuntimeError) as exc_info:
        client.start()

    assert str(exc_info.value) == "Engine is already running"


def test_initialize_usi_プロセスが起動している場合と_正しいコマンドが書き込まれる(
    client: UsiEngineClient, mock_process: MagicMock
) -> None:
    # Arrange
    client.process = mock_process
    mock_process.stdout.readline.side_effect = ["readyok"]

    # Act
    client.initialize_usi(usi_hash=512)

    # Assert
    expected_calls = [
        call("usi\n"),
        call("setoption name USI_Hash value 512\n"),
        call("setoption name ResignValue value 99999\n"),
        call("setoption name DrawValueBlack value 0\n"),
        call("setoption name DrawValueWhite value 0\n"),
        call("isready\n"),
    ]
    mock_process.stdin.write.assert_has_calls(expected_calls, any_order=False)
    assert mock_process.stdin.flush.call_count == len(expected_calls)


def test_initialize_usi_プロセスが起動していない場合と_RuntimeErrorを送出する(
    client: UsiEngineClient,
) -> None:
    # Act & Assert
    with pytest.raises(RuntimeError) as exc_info:
        client.initialize_usi()

    assert str(exc_info.value) == "Engine is not running"


def test_stop_プロセスが起動している場合と_terminateとwaitが呼ばれプロセスがNoneになる(
    client: UsiEngineClient, mock_process: MagicMock
) -> None:
    # Arrange
    client.process = mock_process

    # Act
    client.stop()

    # Assert
    mock_process.terminate.assert_called_once()
    mock_process.wait.assert_called_once()
    assert client.process is None


def test_stop_プロセスが起動していない場合と_何もしない(client: UsiEngineClient) -> None:
    # Act & Assert (例外が発生しないことを確認)
    client.stop()
    assert client.process is None


def test_analyze_position_プロセスが起動している場合と_正しいコマンドが書き込まれる(
    client: UsiEngineClient, mock_process: MagicMock
) -> None:
    # Arrange
    client.process = mock_process
    sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"

    # Act
    result = client.analyze_position(sfen, depth=15, nodes=500000)

    # Assert
    expected_calls = [
        call(f"position sfen {sfen}\n"),
        call("go depth 15 nodes 500000\n"),
    ]
    mock_process.stdin.write.assert_has_calls(expected_calls, any_order=False)
    assert result == {"best_move": "", "score_cp": 0, "pv": []}


def test_analyze_position_プロセスが起動していない場合と_RuntimeErrorを送出する(
    client: UsiEngineClient,
) -> None:
    # Act & Assert
    with pytest.raises(RuntimeError) as exc_info:
        client.analyze_position("lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1")

    assert str(exc_info.value) == "Engine is not running"


def test_analyze_position_with_time_通常の評価値を含む出力をパースする(
    client: UsiEngineClient, mock_process: MagicMock
) -> None:
    # Arrange
    client.process = mock_process
    mock_output = """info depth 10 score cp 150 pv 2g2f 3c3d 2f2e
info depth 15 score cp 200 pv 2g2f 3c3d 2f2e 3d3e
bestmove 2g2f"""
    mock_process.communicate.return_value = (mock_output, "")

    # Act
    result = client.analyze_position_with_time(
        "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1",
        think_time=0.1,
    )

    # Assert
    assert result["best_move"] == "2g2f"
    assert result["score_cp"] == 200
    assert result["pv"] == "2g2f 3c3d 2f2e 3d3e"


def test_analyze_position_with_time_詰みの評価値を含む出力をパースする(
    client: UsiEngineClient, mock_process: MagicMock
) -> None:
    # Arrange
    client.process = mock_process
    mock_output = """info depth 20 score mate 5 pv 2g2f 3c3d 2f2e
bestmove 2g2f"""
    mock_process.communicate.return_value = (mock_output, "")

    # Act
    result = client.analyze_position_with_time(
        "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1",
        think_time=0.1,
    )

    # Assert
    assert result["best_move"] == "2g2f"
    assert result["score_cp"] == 30000
    assert result["pv"] == "2g2f 3c3d 2f2e"


def test_analyze_position_with_time_負の詰みを含む出力をパースする(
    client: UsiEngineClient, mock_process: MagicMock
) -> None:
    # Arrange
    client.process = mock_process
    mock_output = """info depth 15 score mate -3 pv 8c8d
bestmove 8c8d"""
    mock_process.communicate.return_value = (mock_output, "")

    # Act
    result = client.analyze_position_with_time(
        "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1",
        think_time=0.1,
    )

    # Assert
    assert result["best_move"] == "8c8d"
    assert result["score_cp"] == -30000
    assert result["pv"] == "8c8d"


def test_analyze_position_with_time_bestmoveがない場合と_resignを返す(
    client: UsiEngineClient, mock_process: MagicMock
) -> None:
    # Arrange
    client.process = mock_process
    mock_output = "info depth 10 score cp -500"
    mock_process.communicate.return_value = (mock_output, "")

    # Act
    result = client.analyze_position_with_time(
        "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1",
        think_time=0.1,
    )

    # Assert
    assert result["best_move"] == "resign"
    assert result["score_cp"] == -500
    assert result["pv"] == ""


def test_analyze_position_with_time_プロセスが起動していない場合と_RuntimeErrorを送出する(
    client: UsiEngineClient,
) -> None:
    # Act & Assert
    with pytest.raises(RuntimeError) as exc_info:
        client.analyze_position_with_time(
            "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"
        )

    assert str(exc_info.value) == "Engine is not running"


def test_analyze_position_with_time_communicateがタイムアウトした場合と_killを呼び出す(
    client: UsiEngineClient, mock_process: MagicMock
) -> None:
    # Arrange
    client.process = mock_process
    mock_process.communicate.side_effect = [
        subprocess.TimeoutExpired("cmd", 10),
        ("", ""),
    ]

    # Act
    result = client.analyze_position_with_time(
        "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1",
        think_time=0.1,
    )

    # Assert
    mock_process.kill.assert_called_once()
    assert result["best_move"] == "resign"


def test_analyze_position_reusable_通常の評価値を含む出力をパースする(
    client: UsiEngineClient, mock_process: MagicMock
) -> None:
    # Arrange
    client.process = mock_process
    mock_process.stdout.readline.side_effect = [
        "info depth 10 score cp 100 pv 2g2f\n",
        "info depth 15 score cp 150 pv 2g2f 3c3d\n",
        "bestmove 2g2f\n",
    ]

    # Act
    result = client.analyze_position_reusable(
        "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1",
        think_time=0.1,
    )

    # Assert
    assert result["best_move"] == "2g2f"
    assert result["score_cp"] == 150
    assert result["pv"] == "2g2f 3c3d"


def test_analyze_position_reusable_プロセスが起動していない場合と_RuntimeErrorを送出する(
    client: UsiEngineClient,
) -> None:
    # Act & Assert
    with pytest.raises(RuntimeError) as exc_info:
        client.analyze_position_reusable(
            "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"
        )

    assert str(exc_info.value) == "Engine is not running"


def test_analyze_position_reusable_PVが8手より長い場合と_先頭8手のみを返す(
    client: UsiEngineClient, mock_process: MagicMock
) -> None:
    # Arrange
    client.process = mock_process
    long_pv = "2g2f 3c3d 2f2e 3d3e 8h2b+ 2b3c 2b2c 3e3d 4g4f 3c4d"
    mock_process.stdout.readline.side_effect = [
        f"info depth 15 score cp 200 pv {long_pv}\n",
        "bestmove 2g2f\n",
    ]

    # Act
    result = client.analyze_position_reusable(
        "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1",
        think_time=0.1,
    )

    # Assert
    assert result["pv"] == "2g2f 3c3d 2f2e 3d3e 8h2b+ 2b3c 2b2c 3e3d"
