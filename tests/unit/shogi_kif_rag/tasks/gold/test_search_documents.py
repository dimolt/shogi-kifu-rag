"""tasks/gold/search_documents_delta.py のユニットテスト。"""

from unittest.mock import patch

import pytest

from shogi_kif_rag.tasks.gold.search_documents import main


def test_main_requires_catalog_and_gold_schema() -> None:
    """main関数はcatalogとgold_schema引数を必要とする"""
    with patch("sys.argv", ["search_documents.py"]):
        with patch("shogi_kif_rag.tasks.gold.search_documents.SparkSession") as mock_spark:
            mock_spark.getActiveSession.return_value = None

            with pytest.raises(SystemExit):
                main()
