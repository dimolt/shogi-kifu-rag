"""テストシナリオ（small/medium/large/edge_cases）関連のfixture定義。

Job-based integration testで使用するテストデータの構成を提供する。
"""
from pathlib import Path
from typing import List

import pytest

from tests.helpers.databricks.volume_helpers import get_test_data_volume_path
from tests.helpers.models import TestDataScenarioConfig


@pytest.fixture(scope="session")
def test_data_config(catalog: str) -> dict[str, List[TestDataScenarioConfig]]:
    """Job-based integration testで使用するシナリオ別テストデータ設定を提供する。

    tests/scripts/setup_test_data_volume.py の定数（VOLUME_PATH, SAMPLE_KIF_PATH,
    LOCAL_CSV_PATH）を"small"シナリオとして集約しつつ、将来のシナリオ追加
    （medium/large/edge_cases）に備えた辞書構造とする。

    現時点で実データが用意されているのは"small"のみ。medium/large/edge_casesは
    対象のKIFファイルを用意した時点で追加する。

    Args:
        catalog: カタログ名（shogi_dev/shogi_test/shogi）。

    Returns:
        dict[str, List[TestDataScenarioConfig]]: シナリオ名 -> 設定のリスト。
    """
    project_root = Path(__file__).parent.parent.parent.parent
    return {
        "small": [TestDataScenarioConfig(
            kif_path=project_root / "data" / "kif_files" / "sample.kif",
            csv_path=project_root / "data" / "output" / "small.csv",
            volume_path=get_test_data_volume_path(catalog),
            expected_game_count=1,
            # data/kif_files/sample.kif の手数（121手、投了を除く）に基づく暫定値。
            expected_row_count=121,
        )],
        # TODO(#151): medium/large/edge_casesシナリオ用のKIFファイルを用意し次第追加する。
    }


@pytest.fixture(scope="function")
def test_scenario(test_data_config: dict[str, List[TestDataScenarioConfig]],
                  request: pytest.FixtureRequest) -> List[TestDataScenarioConfig]:
    """テストシナリオ設定を提供する。

    Args:
        test_data_config: test_data_configフィクスチャから提供される設定。
        request: pytestのrequestオブジェクト（パラメータ化テスト用）。

    Returns:
        List[TestDataScenarioConfig]: 選択されたシナリオの設定リスト。

    Usage:
        # デフォルト（small）を使用
        def test_something(test_scenario: List[TestDataScenarioConfig]):
            config = test_scenario[0]

        # パラメータ化テストで使用
        @pytest.mark.parametrize("test_scenario", ["small", "medium"], indirect=True)
        def test_with_scenario(test_scenario: List[TestDataScenarioConfig]):
            config = test_scenario[0]
    """
    # パラメータ化テストの場合はrequest.paramを使用
    if hasattr(request, "param") and request.param:
        scenario = request.param
    else:
        # デフォルトはsmallシナリオ
        scenario = "small"

    return test_data_config[scenario]
