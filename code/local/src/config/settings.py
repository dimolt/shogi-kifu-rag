"""ローカル実行用設定管理モジュール"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class LocalSettings(BaseSettings):
    """ローカル実行用設定"""

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # YaneuraOuエンジン設定
    yaneuraou_path: str = "YaneuraOu_nnue.exe"
    yaneuraou_options: str = ""

    # 入出力パス設定
    kif_input_dir: str = "data/kif_files"
    csv_output_dir: str = "data/output"

    # エンジン解析設定
    analysis_depth: int = 20
    analysis_nodes: int = 1000000
