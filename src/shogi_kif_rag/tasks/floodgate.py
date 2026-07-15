import argparse
import re
from datetime import datetime, timedelta

import requests
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    IntegerType,
    StringType,
)

FLOODGATE_BASE = "https://wdoor.c.u-tokyo.ac.jp/shogi/x"
MAX_GAMES_PER_DAY = 10


# Floodgate APIから棋譜を取得
def fetch_floodgate_games(days_back: int = 7) -> list:
    """Floodgateから指定日数分の棋譜を取得する
    Args:
        days_back: 取得する日数
    Returns:
        棋譜リスト（各要素は {"id": 対局ID, "csa": CSAテキスト} の辞書）
    """
    games = []

    for i in range(days_back):
        date = datetime.now() - timedelta(days=i)
        day_url = f"{FLOODGATE_BASE}/{date.year}/{date.month:02d}/{date.day:02d}/"

        try:
            day_response = requests.get(day_url, timeout=10)
        except requests.RequestException:
            continue
        if day_response.status_code != 200:
            continue

        filenames = re.findall(r'(wdoor\+floodgate[^\s"]+\.csa)', day_response.text)
        urls = [f"{day_url}{fname}" for fname in filenames][:MAX_GAMES_PER_DAY]

        for url in urls:
            try:
                game_response = requests.get(url, timeout=15)
            except requests.RequestException:
                continue
            if game_response.status_code != 200:
                continue
            game_id = url.split("/")[-1].rsplit(".", 1)[0]
            games.append({"id": game_id, "csa": game_response.text})

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
    black_player = ""
    white_player = ""

    for line in lines:
        if line.startswith("'"):
            # コメント行は無視
            continue
        elif line.startswith("N+"):
            black_player = line[2:]
        elif line.startswith("N-"):
            white_player = line[2:]
        elif line.startswith("+") or line.startswith("-"):
            if len(line) > 1:
                move = line[1:]
                moves.append({
                    "move_usi": move,
                    "player": current_player,
                })
                current_player = "white" if current_player == "black" else "black"
    return {
        "moves": moves,
        "black_player": black_player,
        "white_player": white_player,
    }


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
    black_player = parsed.get("black_player", "")
    white_player = parsed.get("white_player", "")

    positions = []
    sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"  # 初期局面

    for i, move in enumerate(moves):
        positions.append({
            "game_id": game.get("id", ""),
            "move_number": i,
            "sfen": sfen,
            "move_usi": move["move_usi"],
            "player": move["player"],
            "black_player": black_player,
            "white_player": white_player,
        })
    # SFENの更新（簡易実装）
    # 実際にはUSIからSFENへの変換ライブラリを使用

    return positions


def main():
    spark = SparkSession.getActiveSession()

    # Floodgate棋譜の取得
    games = fetch_floodgate_games(days_back=7)

    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--silver_schema", required=True)
    args = parser.parse_args()

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
    df.write \
      .format("delta") \
      .mode("overwrite") \
      .saveAsTable(f"{args.catalog}.{args.silver_schema}.floodgate_positions")
