import sys
from pathlib import Path

# sharedモジュールをパスに追加
shared_path = Path(__file__).parent.parent.parent / "shared" / "src"
sys.path.insert(0, str(shared_path))

from .parser import kif_to_positions, usi_to_japanese  # noqa: E402

__all__ = ["kif_to_positions", "usi_to_japanese"]
