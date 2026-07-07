"""gold_transforms.pyのユニットテスト。"""

import json

from databricks_bundle.pipelines.gold_transforms import (
    _add_turn_score_columns,
    build_game_summary,
    build_position_features,
)

# --- _add_turn_score_columns -------------------------------------------------


def test_add_turn_score_columns_先手の手は_score_cpをそのまま返す(make_positions_df) -> None:
    # Arrange
    df = make_positions_df(
        [("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 100, "")]
    )

    # Act
    result_df = _add_turn_score_columns(df)

    # Assert
    assert result_df.first()["score_from_turn"] == 100


def test_add_turn_score_columns_後手の手は_符号反転した値を返す(make_positions_df) -> None:
    # Arrange
    df = make_positions_df(
        [("G1", 0, "sfen0", None, "3c3d", "white", "Alice", "Bob", "3c3d", 100, "")]
    )

    # Act
    result_df = _add_turn_score_columns(df)

    # Assert
    assert result_df.first()["score_from_turn"] == -100


def test_add_turn_score_columns_先頭手move_number0は_score_deltaがnullになる(
    make_positions_df,
) -> None:
    # Arrange
    df = make_positions_df(
        [("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 50, "")]
    )

    # Act
    result_df = _add_turn_score_columns(df)

    # Assert
    assert result_df.first()["score_delta"] is None


def test_add_turn_score_columns_2手目以降は_前手番との差分を返す(make_positions_df) -> None:
    # Arrange
    df = make_positions_df(
        [
            ("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 50, ""),
            ("G1", 1, "sfen1", "sfen0", "3c3d", "white", "Alice", "Bob", "3c3d", 30, ""),
        ]
    )

    # Act
    result_df = _add_turn_score_columns(df)

    # Assert
    # move1: score_from_turn = -30, move0: score_from_turn = 50 → delta = -30 - 50 = -80
    row = result_df.filter("move_number = 1").first()
    assert row["score_delta"] == -80


def test_add_turn_score_columns_異なるgame_id間では_score_deltaが引き継がれない(
    make_positions_df,
) -> None:
    # Arrange
    df = make_positions_df(
        [
            ("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 100, ""),
            ("G1", 1, "sfen1", "sfen0", "3c3d", "white", "Alice", "Bob", "3c3d", 80, ""),
            ("G2", 0, "sfen0", None, "2g2f", "black", "Carol", "Dave", "2g2f", 10, ""),
        ]
    )

    # Act
    result_df = _add_turn_score_columns(df)

    # Assert
    row = result_df.filter("game_id = 'G2' and move_number = 0").first()
    assert row["score_delta"] is None


def test_add_turn_score_columns_score_delta絶対値が境界値200のとき_is_blunderがTrueを返す(
    make_positions_df,
) -> None:
    # Arrange
    df = make_positions_df(
        [
            ("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 0, ""),
            ("G1", 1, "sfen1", "sfen0", "3c3d", "white", "Alice", "Bob", "3c3d", -200, ""),
        ]
    )

    # Act
    result_df = _add_turn_score_columns(df)

    # Assert
    # move1: score_from_turn = 200, move0: score_from_turn = 0 → |delta| = 200
    row = result_df.filter("move_number = 1").first()
    assert row["is_blunder"] is True


def test_add_turn_score_columns_score_delta絶対値が199のとき_is_blunderがFalseを返す(
    make_positions_df,
) -> None:
    # Arrange
    df = make_positions_df(
        [
            ("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 0, ""),
            ("G1", 1, "sfen1", "sfen0", "3c3d", "white", "Alice", "Bob", "3c3d", -199, ""),
        ]
    )

    # Act
    result_df = _add_turn_score_columns(df)

    # Assert
    row = result_df.filter("move_number = 1").first()
    assert row["is_blunder"] is False


def test_add_turn_score_columns_score_deltaがnullのとき_is_blunderもnullになる(
    make_positions_df,
) -> None:
    # Arrange
    df = make_positions_df(
        [("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 50, "")]
    )

    # Act
    result_df = _add_turn_score_columns(df)

    # Assert
    assert result_df.first()["is_blunder"] is None


# --- build_position_features --------------------------------------------------


def test_build_position_features_move_usiとbest_moveが一致すると_is_best_moveがTrueを返す(
    make_positions_df,
) -> None:
    # Arrange
    df = make_positions_df(
        [("G1", 1, "sfen1", "sfen0", "7g7f", "black", "Alice", "Bob", "7g7f", 50, "")]
    )

    # Act
    result_df = build_position_features(df)

    # Assert
    assert result_df.first()["is_best_move"] is True


def test_build_position_features_move_usiとbest_moveが不一致だと_is_best_moveがFalseを返す(
    make_positions_df,
) -> None:
    # Arrange
    df = make_positions_df(
        [("G1", 1, "sfen1", "sfen0", "7g7f", "black", "Alice", "Bob", "2g2f", 50, "")]
    )

    # Act
    result_df = build_position_features(df)

    # Assert
    assert result_df.first()["is_best_move"] is False


def test_build_position_features_move_number0のとき_他条件に関わらずmove_qualityがstartになる(
    make_positions_df,
) -> None:
    # Arrange: is_best_move=True になる条件を敢えて満たしても start が優先されるか確認
    df = make_positions_df(
        [("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 50, "")]
    )

    # Act
    result_df = build_position_features(df)

    # Assert
    assert result_df.first()["move_quality"] == "start"


def test_build_position_features_is_best_moveがTrueのとき_move_qualityがbestになる(
    make_positions_df,
) -> None:
    # Arrange
    df = make_positions_df(
        [("G1", 1, "sfen1", "sfen0", "7g7f", "black", "Alice", "Bob", "7g7f", 50, "")]
    )

    # Act
    result_df = build_position_features(df)

    # Assert
    assert result_df.first()["move_quality"] == "best"


def test_build_position_features_best_moveでなくblunderのとき_move_qualityがblunderになる(
    make_positions_df,
) -> None:
    # Arrange
    df = make_positions_df(
        [
            ("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 0, ""),
            ("G1", 1, "sfen1", "sfen0", "3c3d", "white", "Alice", "Bob", "2g2f", -300, ""),
        ]
    )

    # Act
    result_df = build_position_features(df)

    # Assert
    row = result_df.filter("move_number = 1").first()
    assert row["move_quality"] == "blunder"


def test_build_position_features_best_moveかつblunderのとき_move_qualityはbestが優先される(
    make_positions_df,
) -> None:
    # Arrange: is_best_move=True と is_blunder=True を同時に満たす行
    df = make_positions_df(
        [
            ("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 0, ""),
            ("G1", 1, "sfen1", "sfen0", "3c3d", "white", "Alice", "Bob", "3c3d", -300, ""),
        ]
    )

    # Act
    result_df = build_position_features(df)

    # Assert
    row = result_df.filter("move_number = 1").first()
    assert row["move_quality"] == "best"


def test_build_position_features_いずれの条件も満たさないとき_move_qualityがnormalになる(
    make_positions_df,
) -> None:
    # Arrange
    df = make_positions_df(
        [
            ("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 0, ""),
            ("G1", 1, "sfen1", "sfen0", "3c3d", "white", "Alice", "Bob", "2g2f", -50, ""),
        ]
    )

    # Act
    result_df = build_position_features(df)

    # Assert
    row = result_df.filter("move_number = 1").first()
    assert row["move_quality"] == "normal"


def test_build_position_features_search_textにsfenと指し手と評価値が含まれる(
    make_positions_df,
) -> None:
    # Arrange
    df = make_positions_df(
        [("G1", 1, "sfen1", "sfen0", "7g7f", "black", "Alice", "Bob", "2g2f", 123, "")]
    )

    # Act
    search_text = build_position_features(df).first()["search_text"]

    # Assert
    assert "sfen1" in search_text
    assert "7g7f" in search_text
    assert "2g2f" in search_text
    assert "123" in search_text


def test_build_position_features_出力列が仕様通りの17列になる(make_positions_df) -> None:
    # Arrange
    df = make_positions_df(
        [("G1", 1, "sfen1", "sfen0", "7g7f", "black", "Alice", "Bob", "7g7f", 50, "")]
    )
    expected_columns = {
        "game_id", "move_number", "sfen", "prev_sfen", "move_usi", "player",
        "black_player", "white_player", "best_move", "score_cp", "pv",
        "score_from_turn", "score_delta", "is_best_move", "is_blunder",
        "move_quality", "search_text",
    }

    # Act
    result_df = build_position_features(df)

    # Assert
    assert set(result_df.columns) == expected_columns


# --- build_game_summary --------------------------------------------------


def test_build_game_summary_final_score_cpは最終手のscore_cpを返す(make_positions_df) -> None:
    # Arrange: move_numberの昇順ではない順で投入し、順序非依存であることを確認
    df = make_positions_df(
        [
            ("G1", 2, "sfen2", "sfen1", "5i5h", "black", "Alice", "Bob", "5i5h", 40, ""),
            ("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 50, ""),
            ("G1", 1, "sfen1", "sfen0", "3c3d", "white", "Alice", "Bob", "3c3d", 30, ""),
        ]
    )

    # Act
    result_df = build_game_summary(df)

    # Assert
    assert result_df.first()["final_score_cp"] == 40


def test_build_game_summary_total_movesはgame内の最大move_numberを返す(make_positions_df) -> None:
    # Arrange
    df = make_positions_df(
        [
            ("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 50, ""),
            ("G1", 1, "sfen1", "sfen0", "3c3d", "white", "Alice", "Bob", "3c3d", 30, ""),
            ("G1", 2, "sfen2", "sfen1", "5i5h", "black", "Alice", "Bob", "5i5h", 40, ""),
        ]
    )

    # Act
    result_df = build_game_summary(df)

    # Assert
    assert result_df.first()["total_moves"] == 2


def test_build_game_summary_black_blundersとwhite_blundersはplayer別に正しく集計される(
    make_positions_df,
) -> None:
    # Arrange: 黒番1回・白番1回のblunderを発生させる
    df = make_positions_df(
        [
            ("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 0, ""),
            ("G1", 1, "sfen1", "sfen0", "3c3d", "white", "Alice", "Bob", "2g2f", -300, ""),
            ("G1", 2, "sfen2", "sfen1", "5i5h", "black", "Alice", "Bob", "2g2f", 100, ""),
        ]
    )

    # Act
    row = build_game_summary(df).first()

    # Assert
    assert row["black_blunders"] == 1
    assert row["white_blunders"] == 1


def test_build_game_summary_score_series_jsonはmove_number昇順でソートされる(
    make_positions_df,
) -> None:
    # Arrange: move_numberの昇順ではない順で投入
    df = make_positions_df(
        [
            ("G1", 2, "sfen2", "sfen1", "5i5h", "black", "Alice", "Bob", "5i5h", 40, ""),
            ("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 50, ""),
            ("G1", 1, "sfen1", "sfen0", "3c3d", "white", "Alice", "Bob", "3c3d", 30, ""),
        ]
    )

    # Act
    score_series_json = build_game_summary(df).first()["score_series_json"]
    move_numbers = [entry["move_number"] for entry in json.loads(score_series_json)]

    # Assert
    assert move_numbers == [0, 1, 2]


def test_build_game_summary_複数game_idが存在するとき_game_idごとに独立して集計される(
    make_positions_df,
) -> None:
    # Arrange
    df = make_positions_df(
        [
            ("G1", 0, "sfen0", None, "7g7f", "black", "Alice", "Bob", "7g7f", 100, ""),
            ("G2", 0, "sfen0", None, "2g2f", "black", "Carol", "Dave", "2g2f", 10, ""),
        ]
    )

    # Act
    result_df = build_game_summary(df)

    # Assert
    assert result_df.count() == 2
    assert set(row["game_id"] for row in result_df.collect()) == {"G1", "G2"}
