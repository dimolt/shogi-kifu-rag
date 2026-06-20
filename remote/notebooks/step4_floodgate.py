"""Floodgate Acquisition

Floodgate棋譜を取得して解析するノートブック
"""

from datetime import datetime, timedelta

import requests
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    IntegerType,
    StringType,
)

# SparkSessionの初期化
spark = SparkSession.builder.getOrCreate()

# Floodgate APIから棋譜を取得
def fetch_floodgate_games(days_back: int = 7) -> list:
    """Floodgateから指定日数分の棋譜を取得する

    Args:
        days_back: 取得する日数

    Returns:
        棋譜リスト
    """
    base_url = "https://shogi-forest.appspot.com/api/floodgate"
    games = []

    for i in range(days_back):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        url = f"{base_url}/{date}"
        response = requests.get(url)
        if response.status_code == 200:
            games.extend(response.json())

    return games

# CSAパーサーの実装
def parse_csa(csa_text: str) -> dict:
    """CSA形式の棋譜をパースする

    Args:
        csa_text: CSA形式の棋譜テキスト

    Returns:
        パース結果（辞書形式）
    """
    lines = csa_text.split("\n")
    moves = []
    current_player = "black"

    for line in lines:
        if line.startswith("'"):
            # コメント行
            continue
        elif line.startswith("+") or line.startswith("-"):
            # 手
            if len(line) > 1:
                move = line[1:]
                moves.append({
                    "move_usi": move,
                    "player": current_player,
                })
                current_player = "white" if current_player == "black" else "black"

    return {"moves": moves}

# 棋譜の解析と特徴量計算
def analyze_game(game: dict) -> list:
    """棋譜を解析して特徴量を計算する

    Args:
        game: 棋譜データ

    Returns:
        局面リスト
    """
    csa_text = game.get("csa", "")
    parsed = parse_csa(csa_text)
    moves = parsed["moves"]

    positions = []
    sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"  # 初期局面

    for i, move in enumerate(moves):
        positions.append({
            "game_id": game.get("id", ""),
            "move_number": i,
            "sfen": sfen,
            "move_usi": move["move_usi"],
            "player": move["player"],
            "black_player": game.get("black_player", ""),
            "white_player": game.get("white_player", ""),
        })
        # SFENの更新（簡易実装）
        # 実際にはUSIからSFENへの変換ライブラリを使用

    return positions

# Floodgate棋譜の取得
games = fetch_floodgate_games(days_back=7)

# 棋譜の解析
all_positions = []
for game in games:
    positions = analyze_game(game)
    all_positions.extend(positions)

# DataFrameの作成
from pyspark.sql.types import StructField, StructType  # noqa: E402

schema = StructType([
    StructField("game_id", StringType(), True),
    StructField("move_number", IntegerType(), True),
    StructField("sfen", StringType(), True),
    StructField("move_usi", StringType(), True),
    StructField("player", StringType(), True),
    StructField("black_player", StringType(), True),
    StructField("white_player", StringType(), True),
])

df = spark.createDataFrame(all_positions, schema=schema)

# floodgate_positionsテーブルへの書き込み
df.write.format("delta").mode("append").saveAsTable("shogi.shogi_silver.floodgate_positions")
