"""ローカル実行用設定管理モジュール"""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# エンジン解析設定のデフォルト値（マジックナンバー回避のため定数化）
DEFAULT_YANEURAOU_PATH = "YaneuraOu_nnue.exe"
DEFAULT_KIF_INPUT_DIR = Path("data/kif_files")
DEFAULT_CSV_OUTPUT_DIR = Path("data/output")
DEFAULT_ANALYSIS_DEPTH = 20
DEFAULT_ANALYSIS_NODES = 1_000_000


class LocalAnalyzeSettings(BaseSettings):
    """ローカル実行用設定。

    `.env.local_analyze` ファイルから環境変数を読み込み、
    YaneuraOuエンジンによるローカル解析処理に必要な設定値を保持する。
    """

    model_config = SettingsConfigDict(
        env_file=".env.local_analyze",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # YaneuraOuエンジン設定
    yaneuraou_path: str = Field(
        default=DEFAULT_YANEURAOU_PATH,
        description="YaneuraOuエンジンの実行ファイルパス。",
    )
    yaneuraou_options: str = Field(
        default="",
        description="YaneuraOuエンジンに渡す追加オプション文字列。",
    )

    # 入出力パス設定
    kif_input_dir: Path = Field(
        default=DEFAULT_KIF_INPUT_DIR,
        description="KIFファイルを読み込むディレクトリのパス。",
    )
    csv_output_dir: Path = Field(
        default=DEFAULT_CSV_OUTPUT_DIR,
        description="解析結果CSVを出力するディレクトリのパス。",
    )

    # エンジン解析設定
    analysis_depth: int = Field(
        default=DEFAULT_ANALYSIS_DEPTH,
        description="エンジン解析の探索深さ。",
    )
    analysis_nodes: int = Field(
        default=DEFAULT_ANALYSIS_NODES,
        description="エンジン解析の探索ノード数上限。",
    )

    @field_validator("analysis_depth", "analysis_nodes")
    @classmethod
    def validate_positive(cls, value: int) -> int:
        """解析深さ・ノード数が正の整数であることを検証する。

        Args:
            value: 検証対象の値。

        Returns:
            検証済みの値。

        Raises:
            ValueError: 値が1未満の場合。
        """
        if value < 1:
            raise ValueError("analysis_depth / analysis_nodes は1以上の整数である必要があります。") #noqa: E501
        return value
