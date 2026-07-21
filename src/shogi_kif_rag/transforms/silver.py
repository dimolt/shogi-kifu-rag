"""Silver層のテーブル定義に関する純粋関数群。"""

from pyspark.sql import DataFrame, SparkSession

from shogi_kif_rag.kif.schemas.shemas import get_analysis_schema
from shogi_kif_rag.kif.utils import resolve_csv_paths


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
