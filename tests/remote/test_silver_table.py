"""Tests for Silver Table registration notebook"""

import pytest
from pyspark.sql.functions import col


def test_silver_table_schema(spark):
    """Test that Silver Table has the correct schema"""
    # Check if table exists
    table_exists = spark.catalog.tableExists("shogi.shogi_silver.positions")
    
    if not table_exists:
        pytest.skip("Silver Table does not exist")
    
    # Get table schema
    df = spark.table("shogi.shogi_silver.positions")
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
    ]
    
    column_names = [field.name for field in schema.fields]
    
    for col_name in required_columns:
        assert col_name in column_names, f"Column {col_name} not found in Silver Table"


def test_silver_table_data_types(spark):
    """Test that Silver Table has correct data types"""
    if not spark.catalog.tableExists("shogi.shogi_silver.positions"):
        pytest.skip("Silver Table does not exist")
    
    df = spark.table("shogi.shogi_silver.positions")
    schema = df.schema
    
    # Check data types
    type_mapping = {
        "game_id": "string",
        "move_number": "integer",
        "sfen": "string",
        "prev_sfen": "string",
        "move_usi": "string",
        "player": "string",
        "black_player": "string",
        "white_player": "string",
        "best_move": "string",
        "score_cp": "integer",
        "pv": "string",
    }
    
    for field in schema.fields:
        if field.name in type_mapping:
            expected_type = type_mapping[field.name]
            actual_type = field.dataType.simpleString()
            assert actual_type == expected_type, \
                f"Column {field.name} has type {actual_type}, expected {expected_type}"


def test_silver_table_not_empty(spark):
    """Test that Silver Table contains data"""
    if not spark.catalog.tableExists("shogi.shogi_silver.positions"):
        pytest.skip("Silver Table does not exist")
    
    df = spark.table("shogi.shogi_silver.positions")
    count = df.count()
    
    assert count > 0, "Silver Table is empty"


def test_silver_table_data_integrity(spark):
    """Test that Silver Table data is valid"""
    if not spark.catalog.tableExists("shogi.shogi_silver.positions"):
        pytest.skip("Silver Table does not exist")
    
    df = spark.table("shogi.shogi_silver.positions")
    
    # Check for null values in critical columns
    critical_columns = ["game_id", "move_number", "sfen", "move_usi"]
    
    for col_name in critical_columns:
        null_count = df.filter(col(col_name).isNull()).count()
        assert null_count == 0, f"Column {col_name} contains null values"
    
    # Check that move_number is non-negative
    negative_moves = df.filter(col("move_number") < 0).count()
    assert negative_moves == 0, "move_number contains negative values"
    
    # Check that player is either 'black' or 'white'
    invalid_players = df.filter(~col("player").isin(["black", "white"])).count()
    assert invalid_players == 0, "player column contains invalid values"
