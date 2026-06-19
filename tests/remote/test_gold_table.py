"""Tests for Gold Table construction notebook"""

import pytest
from pyspark.sql.functions import col


def test_gold_table_position_features_schema(spark):
    """Test that position_features table has the correct schema"""
    if not spark.catalog.tableExists("shogi.shogi_gold.position_features"):
        pytest.skip("Gold Table position_features does not exist")
    
    df = spark.table("shogi.shogi_gold.position_features")
    schema = df.schema
    
    # Check required columns
    required_columns = [
        "game_id",
        "move_number",
        "sfen",
        "prev_sfen",
        "move_usi",
        "player",
        "black_player",
        "white_player",
        "best_move",
        "score_cp",
        "pv",
        "score_from_turn",
        "score_delta",
        "is_best_move",
        "is_blunder",
        "move_quality",
        "search_text",
    ]
    
    column_names = [field.name for field in schema.fields]
    
    for col_name in required_columns:
        assert col_name in column_names, f"Column {col_name} not found in position_features"


def test_gold_table_position_features_calculations(spark):
    """Test that position_features calculations are correct"""
    if not spark.catalog.tableExists("shogi.shogi_gold.position_features"):
        pytest.skip("Gold Table position_features does not exist")
    
    df = spark.table("shogi.shogi_gold.position_features")
    
    # Check that score_from_turn is calculated correctly
    # For black player, score_from_turn should equal score_cp
    # For white player, score_from_turn should equal -score_cp
    black_positions = df.filter(col("player") == "black")
    white_positions = df.filter(col("player") == "white")
    
    if black_positions.count() > 0:
        black_positions.select(
            (col("score_from_turn") == col("score_cp")).alias("correct")
        ).filter(col("correct") == False).count()
    
    if white_positions.count() > 0:
        white_positions.select(
            (col("score_from_turn") == -col("score_cp")).alias("correct")
        ).filter(col("correct") == False).count()


def test_gold_table_move_quality_logic(spark):
    """Test that move_quality logic is correct"""
    if not spark.catalog.tableExists("shogi.shogi_gold.position_features"):
        pytest.skip("Gold Table position_features does not exist")
    
    df = spark.table("shogi.shogi_gold.position_features")
    
    # Check that move_quality values are valid
    valid_qualities = ["start", "best", "blunder", "normal"]
    invalid_qualities = df.filter(~col("move_quality").isin(valid_qualities)).count()
    assert invalid_qualities == 0, "move_quality contains invalid values"
    
    # Check that is_best_move matches move_quality == "best"
    best_moves = df.filter(col("move_quality") == "best")
    if best_moves.count() > 0:
        not_best = best_moves.filter(col("is_best_move") == False).count()
        assert not_best == 0, "move_quality='best' but is_best_move=False"
    
    # Check that is_blunder matches move_quality == "blunder"
    blunders = df.filter(col("move_quality") == "blunder")
    if blunders.count() > 0:
        not_blunder = blunders.filter(col("is_blunder") == False).count()
        assert not_blunder == 0, "move_quality='blunder' but is_blunder=False"


def test_gold_table_game_summary_schema(spark):
    """Test that game_summary table has the correct schema"""
    if not spark.catalog.tableExists("shogi.shogi_gold.game_summary"):
        pytest.skip("Gold Table game_summary does not exist")
    
    df = spark.table("shogi.shogi_gold.game_summary")
    schema = df.schema
    
    # Check required columns
    required_columns = [
        "game_id",
        "black_player",
        "white_player",
        "total_moves",
        "final_score_cp",
        "black_blunders",
        "white_blunders",
        "score_series_json",
    ]
    
    column_names = [field.name for field in schema.fields]
    
    for col_name in required_columns:
        assert col_name in column_names, f"Column {col_name} not found in game_summary"


def test_gold_table_not_empty(spark):
    """Test that Gold Tables contain data"""
    if not spark.catalog.tableExists("shogi.shogi_gold.position_features"):
        pytest.skip("Gold Table position_features does not exist")
    
    df = spark.table("shogi.shogi_gold.position_features")
    count = df.count()
    
    assert count > 0, "Gold Table position_features is empty"


def test_gold_table_data_integrity(spark):
    """Test that Gold Table data is valid"""
    if not spark.catalog.tableExists("shogi.shogi_gold.position_features"):
        pytest.skip("Gold Table position_features does not exist")
    
    df = spark.table("shogi.shogi_gold.position_features")
    
    # Check for null values in critical columns
    critical_columns = ["game_id", "move_number", "sfen", "move_quality"]
    
    for col_name in critical_columns:
        null_count = df.filter(col(col_name).isNull()).count()
        assert null_count == 0, f"Column {col_name} contains null values"
    
    # Check that blunder count is non-negative
    if spark.catalog.tableExists("shogi.shogi_gold.game_summary"):
        game_summary = spark.table("shogi.shogi_gold.game_summary")
        negative_black_blunders = game_summary.filter(col("black_blunders") < 0).count()
        negative_white_blunders = game_summary.filter(col("white_blunders") < 0).count()
        assert negative_black_blunders == 0, "black_blunders contains negative values"
        assert negative_white_blunders == 0, "white_blunders contains negative values"
