"""CSVファイル処理に関するユーティリティ関数群。"""

from pathlib import Path


def resolve_csv_paths(csv_path: str) -> str | list[str]:
    """CSVパスを解決する。

    ワイルドカードが含まれる場合は一致したファイル一覧を返し、
    含まれない場合はそのまま返す。ディレクトリパスの場合もそのまま返す。
    Databricks Volumeパス（/Volumes/で始まる）の場合はワイルドカード展開をスキップし、
    Sparkに処理を委ねる。

    Args:
        csv_path: CSVファイルパス（単一ファイル、ディレクトリ、
                  ワイルドカードパターンをサポート）。

    Returns:
        ワイルドカード展開後のファイルパス（単一文字列または文字列リスト）。

    Raises:
        FileNotFoundError: ワイルドカードパターンに一致するファイルが存在しない場合。
    """
    # Databricks Volumeパスの場合はワイルドカード展開をスキップ（Sparkに委ねる）
    if csv_path.startswith("/Volumes/"):
        return csv_path

    # ワイルドカードが含まれない場合はそのまま返す
    if not any(char in csv_path for char in "*?[]"):
        return csv_path

    path = Path(csv_path)
    paths = sorted(
        str(p)
        for p in path.parent.glob(path.name)
        if p.is_file()
    )

    if not paths:
        raise FileNotFoundError(f"No files matched: {csv_path}")

    return paths
