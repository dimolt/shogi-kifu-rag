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
if japanese_converter_spec.loader is None:
    raise ImportError("Failed to load japanese_converter loader")
japanese_converter_spec.loader.exec_module(japanese_converter)

parser_spec = importlib.util.spec_from_file_location(
    "shared_parser",
    shared_path / "kif_parser" / "parser.py"
)
if parser_spec is None:
    raise ImportError("Failed to load parser spec")
kif_parser_module = importlib.util.module_from_spec(parser_spec)
if parser_spec.loader is None:
    raise ImportError("Failed to load parser loader")
parser_spec.loader.exec_module(kif_parser_module)

usi_to_japanese = japanese_converter.usi_to_japanese
kif_to_positions = kif_parser_module.kif_to_positions

__all__ = ["kif_to_positions", "usi_to_japanese"]
