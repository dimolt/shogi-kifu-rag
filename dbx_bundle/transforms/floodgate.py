"""Bronze層のfloodgate_rawからSilver層のfloodgate_positionsへ変換する純粋関数群。"""

from collections.abc import Iterator

import pandas as pd
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F  #noqa: N812
from pyspark.sql.functions import concat, lit
from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructField,
    StructType,
)
from pyspark.sql.window import Window

FLOODGATE_POSITIONS_SCHEMA = StructType([
    StructField("game_id", StringType(), True),
    StructField("move_number", IntegerType(), True),
    StructField("sfen", StringType(), True),
    StructField("move_usi", StringType(), True),
    StructField("player", StringType(), True),
    StructField("black_player", StringType(), True),
    StructField("white_player", StringType(), True),
])

# NOTE: SFENは初期局面固定。move_usiを盤面に適用しないためチェーンが繋がっていない
# （既知の既存バグ・別Issue管理）。旧 floodgate.py の挙動をそのまま踏襲する。
_INITIAL_SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"


def parse_csa(csa_text: str) -> dict:
    """CSA形式の棋譜をパースする。

    Args:
        csa_text: CSA形式の棋譜テキスト。

    Returns:
        指し手リストと対局者名を持つ辞書。
    """
    lines = csa_text.split("\n")
    moves: list[dict] = []
    current_player = "black"
    black_player = ""
    white_player = ""

    for line in lines:
        if line.startswith("'"):
            continue
        elif line.startswith("N+"):
            black_player = line[2:]
        elif line.startswith("N-"):
            white_player = line[2:]
        elif line.startswith("+") or line.startswith("-"):
            if len(line) > 1:
                moves.append({"move_usi": line[1:], "player": current_player})
                current_player = "white" if current_player == "black" else "black"

    return {"moves": moves, "black_player": black_player, "white_player": white_player}


def _analyze_game(game_id: str, csa_text: str) -> list[dict]:
    """1局分のCSAをパースして局面レコードのリストを生成する。

    Args:
        game_id: 対局ID。
        csa_text: CSA形式の棋譜テキスト。

    Returns:
        局面レコードのリスト。
    """
    parsed = parse_csa(csa_text)
    black_player = parsed["black_player"]
    white_player = parsed["white_player"]

    positions = []
    for i, move in enumerate(parsed["moves"]):
        positions.append({
            "game_id": game_id,
            "move_number": i,
            "sfen": _INITIAL_SFEN,
            "move_usi": move["move_usi"],
            "player": move["player"],
            "black_player": black_player,
            "white_player": white_player,
        })
    return positions


def _build_positions(pdf_iter: Iterator[pd.DataFrame]) -> Iterator[pd.DataFrame]:
    for pdf in pdf_iter:
        rows = []

        for _, row in pdf.iterrows():
            rows.extend(_analyze_game(row.game_id, row.csa))

        yield pd.DataFrame(rows)


def build_floodgate_positions(spark: SparkSession, bronze_df: DataFrame) -> DataFrame:
    """Bronzeテーブル(floodgate_raw)からSilverテーブル(floodgate_positions)を生成する。
    game_id単位でfetched_atが最新のレコードのみを抽出する。

    Args:
        spark: DataFrame生成に使用するSparkSession。
        bronze_df: Bronzeテーブルのfloodgate_rawデータ
            （game_id, csa, fetched_at列を使用）

    Returns:
        局面ごとのレコードを持つSilver DataFrame。
    """
    window = Window.partitionBy("game_id").orderBy(F.col("fetched_at").desc())

    dedup_df = (
        bronze_df
        .withColumn("rn", F.row_number().over(window))
        .filter(F.col("rn") == 1)
    )

    return dedup_df.select(
        "game_id",
        "csa",
    ).mapInPandas(
        _build_positions,
        schema=FLOODGATE_POSITIONS_SCHEMA,
    )


def build_floodgate_features(silver_df: DataFrame) -> DataFrame:
    """Silverテーブルから局面特徴量（Gold: floodgate_position_features）を生成する。

    Silverの列をそのまま横流しし、search_text列のみ追加する「薄いGold」とする。
    search_textの書式は既存の_rebuild_floodgateが使っている書式を踏襲する。

    Args:
        silver_df: Silverテーブルのfloodgate_positionsデータ。

    Returns:
        局面ごとの特徴量列を持つGold DataFrame。
    """
    featured_df = silver_df.withColumn(
        "search_text",
        concat(
            lit("局面: "),
            F.col("sfen"),
            lit(" 指し手: "),
            F.col("move_usi"),
        ),
    )

    return featured_df.select(
        "game_id",
        "move_number",
        "sfen",
        "move_usi",
        "player",
        "black_player",
        "white_player",
        "search_text",
    )
