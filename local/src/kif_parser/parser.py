"""ローカルKIFパーサモジュール（sharedのラッパー）"""

import sys
from pathlib import Path

# sharedモジュールをパスに追加
shared_path = Path(__file__).parent.parent.parent / "shared" / "src"
sys.path.insert(0, str(shared_path))

from shared.src.kif_parser.japanese_converter import usi_to_japanese
from shared.src.kif_parser.parser import kif_to_positions

__all__ = ["kif_to_positions", "usi_to_japanese"]
