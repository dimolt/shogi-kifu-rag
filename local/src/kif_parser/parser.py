"""ローカルKIFパーサモジュール（sharedのラッパー）"""

from shared.src.kif_parser.japanese_converter import usi_to_japanese
from shared.src.kif_parser.parser import kif_to_positions

__all__ = ["kif_to_positions", "usi_to_japanese"]
