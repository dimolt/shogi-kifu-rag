"""Configuration-related test helpers.

This module contains constants and table registry definitions used across
the test suite.
"""

from tests.helpers.config.constants import (
    TEST_CATALOG,
    TEST_GOLD_SCHEMA,
    TEST_SILVER_SCHEMA,
)
from tests.helpers.config.table_registry import (
    ALL_TABLES,
    GOLD_TABLES,
    SILVER_TABLES,
    fqn,
)

__all__ = [
    "TEST_CATALOG",
    "TEST_GOLD_SCHEMA",
    "TEST_SILVER_SCHEMA",
    "ALL_TABLES",
    "GOLD_TABLES",
    "SILVER_TABLES",
    "fqn",
]
