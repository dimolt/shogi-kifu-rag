"""
Job-based integration test用のテストデータをVolumeに配置するスクリプト。
"""

import logging
from pathlib import Path

from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv

from shogi_kif_rag.kif.local_analyze import analyze_kif_to_csv

logger = logging.getLogger(__name__)

class DataIngestionError(Exception):
    """kifのパースに失敗した場合。"""

VOLUME_PATH = "/Volumes/shogi_test/test/data"
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
    w = WorkspaceClient(profile="shogi")
    remote_path = f"{volume_path}/small.csv"
    with local_path.open("rb") as f:
        w.files.upload(remote_path, f, overwrite=True)
    logger.info("Volumeにアップロードしました: %s", remote_path)


def main() -> None:
    """テストデータVolumeのセットアップを実行する。"""

    # dotenvで環境変数をロードする
    project_root = Path(__file__).parent.parent.parent
    load_dotenv(project_root / ".env")

    generate_small_csv(SAMPLE_KIF_PATH, LOCAL_CSV_PATH)
    upload_to_volume(LOCAL_CSV_PATH, VOLUME_PATH)


if __name__ == "__main__":
    main()
