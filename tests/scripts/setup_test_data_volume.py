"""
Job-based integration test用のテストデータをVolumeに配置するスクリプト。
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from shogi_kif_rag.kif.local_analyze import analyze_kif_to_csv
from tests.helpers.databricks.volume_helpers import (
    get_test_data_volume_path,
    upload_csv_to_volume,
)

logger = logging.getLogger(__name__)

class DataIngestionError(Exception):
    """kifのパースに失敗した場合。"""

SAMPLE_KIF_PATH = Path("./data/kif_files/sample.kif").resolve()
LOCAL_CSV_PATH = Path("./data/output/small.csv").resolve()


def generate_small_csv(kif_path: Path, output_path: Path) -> None:
    """sample.kifを基にsmall.csvをローカルに生成する。

    Args:
        kif_path: 変換元のkifファイルパス。
        output_path: 出力先CSVパス。

    Raises:
        DataIngestionError: kifのパースに失敗した場合。
    """
    try:
        analyze_kif_to_csv(kif_path, output_path)
    except Exception as e:
        raise DataIngestionError(f"kifパース失敗: {kif_path}") from e

    logger.info("small.csvを生成しました: %s", output_path)


def upload_to_volume(local_path: Path, volume_path: str) -> None:
    """生成したCSVをUnity Catalog Volumeにアップロードする。

    Args:
        local_path: ローカルのCSVファイルパス。
        volume_path: アップロード先のVolumeディレクトリパス。
    """
    upload_csv_to_volume(local_path, volume_path, "small.csv")
    logger.info("Volumeにアップロードしました: %s/small.csv", volume_path)


def main() -> None:
    """テストデータVolumeのセットアップを実行する。"""

    # dotenvで環境変数をロードする
    project_root = Path(__file__).parent.parent.parent
    load_dotenv(project_root / ".env")

    # カタログ名を取得（デフォルトはshogi_test）
    catalog = os.environ.get("TEST_CATALOG", "shogi_test")
    volume_path = get_test_data_volume_path(catalog)

    generate_small_csv(SAMPLE_KIF_PATH, LOCAL_CSV_PATH)
    upload_to_volume(LOCAL_CSV_PATH, volume_path)


if __name__ == "__main__":
    main()
