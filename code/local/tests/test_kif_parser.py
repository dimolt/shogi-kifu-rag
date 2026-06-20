"""ローカルKIFパーサのテスト（sharedのラッパー）"""


def test_kif_parser_wrapper_import():
    """sharedモジュールから正しくインポートできること"""
    # Arrange & Act
    from kif_parser.parser import kif_to_positions, usi_to_japanese

    # Assert
    assert kif_to_positions is not None
    assert usi_to_japanese is not None


def test_kif_parser_wrapper_functionality():
    """ラッパー経由でsharedモジュールの機能を使用できること"""
    # Arrange
    kif_content = """先手：テスト先手
後手：テスト後手
手数----指手---------消費時間--
   1 ２六歩(27)    ( 0:00/00:00:00)
"""

    # Act
    from kif_parser.parser import kif_to_positions
    positions = kif_to_positions(kif_content)

    # Assert
    assert len(positions) >= 1
    assert positions[0]["move_number"] == 0
