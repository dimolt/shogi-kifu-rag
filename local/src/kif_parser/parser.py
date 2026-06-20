"""ローカルKIFパーサモジュール（sharedのラッパー）"""

import sys
from pathlib import Path
import importlib.util

# sharedモジュールをパスに追加
shared_path = Path(__file__).parent.parent.parent.parent / "shared" / "src"
sys.path.insert(0, str(shared_path))

# sharedモジュールをインポート（循環インポート回避のため）
japanese_converter_spec = importlib.util.spec_from_file_location(
    "shared_japanese_converter",
    shared_path / "kif_parser" / "japanese_converter.py"
)
japanese_converter = importlib.util.module_from_spec(japanese_converter_spec)
japanese_converter_spec.loader.exec_module(japanese_converter)

parser_spec = importlib.util.spec_from_file_location(
    "shared_parser",
    shared_path / "kif_parser" / "parser.py"
)
kif_parser_module = importlib.util.module_from_spec(parser_spec)
parser_spec.loader.exec_module(kif_parser_module)

usi_to_japanese = japanese_converter.usi_to_japanese
kif_to_positions = kif_parser_module.kif_to_positions

__all__ = ["kif_to_positions", "usi_to_japanese"]
