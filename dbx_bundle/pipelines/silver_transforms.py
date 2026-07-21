"""Silver層のテーブル定義に関する純粋関数群。"""

from pathlib import Path

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


def resolve_csv_paths(csv_path: str) -> str | list[str]:
    """CSVパスを解決する。

    ワイルドカードが含まれる場合は一致したファイル一覧を返し、
    含まれない場合はそのまま返す。ディレクトリパスの場合もそのまま返す。

    Args:
        csv_path: CSVファイルパス（単一ファイル、ディレクトリ、
                  ワイルドカードパターンをサポート）。

    Returns:
        ワイルドカード展開後のファイルパス（単一文字列または文字列リスト）。

    Raises:
        FileNotFoundError: ワイルドカードパターンに一致するファイルが存在しない場合。
    """
    # ワイルドカードが含まれない場合はそのまま返す
    if not any(char in csv_path for char in "*?[]"):
        return csv_path

    path = Path(csv_path)
    paths = sorted(
        str(p)
        for p in path.parent.glob(path.name)
        if p.is_file()
    )

    if not paths:
        raise FileNotFoundError(f"No files matched: {csv_path}")

    return paths


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
    paths = resolve_csv_paths(csv_path)
    df = spark.read.csv(paths, header=True, schema=get_analysis_schema())
    return df.dropDuplicates(["game_id", "move_number"])
