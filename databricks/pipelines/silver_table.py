"""Silver Table: analysis.csvから棋譜局面を登録するLakeflowパイプライン定義。"""

from pyspark import pipelines as dp
from silver_transforms import build_positions

CSV_PATH = "/Volumes/shogi/landing/kif/analysis.csv"


@dp.table
def positions():
    """Silver Table: analysis.csvから棋譜局面を登録"""
    return build_positions(spark, CSV_PATH)
