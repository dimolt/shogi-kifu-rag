"""pytest統合テスト用フィクスチャ定義のエントリーポイント。

spark, pipeline_id のフィクスチャは tests/conftest.py（ルート）に集約されている。
FQN（catalog.schema.table）はfixtureではなく tests/table_registry.py の fqn() 関数として
提供している（setup/teardownやscopeによるキャッシュを必要としないため）。
本ファイルはintegration層固有のフィクスチャを integration_fixtures/ 配下の各モジュールから
再エクスポートするだけの薄いエントリーポイントとする。
実装本体は関心事ごとに以下へ分割している。

- integration/fixtures/scenarios.py    : テストシナリオ（small/medium/...）関連
- integration/fixtures/tables.py       : Silver/Gold テーブルDataFrame関連
                                          （tests/table_registry.py の一覧から自動生成）
- integration/fixtures/test_data.py    : テストデータ管理（原本→Volumeコピー、クリーンアップ）
- integration/fixtures/job_execution.py: Job実行・監視まわりのfixture定義
- integration/fixtures/config_validation.py: Bundle validation関連のfixture定義

テスト構成:
    正常系テスト: test_normal_*.py (pytest.mark.integration)
    異常系テスト: test_abnormal_*.py (pytest.mark.integration, pytest.mark.abnormal)
"""
import os

# integration層は常にshogi_devを使用
os.environ["TEST_CATALOG"] = "shogi_dev"

from tests.fixtures.tables import *  # noqa: F403
from tests.helpers.databricks.spark_fixture import spark  # noqa: F401
from tests.integration.fixtures.config_validation import (  # noqa: F401
    run_bundle_validate_json,
)
from tests.integration.fixtures.job_execution import (  # noqa: F401
    floodgate_job_id,
    floodgate_job_run_result,
    job_id,
    job_run_result,
    joseki_job_id,
    joseki_job_run_result,
    workspace_client,
)
from tests.integration.fixtures.scenarios import (  # noqa: F401
    test_data_config,
    test_scenario,
)
from tests.integration.fixtures.test_data import (  # noqa: F401
    abnormal_test_data,
    clean_volume,
    normal_test_data,
    volume_setup,
)
