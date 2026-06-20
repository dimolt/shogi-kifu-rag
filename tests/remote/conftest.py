"""Pytest configuration for Databricks Connect integration tests"""

import os

import pytest

# Databricks Connect configuration
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
DATABRICKS_CLUSTER_ID = os.getenv("DATABRICKS_CLUSTER_ID")


@pytest.fixture(scope="session")
def spark():
    """Create a Spark session using Databricks Connect"""
    if not all([DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_CLUSTER_ID]):
        pytest.skip("Databricks Connect credentials not set")

    try:
        from databricks.connect import DatabricksSession

        spark = DatabricksSession.builder.remote(
            host=DATABRICKS_HOST,
            token=DATABRICKS_TOKEN,
            cluster_id=DATABRICKS_CLUSTER_ID,
        ).getOrCreate()

        yield spark

        spark.stop()
    except ImportError:
        pytest.skip("databricks-connect not installed")
    except Exception as e:
        pytest.skip(f"Failed to connect to Databricks: {e}")


@pytest.fixture(scope="session")
def test_data(spark):
    """Create test data for integration tests"""
    # Create a test analysis.csv-like DataFrame
    test_data = [
        {
            "game_id": "test_game_1",
            "move_number": 0,
            "sfen": (
                "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/"
                "PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"
            ),
            "prev_sfen": (
                "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/"
                "PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"
            ),
            "move_usi": "7g7f",
            "player": "black",
            "black_player": "TestPlayer1",
            "white_player": "TestPlayer2",
            "best_move": "7g7f",
            "score_cp": 50,
            "pv": "7g7f 3c3d",
        },
        {
            "game_id": "test_game_1",
            "move_number": 1,
            "sfen": (
                "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/"
                "PPPPPPPPP/1B5R1/LNSGKGSNL w - 1"
            ),
            "prev_sfen": (
                "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/"
                "PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"
            ),
            "move_usi": "3c3d",
            "player": "white",
            "black_player": "TestPlayer1",
            "white_player": "TestPlayer2",
            "best_move": "3c3d",
            "score_cp": -30,
            "pv": "3c3d 7g7f",
        },
    ]

    from pyspark.sql.types import IntegerType, StringType, StructField, StructType

    schema = StructType([
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

    df = spark.createDataFrame(test_data, schema)

    # Register as a temporary view for testing
    df.createOrReplaceTempView("test_analysis")

    yield df

    # Cleanup
    spark.catalog.dropTempView("test_analysis")
