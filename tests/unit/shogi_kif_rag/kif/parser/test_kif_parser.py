"""kif_parser.py の単体テスト"""

import shogi

from shogi_kif_rag.kif.parser import (
    KifParser,
    detect_encoding,
    kif_to_positions,
)

# ---------------------------------------------------------------------------
# detect_encoding（モジュール関数）
# ---------------------------------------------------------------------------


def test_detect_encoding_UTF8ファイルを渡すと_utf8を返す(kif_file_utf8):
    # Act
    result = detect_encoding(kif_file_utf8)

    # Assert
    assert result.lower() == "utf-8"


def test_detect_encoding_CP932ファイルを渡すと_cp932を返す(kif_file_cp932):
    # Act
    result = detect_encoding(kif_file_cp932)

    # Assert
    assert result == "cp932"


def test_detect_encoding_cp1006が検出されると_cp932に変換する(tmp_path, mocker):
    # Arrange
    file_path = tmp_path / "dummy.kif"
    file_path.write_bytes(b"dummy")
    mocker.patch("chardet.detect", return_value={"encoding": "cp1006"})

    # Act
    result = detect_encoding(str(file_path))

    # Assert
    assert result == "cp932"


def test_detect_encoding_検出結果がNoneの場合_utf8を返す(tmp_path, mocker):
    # Arrange
    file_path = tmp_path / "dummy.kif"
    file_path.write_bytes(b"dummy")
    mocker.patch("chardet.detect", return_value={"encoding": None})

    # Act
    result = detect_encoding(str(file_path))

    # Assert
    assert result == "utf-8"


# ---------------------------------------------------------------------------
# KifParser._detect_encoding / _load_file_content
# ---------------------------------------------------------------------------


def test_KifParser_detect_encoding_UTF8ファイルを渡すと_utf8を返す(kif_file_utf8):
    # Arrange
    parser = KifParser(kif_file_utf8)

    # Act
    result = parser._detect_encoding()

    # Assert
    assert result.lower() == "utf-8"


def test_KifParser_detect_encoding_CP932ファイルを渡すと_cp932を返す(kif_file_cp932):
    # Arrange
    parser = KifParser(kif_file_cp932)

    # Act
    result = parser._detect_encoding()

    # Assert
    assert result == "cp932"


def test_KifParser_load_file_content_指定エンコーディングで内容を読み込む(
    kif_file_cp932, sample_kif_content
):
    # Arrange
    parser = KifParser(kif_file_cp932)

    # Act
    result = parser._load_file_content("cp932")

    # Assert
    assert result == sample_kif_content


def test_KifParser_load_file_content_デコードできない文字は置換される(tmp_path):
    # Arrange
    file_path = tmp_path / "broken.kif"
    file_path.write_bytes(b"\x81\xff\x81\xff")  # cp932として不正なバイト列
    parser = KifParser(str(file_path))

    # Act
    result = parser._load_file_content("cp932")

    # Assert
    assert "\ufffd" in result


# ---------------------------------------------------------------------------
# KifParser._extract_player_info
# ---------------------------------------------------------------------------


def test_extract_player_info_名前が両方存在すると_そのまま返す():
    # Arrange
    parser = KifParser("dummy_path")
    kif = {"names": ["先手太郎", "後手次郎"]}

    # Act
    black_player, white_player = parser._extract_player_info(kif)

    # Assert
    assert (black_player, white_player) == ("先手太郎", "後手次郎")


def test_extract_player_info_名前が存在しないと_デフォルト名を返す():
    # Arrange
    parser = KifParser("dummy_path")
    kif = {"names": []}

    # Act
    black_player, white_player = parser._extract_player_info(kif)

    # Assert
    assert (black_player, white_player) == ("先手", "後手")


# ---------------------------------------------------------------------------
# KifParser._parse_move
# ---------------------------------------------------------------------------


def test_parse_move_有効なUSI文字列を渡すと_Moveと同じ文字列を返す():
    # Arrange
    parser = KifParser("dummy_path")

    # Act
    move_int, move_usi = parser._parse_move("7g7f")

    # Assert
    assert (move_int, move_usi) == (shogi.Move.from_usi("7g7f"), "7g7f")


def test_parse_move_不正なUSI文字列を渡すと_Noneと空文字を返す():
    # Arrange
    parser = KifParser("dummy_path")

    # Act
    move_int, move_usi = parser._parse_move("invalid_move")

    # Assert
    assert (move_int, move_usi) == (None, "")


def test_parse_move_Moveオブジェクトを渡すと_USI文字列に変換する():
    # Arrange
    parser = KifParser("dummy_path")
    move = shogi.Move.from_usi("7g7f")

    # Act
    move_int, move_usi = parser._parse_move(move)

    # Assert
    assert (move_int, move_usi) == (move, "7g7f")


# ---------------------------------------------------------------------------
# KifParser._build_initial_record / _build_move_record
# ---------------------------------------------------------------------------


def test_build_initial_record_初期局面のレコードを構築する():
    # Arrange
    parser = KifParser("dummy_path")
    board = shogi.Board()

    # Act
    record = parser._build_initial_record(board, "先手太郎", "後手次郎")

    # Assert
    assert record == {
        "move_number": 0,
        "sfen": board.sfen(),
        "prev_sfen": board.sfen(),
        "move_usi": "",
        "player": "black",
        "black_player": "先手太郎",
        "white_player": "後手次郎",
    }


def test_build_move_record_指し手のレコードを構築する():
    # Arrange
    parser = KifParser("dummy_path")
    board = shogi.Board()
    move = shogi.Move.from_usi("7g7f")
    prev_sfen = board.sfen()
    board.push(move)

    # Act
    record = parser._build_move_record(
        board, move, "7g7f", "black", "先手太郎", "後手次郎", 1, prev_sfen
    )

    # Assert
    assert record == {
        "move_number": 1,
        "sfen": board.sfen(),
        "prev_sfen": prev_sfen,
        "move_usi": "7g7f",
        "player": "black",
        "black_player": "先手太郎",
        "white_player": "後手次郎",
    }


# ---------------------------------------------------------------------------
# KifParser.load_file（統合テスト）
# ---------------------------------------------------------------------------


def test_load_file_正常なKIFファイルを渡すと_初期局面を含む全レコードを返す(
    kif_file_utf8,
):
    # Arrange
    parser = KifParser(kif_file_utf8)

    # Act
    records = parser.load_file()

    # Assert
    assert len(records) == 4  # 初期局面 + 3手


def test_load_file_正常なKIFファイルを渡すと_プレイヤー名を各レコードに含む(
    kif_file_utf8,
):
    # Arrange
    parser = KifParser(kif_file_utf8)

    # Act
    records = parser.load_file()

    # Assert
    assert all(
        (r["black_player"], r["white_player"]) == ("先手太郎", "後手次郎")
        for r in records
    )


def test_load_file_正常なKIFファイルを渡すと_最終局面のSFENが指し手を反映する(
    kif_file_utf8,
):
    # Arrange
    parser = KifParser(kif_file_utf8)
    board = shogi.Board()
    for usi in ("7g7f", "3c3d", "2g2f"):
        board.push(shogi.Move.from_usi(usi))

    # Act
    records = parser.load_file()

    # Assert
    assert records[-1]["sfen"] == board.sfen()


def test_load_file_名前情報がないKIFを渡すと_プレイヤー名はNoneになる(
    tmp_path, sample_kif_content_no_names
):
    # Arrange
    # shogi.KIF.Parser.parse_strはnames行がなくても常に[None, None]を返すため、
    # _extract_player_infoのデフォルト名（len(names)==0時）には到達しない
    file_path = tmp_path / "no_names.kif"
    file_path.write_text(sample_kif_content_no_names, encoding="utf-8")
    parser = KifParser(str(file_path))

    # Act
    records = parser.load_file()

    # Assert
    assert (records[0]["black_player"], records[0]["white_player"]) == (
        None,
        None,
    )


def test_load_file_不正な指し手が含まれると_その手より前で処理を打ち切る(
    mocker,
):
    # Arrange
    # 初手は合法（先手が飛車先を突く）、2手目は駒台にない歩を打つ不正な手
    fake_kif = {
        "names": ["先手太郎", "後手次郎"],
        "sfen": shogi.STARTING_SFEN,
        "moves": ["7g7f", "P*5e"],
        "win": None,
    }
    mocker.patch("shogi.KIF.Parser.parse_str", return_value=[fake_kif])
    parser = KifParser("dummy_path")

    # Act
    records = parser._parse_kif_content("dummy_content")

    # Assert
    assert len(records) == 2  # 初期局面 + 合法な1手のみ


def test_load_file_指し手のパースに失敗すると_その時点で処理を打ち切る(mocker):
    # Arrange
    fake_kif = {
        "names": ["先手太郎", "後手次郎"],
        "sfen": shogi.STARTING_SFEN,
        "moves": ["7g7f", "invalid_move"],
        "win": None,
    }
    mocker.patch("shogi.KIF.Parser.parse_str", return_value=[fake_kif])
    parser = KifParser("dummy_path")

    # Act
    records = parser._parse_kif_content("dummy_content")

    # Assert
    assert len(records) == 2  # 初期局面 + 合法な1手のみ


# ---------------------------------------------------------------------------
# kif_to_positions（モジュール関数、KifParserと同等の挙動を持つ）
# ---------------------------------------------------------------------------


def test_kif_to_positions_正常なKIF文字列を渡すと_初期局面を含む全レコードを返す(
    sample_kif_content,
):
    # Act
    records = kif_to_positions(sample_kif_content)

    # Assert
    assert len(records) == 4  # 初期局面 + 3手


def test_kif_to_positions_名前情報がないと_プレイヤー名はNoneになる(
    sample_kif_content_no_names,
):
    # Act
    records = kif_to_positions(sample_kif_content_no_names)

    # Assert
    assert (records[0]["black_player"], records[0]["white_player"]) == (
        None,
        None,
    )


def test_kif_to_positions_不正な指し手が含まれると_その手より前で処理を打ち切る(
    mocker,
):
    # Arrange
    fake_kif = {
        "names": ["先手太郎", "後手次郎"],
        "sfen": shogi.STARTING_SFEN,
        "moves": ["7g7f", "P*5e"],
        "win": None,
    }
    mocker.patch("shogi.KIF.Parser.parse_str", return_value=[fake_kif])

    # Act
    records = kif_to_positions("dummy_content")

    # Assert
    assert len(records) == 2  # 初期局面 + 合法な1手のみ
