"""USIエンジン連携モジュール"""

import re
import subprocess
import time
from typing import Optional


class UsiEngineClient:
    """USIエンジンとの連携を管理するクラス"""

    def __init__(self, engine_path: str, options: str = ""):
        """初期化

        Args:
            engine_path: やねうら王エンジンのパス
            options: エンジンオプション
        """
        self.engine_path = engine_path
        self.options = options
        self.process: Optional[subprocess.Popen] = None

    def start(self) -> None:
        """エンジンを起動する"""
        if self.process is not None:
            raise RuntimeError("Engine is already running")

        self.process = subprocess.Popen(
            [self.engine_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def initialize_usi(self, usi_hash: int = 256) -> None:
        """USIプロトコルの初期化を行う

        Args:
            usi_hash: USI_Hash設定値（MB）
        """
        if self.process is None:
            raise RuntimeError("Engine is not running")

        # USI初期化コマンド
        init_cmds = [
            "usi",
            f"setoption name USI_Hash value {usi_hash}",
            "setoption name ResignValue value 99999",
            "setoption name DrawValueBlack value 0",
            "setoption name DrawValueWhite value 0",
            "isready",
        ]

        for cmd in init_cmds:
            if self.process.stdin:
                self.process.stdin.write(cmd + "\n")
                self.process.stdin.flush()

        # readyokを待機
        if self.process.stdout:
            while True:
                line = self.process.stdout.readline()
                if not line:
                    break
                if line.strip() == "readyok":
                    break

    def stop(self) -> None:
        """エンジンを停止する"""
        if self.process is not None:
            self.process.terminate()
            self.process.wait()
            self.process = None

    def analyze_position(
        self, sfen: str, depth: int = 20, nodes: int = 1000000
    ) -> dict:
        """局面を解析する

        Args:
            sfen: SFEN形式の局面
            depth: 探索深さ
            nodes: 探索ノード数

        Returns:
            解析結果（best_move, score_cp, pvなど）
        """
        if self.process is None:
            raise RuntimeError("Engine is not running")

        # USIプロトコルで解析を依頼
        commands = [
            f"position sfen {sfen}",
            f"go depth {depth} nodes {nodes}",
        ]

        for cmd in commands:
            if self.process.stdin:
                self.process.stdin.write(cmd + "\n")
                self.process.stdin.flush()

        # 結果を解析（簡易実装）
        # 実際にはエンジンからの出力をパースする必要がある
        return {
            "best_move": "",
            "score_cp": 0,
            "pv": [],
        }

    def analyze_position_with_time(
        self, sfen: str, think_time: float = 3.0, usi_hash: int = 256
    ) -> dict:
        """思考時間指定で局面を解析する

        Args:
            sfen: SFEN形式の局面
            think_time: 思考時間（秒）
            usi_hash: USI_Hash設定値（MB）

        Returns:
            解析結果（best_move, score_cp, pvなど）
        """
        if self.process is None:
            raise RuntimeError("Engine is not running")

        # USI初期化コマンド
        init_cmds = [
            "usi",
            f"setoption name USI_Hash value {usi_hash}",
            "setoption name ResignValue value 99999",
            "setoption name DrawValueBlack value 0",
            "setoption name DrawValueWhite value 0",
            "isready",
            f"position sfen {sfen}",
            "go infinite",
        ]

        for cmd in init_cmds:
            if self.process.stdin:
                self.process.stdin.write(cmd + "\n")
                self.process.stdin.flush()

        time.sleep(think_time)

        if self.process.stdin:
            self.process.stdin.write("stop\n")
            self.process.stdin.flush()

        time.sleep(0.3)

        if self.process.stdin:
            self.process.stdin.write("quit\n")
            self.process.stdin.flush()

        try:
            out, _ = self.process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            out, _ = self.process.communicate()

        # 結果をパース
        best_move = "resign"
        score_cp = 0
        pv = ""

        info_lines = [
            line
            for line in out.splitlines()
            if line.startswith("info depth")
        ]
        if info_lines:
            last = info_lines[-1]

            # 通常評価値
            m = re.search(r"score cp\s+(-?\d+)", last)
            if m:
                score_cp = int(m.group(1))

            # 詰み: score mate N → ±30000cpに変換
            m = re.search(r"score mate\s+(-?\d+)", last)
            if m:
                mate_n = int(m.group(1))
                score_cp = 30000 if mate_n > 0 else -30000

            m = re.search(r"\bpv\s+(.+)", last)
            if m:
                pv = " ".join(m.group(1).split()[:8])

        m = re.search(r"bestmove\s+(\S+)", out)
        if m:
            best_move = m.group(1)

        return {
            "best_move": best_move,
            "score_cp": score_cp,
            "pv": pv,
        }

    def analyze_position_reusable(
        self, sfen: str, think_time: float = 3.0
    ) -> dict:
        """エンジンを再利用して局面を解析する

        Args:
            sfen: SFEN形式の局面
            think_time: 思考時間（秒）

        Returns:
            解析結果（best_move, score_cp, pvなど）
        """
        if self.process is None:
            raise RuntimeError("Engine is not running")

        # USIコマンド（初期化はスキップ）
        cmds = [
            f"position sfen {sfen}",
            "go infinite",
        ]

        for cmd in cmds:
            if self.process.stdin:
                self.process.stdin.write(cmd + "\n")
                self.process.stdin.flush()

        time.sleep(think_time)

        if self.process.stdin:
            self.process.stdin.write("stop\n")
            self.process.stdin.flush()

        # 出力を読み取る（bestmoveまで待機）
        out_lines = []
        if self.process.stdout:
            while True:
                line = self.process.stdout.readline()
                if not line:
                    break
                out_lines.append(line)
                if line.startswith("bestmove"):
                    break

        out = "".join(out_lines)

        # 結果をパース
        best_move = "resign"
        score_cp = 0
        pv = ""

        info_lines = [
            line
            for line in out.splitlines()
            if line.startswith("info depth")
        ]
        if info_lines:
            last = info_lines[-1]

            # 通常評価値
            m = re.search(r"score cp\s+(-?\d+)", last)
            if m:
                score_cp = int(m.group(1))

            # 詰み: score mate N → ±30000cpに変換
            m = re.search(r"score mate\s+(-?\d+)", last)
            if m:
                mate_n = int(m.group(1))
                score_cp = 30000 if mate_n > 0 else -30000

            m = re.search(r"\bpv\s+(.+)", last)
            if m:
                pv = " ".join(m.group(1).split()[:8])

        m = re.search(r"bestmove\s+(\S+)", out)
        if m:
            best_move = m.group(1)

        return {
            "best_move": best_move,
            "score_cp": score_cp,
            "pv": pv,
        }
