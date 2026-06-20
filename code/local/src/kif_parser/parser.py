"""ローカルKIFパーサモジュール（sharedのラッパー）"""

import importlib.util
import sys
from pathlib import Path

# sharedモジュールをパスに追加
shared_path = Path(__file__).parent.parent.parent.parent / "shared" / "src"
sys.path.insert(0, str(shared_path))

# sharedモジュールをインポート（循環インポート回避のため）
japanese_converter_spec = importlib.util.spec_from_file_location(
    "shared_japanese_converter",
    shared_path / "kif_parser" / "japanese_converter.py"
)
if japanese_converter_spec is None:
    raise ImportError("Failed to load japanese_converter spec")
japanese_converter = importlib.util.module_from_spec(japanese_converter_spec)
if japanese_converter_spec.loader:
    japanese_converter_spec.loader.exec_module(japanese_converter)

parser_spec = importlib.util.spec_from_file_location(
    "shared_parser",
    shared_path / "kif_parser" / "parser.py"
)
if parser_spec is None:
    raise ImportError("Failed to load parser spec")
shared_parser = importlib.util.module_from_spec(parser_spec)
if parser_spec.loader:
    parser_spec.loader.exec_module(shared_parser)

kif_to_positions = shared_parser.kif_to_positions
usi_to_japanese = japanese_converter.usi_to_japanese

__all__ = ["kif_to_positions", "usi_to_japanese"]
