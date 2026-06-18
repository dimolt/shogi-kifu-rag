"""KIFパーサのテスト"""

import pytest


def test_kif_to_positions_initial_position():
    """KIF文字列をパースして初期局面を取得できること"""
    # Arrange
    kif_content = """# KIF形式の棋譜
先手：テスト先手
後手：テスト後手
手数----指手---------駒
 1 7六歩(77)
"""
    
    # Act
    from src.kif_parser.parser import kif_to_positions
    positions = kif_to_positions(kif_content)
    
    # Assert
    assert len(positions) >= 1
    initial_position = positions[0]
    assert initial_position["move_number"] == 0
    assert initial_position["move_usi"] == ""
    assert initial_position["player"] == "black"
    assert initial_position["black_player"] == "テスト先手"
    assert initial_position["white_player"] == "テスト後手"


def test_kif_to_positions_with_moves():
    """KIF文字列をパースして指し手を含む局面リストを取得できること"""
    # Arrange
    # sample.kifの形式を参考にテストデータを作成
    kif_content = """先手：テスト先手
後手：テスト後手
手数----指手---------消費時間--
   1 ２六歩(27)    ( 0:00/00:00:00)
   2 ３四歩(33)    ( 0:01/00:00:01)
"""
    
    # Act
    from src.kif_parser.parser import kif_to_positions
    import shogi
    import shogi.KIF
    
    # デバッグ: KIFパース結果を確認
    kif = shogi.KIF.Parser.parse_str(kif_content)[0]
    print(f"names: {kif.get('names', [])}")
    print(f"moves: {kif.get('moves', [])}")
    print(f"keys: {kif.keys()}")
    
    positions = kif_to_positions(kif_content)
    
    # Assert
    assert len(positions) >= 3  # 初期局面 + 2手
    
    # 1手目の検証
    first_move = positions[1]
    assert first_move["move_number"] == 1
    assert first_move["player"] == "black"
    assert first_move["move_usi"] == "2g2f"
    
    # 2手目の検証
    second_move = positions[2]
    assert second_move["move_number"] == 2
    assert second_move["player"] == "white"
    assert second_move["move_usi"] == "3c3d"


def test_usi_to_japanese():
    """USI形式の指し手を日本語表記に変換できること"""
    # Arrange
    usi_move = "2g2f"
    
    # Act
    from src.kif_parser.japanese_converter import usi_to_japanese
    japanese = usi_to_japanese(usi_move)
    
    # Assert
    assert japanese == "4八歩"
