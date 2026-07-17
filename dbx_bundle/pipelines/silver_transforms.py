"""Silver層のテーブル定義に関する純粋関数群。"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    IntegerType,
    StringType,
    StructField,
    StructType,
)


def get_analysis_schema():
    """AnalysisRowに対応するSpark StructTypeを返す。

    Returns:
        analysis.csvのカラム定義に対応したStructType。
    """
    return StructType([
        StructField("game_id", StringType(), True),
        StructField("move_number", IntegerType(), True),
        StructField("sfen", StringType(), True),
        StructField("prev_sfen", StringType(), True),
        StructField("move_usi", StringType(), True),
        StructField("player", StringType(), True),
        StructField("black_player", StringType(), True),
        StructField("white_player", StringType(), True),
        StructField("best_move", StringType(), True),
        StructField("score_cp", IntegerType(), True),
        StructField("pv", StringType(), True),
    ])


def build_positions(spark: SparkSession, csv_path: str) -> DataFrame:
    """analysis.csvを読み込み、Silverテーブル用DataFrameを生成する。

    Args:
        spark: 読み込みに使用するSparkSession。
        csv_path: 読み込み対象のCSVファイルパス（単一ファイル、ディレクトリ、
                  ワイルドカードパターンをサポート）。

    Returns:
        get_analysis_schema()に基づいて型付けされたDataFrame。
        game_idとmove_numberの組み合わせで重複排除を行う。
    """
    df = spark.read.csv(csv_path, header=True, schema=get_analysis_schema())
    return df.dropDuplicates(["game_id", "move_number"])
