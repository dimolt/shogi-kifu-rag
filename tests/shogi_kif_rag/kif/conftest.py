"""local_analyze.py テスト用の共有フィクスチャ。"""

import pytest

from shogi_kif_rag.kif.local_analyze import AnalysisRow, PositionRecord


@pytest.fixture
def sample_position() -> PositionRecord:
    """1件分のテスト用局面レコードを提供する。"""
    return {
        "move_number": 1,
        "sfen": "sfen_after_move_1",
        "prev_sfen": "sfen_initial",
        "move_usi": "7g7f",
        "player": "black",
        "black_player": "先手太郎",
        "white_player": "後手次郎",
    }


@pytest.fixture
def sample_positions(sample_position: PositionRecord) -> list[PositionRecord]:
    """複数件のテスト用局面レコードを提供する。"""
    initial: PositionRecord = {
        "move_number": 0,
        "sfen": "sfen_initial",
        "prev_sfen": "sfen_initial",
        "move_usi": "",
        "player": "black",
        "black_player": "先手太郎",
        "white_player": "後手次郎",
    }
    return [initial, sample_position]


@pytest.fixture
def sample_analysis_row(sample_position: PositionRecord) -> AnalysisRow:
    """エンジン解析結果を付与したテスト用出力行を提供する。"""
    return {
        **sample_position,
        "game_id": "sample_game",
        "best_move": "2g2f",
        "score_cp": 120,
        "pv": "2g2f 8c8d",
    }


@pytest.fixture
def mock_engine_result() -> dict:
    """UsiEngineClient.analyze_position_reusable の戻り値を模したデータを提供する。"""
    return {"best_move": "2g2f", "score_cp": 120, "pv": "2g2f 8c8d"}