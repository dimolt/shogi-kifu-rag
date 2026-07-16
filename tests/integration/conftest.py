"""pytest統合テスト用フィクスチャ定義（Layer 2）のエントリーポイント。

spark, pipeline_id のフィクスチャは tests/conftest.py（ルート）に集約されている。
FQN（catalog.schema.table）はfixtureではなく tests/table_registry.py の fqn() 関数として
提供している（setup/teardownやscopeによるキャッシュを必要としないため）。
本ファイルはintegration層固有のフィクスチャを integration_fixtures/ 配下の各モジュールから
再エクスポートするだけの薄いエントリーポイントとする。
実装本体は関心事ごとに以下へ分割している。

- integration/fixtures/scenarios.py    : テストシナリオ（small/medium/...）関連
- integration/fixtures/job_execution.py: Databricks Job実行・監視関連
- integration/fixtures/tables.py       : Silver/Gold テーブルDataFrame関連
                                          （tests/table_registry.py の一覧から自動生成）

"""
from tests.helpers.databricks.spark_fixture import spark  # noqa: F401
from tests.integration.fixtures.job_execution import (  # noqa: F401,E501
    job_id,
    job_run_result,
    workspace_client,
)
from tests.integration.fixtures.scenarios import (  # noqa: F401
    test_data_config,
    test_scenario,
)
