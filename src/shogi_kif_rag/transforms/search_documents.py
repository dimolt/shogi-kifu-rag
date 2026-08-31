"""Goldテーブル群からSearch Documents Tableへの変換に関する純粋関数群。"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, concat, lit, struct, to_json


def build_search_documents(
    positions_df: DataFrame,
    floodgate_df: DataFrame,
    joseki_df: DataFrame,
) -> DataFrame:
    """3種のGold DataFrameを共通スキーマに正規化・UNIONして
    Search Documents用DataFrameを生成する。

    Args:
        positions_df: Goldテーブルのposition_featuresデータ。
        floodgate_df: Goldテーブルのfloodgate_position_featuresデータ。
        joseki_df: Goldテーブルのjoseki_featuresデータ。

    Returns:
        id, text, metadata, source_type列を持つ統合DataFrame。
    """
    # position_featuresの正規化
    position_docs = _normalize_positions(positions_df)

    # floodgate_position_featuresの正規化
    floodgate_docs = _normalize_floodgate(floodgate_df)

    # joseki_featuresの正規化
    joseki_docs = _normalize_joseki(joseki_df)

    # 3つのDataFrameをUNION
    return position_docs.union(floodgate_docs).union(joseki_docs)


def _normalize_positions(df: DataFrame) -> DataFrame:
    """position_featuresをSearch Documents共通スキーマに正規化する。

    Args:
        df: position_featuresのDataFrame。

    Returns:
        id, text, metadata, source_type列を持つDataFrame。
    """
    # idの生成: position:{game_id}:{move_number}
    docs_df = df.withColumn(
        "id",
        concat(lit("position:"), col("game_id"), lit(":"),
               col("move_number").cast("string")),
    )
    docs_df = docs_df.withColumn("text", col("search_text"))
    docs_df = docs_df.withColumn("source_type", lit("position"))
    docs_df = docs_df.withColumn(
        "metadata",
        to_json(
            struct(
                col("game_id"),
                col("move_number"),
                col("sfen"),
                col("move_usi"),
                col("player"),
                col("black_player"),
                col("white_player"),
                col("best_move"),
                col("score_cp"),
                col("move_quality"),
            )
        ),
    )

    return docs_df.select("id", "text", "metadata", "source_type")


def _normalize_floodgate(df: DataFrame) -> DataFrame:
    """floodgate_position_featuresをSearch Documents共通スキーマに正規化する。

    Args:
        df: floodgate_position_featuresのDataFrame。

    Returns:
        id, text, metadata, source_type列を持つDataFrame。
    """
    # idの生成: floodgate:{game_id}:{move_number}
    docs_df = df.withColumn(
        "id",
        concat(lit("floodgate:"), col("game_id"), lit(":"),
               col("move_number").cast("string")),
    )
    docs_df = docs_df.withColumn("text", col("search_text"))
    docs_df = docs_df.withColumn("source_type", lit("floodgate"))
    docs_df = docs_df.withColumn(
        "metadata",
        to_json(
            struct(
                col("game_id"),
                col("move_number"),
                col("sfen"),
                col("move_usi"),
                col("player"),
                col("black_player"),
                col("white_player"),
            )
        ),
    )

    return docs_df.select("id", "text", "metadata", "source_type")


def _normalize_joseki(df: DataFrame) -> DataFrame:
    """joseki_featuresをSearch Documents共通スキーマに正規化する。

    Args:
        df: joseki_featuresのDataFrame。

    Returns:
        id, text, metadata, source_type列を持つDataFrame。
    """
    # idの生成: joseki:{strategy}
    docs_df = df.withColumn("id", concat(lit("joseki:"), col("strategy")))
    docs_df = docs_df.withColumn("text", col("search_text"))
    docs_df = docs_df.withColumn("source_type", lit("joseki"))
    docs_df = docs_df.withColumn(
        "metadata",
        to_json(
            struct(
                col("strategy"),
                col("content"),
                col("source"),
            )
        ),
    )

    return docs_df.select("id", "text", "metadata", "source_type")
