"""pytest統合テスト用フィクスチャ定義（Layer 2）。

spark, pipeline_id, FQN系のフィクスチャは `tests/conftest.py`（ルート）に
集約されているため、ここではintegration層固有のDataFrame系フィクスチャのみ定義する。
"""
import sys
from pathlib import Path
from typing import List

import pytest
from databricks.connect import DatabricksSession
from databricks.sdk import WorkspaceClient
from helpers.job_monitoring import JobMonitor
from helpers.models import JobRunResult, TestDataScenarioConfig
from pyspark.sql import DataFrame, SparkSession

# databricksモジュールをインポート可能にするためPythonパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def test_data_config() -> dict[str, List[TestDataScenarioConfig]]:
    """Job-based integration testで使用するシナリオ別テストデータ設定を提供する。

    `tests/scripts/setup_test_data_volume.py` の定数（VOLUME_PATH, SAMPLE_KIF_PATH,
    LOCAL_CSV_PATH）を"small"シナリオとして集約しつつ、将来のシナリオ追加
    （medium/large/edge_cases）に備えた辞書構造とする。

    現時点で実データが用意されているのは"small"のみ。medium/large/edge_casesは
    対象のKIFファイルを用意した時点で追加する。

    Returns:
        dict[str, TestDataScenarioConfig]: シナリオ名 -> 設定。
    """
    return {
        "small": [TestDataScenarioConfig(
            kif_path=project_root / "data" / "kif_files" / "sample.kif",
            csv_path=project_root / "data" / "output" / "small.csv",
            volume_path="/Volumes/shogi_test/test/data",
            expected_game_count=1,
            # data/kif_files/sample.kif の手数（121手、投了を除く）に基づく暫定値。
            expected_row_count=121,
        )],
        # TODO(#151): medium/large/edge_casesシナリオ用のKIFファイルを用意し次第追加する。
        # "medium": [
        #     {
        #         "path": "/Volumes/shogi/test/data/small_01.csv",
        #         "expected_rows": 121,
        #         "expected_games": 1,
        #     },
        #     {
        #         "path": "/Volumes/shogi/test/data/small_02.csv",
        #         "expected_rows": 121,
        #         "expected_games": 1,
        #     },
        #     {
        #         "path": "/Volumes/shogi/test/data/small_03.csv",
        #         "expected_rows": 121,
        #         "expected_games": 1,
        #     },
        # ],
    }


@pytest.fixture(scope="function")
def test_scenario(test_data_config: dict[str, List[TestDataScenarioConfig]],
                  request: pytest.FixtureRequest) -> List[TestDataScenarioConfig]:
    """テストシナリオ設定を提供する

    Args:
        test_data_config: test_data_configフィクスチャから提供される設定
        request: pytestのrequestオブジェクト（パラメータ化テスト用）

    Returns:
         TestDataScenarioConfig: 選択されたシナリオの設定

    Usage:
        # デフォルト（small）を使用
        def test_something(test_scenario: dict):
            path = test_scenario["path"]

        # パラメータ化テストで使用
        @pytest.mark.parametrize("test_scenario", ["small", "medium"], indirect=True)
        def test_with_scenario(test_scenario: dict):
            path = test_scenario["path"]
    """
    # パラメータ化テストの場合はrequest.paramを使用
    if hasattr(request, "param") and request.param:
        scenario = request.param
    else:
        # デフォルトはsmallシナリオ
        scenario = "small"

    return test_data_config[scenario]


@pytest.fixture(scope="session")
def spark(databricks_profile: str) -> SparkSession:
    """環境に応じてDatabricks Connectセッションを構築する。

    ローカル実行時はDATABRICKS_CONFIG_PROFILE環境変数で指定したプロファイルを使用し、
    CI/CD（サービスプリンシパル認証）ではprofile()を呼ばず、環境変数ベースの
    デフォルト認証チェーン（oauth-m2m）に委ねる。

    ローカルの`.databrickscfg`ではプロファイル側の`serverless_compute_id = auto`に
    暗黙的に依存していたが、CD環境にはプロファイル自体が存在せずクラスタ／サーバーレスの
    どちらも解決できないため、`.serverless()`を明示的に指定し環境差を無くす。
    """
    builder = DatabricksSession.builder.serverless()
    if databricks_profile:
        builder = builder.profile(databricks_profile)
    return builder.getOrCreate()


@pytest.fixture(scope="session")
def workspace_client(databricks_profile: str) -> WorkspaceClient:
    """Job実行監視（JobMonitor）に使用するWorkspaceClientを構築する。

    sparkフィクスチャと同様、ローカル実行時はDATABRICKS_CONFIG_PROFILE環境変数で
    指定したプロファイルを使用し、CI/CD（サービスプリンシパル認証）では
    プロファイル指定なしで環境変数ベースのデフォルト認証チェーンに委ねる。
    """
    if databricks_profile:
        return WorkspaceClient(profile=databricks_profile)
    return WorkspaceClient()


@pytest.fixture(scope="session")
def job_id(_bundle_resources: dict) -> int:
    """デプロイ済みshogi_kif_rag_main_jobのjob_idをCLI経由で取得する。

    `_bundle_resources`（`databricks bundle summary` CLI実行結果）から取得する。
    本fixtureはJobを起動しない。

    Returns:
        int: databricks.yml/jobs.yml で定義されたshogi_kif_rag_main_jobのID。
    """
    return _bundle_resources["resources"]["jobs"]["shogi_kif_rag_main_job"]["id"]


@pytest.fixture(scope="session")
def job_run_result(workspace_client: WorkspaceClient, job_id: int) -> JobRunResult:
    """shogi_kif_rag_main_jobをSDK経由で起動し、完了するまで待機した結果を提供する。

    job_idの取得はCLI経由（`_bundle_resources`）、Job自体の起動・監視は
    Databricks SDK（`workspace_client.jobs.run_now` + `JobMonitor`）経由という
    Hybrid CLI + SDKアプローチを採る。

    Returns:
        JobRunResult: Job全体・タスク単位の実行結果。

    Raises:
        JobRunFailedError: いずれかのタスクがSUCCESS以外の結果で終了した場合。
        TimeoutError: タイムアウト時間内に完了しなかった場合。
    """
    waiter = workspace_client.jobs.run_now(job_id=job_id)
    return JobMonitor(workspace_client).wait_for_completion(waiter.run_id)


@pytest.fixture(scope="session", autouse=True)
def prepare_test_data(spark: SparkSession, test_data_config: dict) -> None:
    """テストデータを準備する

    テストデータが存在しない場合のみ、KIFファイルからCSVを生成する。
    エンジンはDatabricks上に存在しないため、
    エンジン解析なしでKIFをCSVに変換する関数を使用する。

    Args:
        spark: SparkSessionフィクスチャ
        test_data_config: test_data_configフィクスチャ

    Note:
        - 既にテストデータが存在する場合はスキップする（冪等性）
        - エンジン解析を行わないため、best_move, score_cp, pvはダミー値
        - テストデータの構造検証には十分
    """
    import csv
    from pathlib import Path

    from shogi_kif_rag.kif.parser import KifParser
    from shogi_kif_rag.kif.schemas.shemas import CSV_FIELDNAMES, AnalysisRow

    # smallシナリオのデータを準備
    small_configs = test_data_config["small"]

    # 各CSVファイル設定について処理
    for i, config in enumerate(small_configs):
        target_path = config["path"]

        # データが既に存在する場合はスキップ
        if _data_exists(spark, target_path):
            continue

        # KIFファイルからCSVを生成（エンジン解析なし）
        kif_path = Path("data/kif_files/sample.kif")

        # KIFファイルをパース
        parser = KifParser(str(kif_path))
        positions = parser.load_file()
        game_id = kif_path.stem

        # エンジン解析なしでCSV行を作成
        rows: list[AnalysisRow] = []
        for pos in positions:
            row: AnalysisRow = {
                "game_id": game_id,
                **pos,
                "best_move": "",  # ダミー値
                "score_cp": 0,     # ダミー値
                "pv": "",         # ダミー値
            }
            rows.append(row)

        # Spark DataFrameを作成してVolumeに保存
        from io import StringIO

        import pandas as pd

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

        pdf = pd.read_csv(StringIO(output.getvalue()))
        df = spark.createDataFrame(pdf)
        df.write.mode("overwrite").csv(target_path, header=True)


def _data_exists(spark: SparkSession, path: str) -> bool:
    """指定パスにデータが存在するか確認する

    Args:
        spark: SparkSession
        path: チェックするパス

    Returns:
        bool: データが存在する場合はTrue
    """
    try:
        df = spark.read.csv(path, header=True)
        return df.count() > 0
    except Exception:
        return False


@pytest.fixture(scope="session")
def positions_df(spark: SparkSession, positions_fqn: str) -> DataFrame:
    """Silverテーブルpositionsを読み込んだDataFrameを提供する。

    Returns:
        positionsテーブルの全件を保持するDataFrame。
    """
    return spark.table(positions_fqn)


@pytest.fixture(scope="session")
def position_features_df(spark: SparkSession, position_features_fqn: str) -> DataFrame:
    """Goldテーブルposition_featuresを読み込んだDataFrameを提供する。

    Returns:
        position_featuresテーブルの全件を保持するDataFrame。
    """
    return spark.table(position_features_fqn)


@pytest.fixture(scope="session")
def game_summary_df(spark: SparkSession, game_summary_fqn: str) -> DataFrame:
    """Goldテーブルgame_summaryを読み込んだDataFrameを提供する。

    Returns:
        game_summaryテーブルの全件を保持するDataFrame。
    """
    return spark.table(game_summary_fqn)
