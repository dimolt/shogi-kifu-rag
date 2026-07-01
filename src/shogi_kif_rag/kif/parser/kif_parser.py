"""KIFパーサモジュール"""

import chardet
import shogi
import shogi.KIF


class KifParser:
    """KIFファイルをパースして局面リストを生成するパーサクラス"""

    def __init__(self, file_path: str) -> None:
        """パーサを初期化する

        Args:
            file_path: KIFファイルのパス
        """
        self.file_path = file_path

    def load_file(self) -> list[dict]:
        """KIFファイルを読み込んで局面リストを生成する

        Returns:
            局面情報の辞書リスト
        """
        encoding = self._detect_encoding()
        kif_content = self._load_file_content(encoding)
        return self._parse_kif_content(kif_content)

    def _detect_encoding(self) -> str:
        """ファイルのエンコーディングを検出する

        Returns:
            エンコーディング名（cp932または検出結果）
        """
        with open(self.file_path, "rb") as f:
            raw = f.read()
        enc = chardet.detect(raw).get("encoding", "utf-8") or "utf-8"
        # cp1006はcp932のエイリアスとして扱う
        if enc.lower() in ("shift_jis", "shift-jis", "sjis", "cp1006"):
            return "cp932"
        return enc

    def _load_file_content(self, encoding: str) -> str:
        """エンコーディング検出後にファイルを読み込む

        Args:
            encoding: 検出されたエンコーディング

        Returns:
            ファイルの内容
        """
        with open(self.file_path, encoding=encoding, errors="replace") as f:
            return f.read()

    def _parse_kif_content(self, kif_content: str) -> list[dict]:
        """KIF文字列をパースして局面リストを生成する

        Args:
            kif_content: KIF形式の棋譜文字列

        Returns:
            局面情報の辞書リスト
        """
        kif = shogi.KIF.Parser.parse_str(kif_content)[0]
        black_player, white_player = self._extract_player_info(kif)
        moves = kif.get("moves", [])

        board = shogi.Board()
        records = []
        records.append(
            self._build_initial_record(board, black_player, white_player)
        )

        for i, move in enumerate(moves):
            move_int, move_usi = self._parse_move(move)
            if move_int is None:
                break

            player = "black" if board.turn == shogi.BLACK else "white"
            prev_sfen = board.sfen()

            try:
                board.push(move_int)
            except Exception:
                break

            records.append(
                self._build_move_record(
                    board,
                    move_int,
                    move_usi,
                    player,
                    black_player,
                    white_player,
                    i + 1,
                    prev_sfen,
                )
            )

        return records

    def _extract_player_info(self, kif) -> tuple[str, str]:
        """KIFオブジェクトからプレイヤー名を抽出する

        Args:
            kif: shogi.KIF.Parser.parse_strの結果

        Returns:
            (先手の名前, 後手の名前)
        """
        names = kif.get("names", [])
        black_player = names[0] if len(names) > 0 else "先手"
        white_player = names[1] if len(names) > 1 else "後手"
        return black_player, white_player

    def _build_initial_record(
        self, board: shogi.Board, black_player: str, white_player: str
    ) -> dict:
        """初期局面のレコードを構築する

        Args:
            board: shogi.Boardオブジェクト
            black_player: 先手の名前
            white_player: 後手の名前

        Returns:
            初期局面の辞書
        """
        return {
            "move_number": 0,
            "sfen": board.sfen(),
            "prev_sfen": board.sfen(),
            "move_usi": "",
            "player": "black",
            "black_player": black_player,
            "white_player": white_player,
        }

    def _parse_move(self, move) -> tuple[shogi.Move | None, str]:
        """指し手をパースしてMoveオブジェクトとUSI文字列を返す

        Args:
            move: 指し手（文字列またはMoveオブジェクト）

        Returns:
            (Moveオブジェクト, USI文字列)。パース失敗時は (None, "")
        """
        if isinstance(move, str):
            move_usi = move
            try:
                move_int = shogi.Move.from_usi(move_usi)
            except Exception:
                return None, ""
        else:
            move_int = move
            try:
                move_usi = shogi.move_to_usi(move_int)
            except Exception:
                move_usi = str(move)
        return move_int, move_usi

    def _build_move_record(
        self,
        board: shogi.Board,
        move_int: shogi.Move,
        move_usi: str,
        player: str,
        black_player: str,
        white_player: str,
        move_number: int,
        prev_sfen: str,
    ) -> dict:
        """指し手のレコードを構築する

        Args:
            board: shogi.Boardオブジェクト
            move_int: shogi.Moveオブジェクト
            move_usi: USI形式の指し手
            player: 手番（"black"または"white"）
            black_player: 先手の名前
            white_player: 後手の名前
            move_number: 手数
            prev_sfen: 指し手前のSFEN

        Returns:
            指し手の辞書
        """
        return {
            "move_number": move_number,
            "sfen": board.sfen(),
            "prev_sfen": prev_sfen,
            "move_usi": move_usi,
            "player": player,
            "black_player": black_player,
            "white_player": white_player,
        }


def detect_encoding(file_path: str) -> str:
    """ファイルのエンコーディングを検出する

    Args:
        file_path: ファイルパス

    Returns:
        エンコーディング名（cp932または検出結果）
    """
    with open(file_path, "rb") as f:
        raw = f.read()
    enc = chardet.detect(raw).get("encoding", "utf-8") or "utf-8"
    if enc.lower() in ("shift_jis", "shift-jis", "sjis", "cp1006"):
        return "cp932"
    return enc


def kif_to_positions(kif_content: str) -> list[dict]:
    """KIF形式の棋譜をパースして局面リストを生成する

    Args:
        kif_content: KIF形式の棋譜文字列

    Returns:
        局面情報の辞書リスト
    """
    kif = shogi.KIF.Parser.parse_str(kif_content)[0]
    names = kif.get("names", [])
    black_player = names[0] if len(names) > 0 else "先手"
    white_player = names[1] if len(names) > 1 else "後手"
    moves = kif.get("moves", [])

    board = shogi.Board()
    records = []
    records.append({
        "move_number": 0,
        "sfen": board.sfen(),
        "prev_sfen": board.sfen(),
        "move_usi": "",
        "player": "black",
        "black_player": black_player,
        "white_player": white_player,
    })

    for i, move in enumerate(moves):
        if isinstance(move, str):
            move_usi = move
            try:
                move_int = shogi.Move.from_usi(move_usi)
            except Exception:
                break
        else:
            move_int = move
            try:
                move_usi = shogi.move_to_usi(move_int)
            except Exception:
                move_usi = str(move)

        player = "black" if board.turn == shogi.BLACK else "white"
        prev_sfen = board.sfen()

        try:
            board.push(move_int)
        except Exception:
            break

        records.append({
            "move_number": i + 1,
            "sfen": board.sfen(),
            "prev_sfen": prev_sfen,
            "move_usi": move_usi,
            "player": player,
            "black_player": black_player,
            "white_player": white_player,
        })

    return records
