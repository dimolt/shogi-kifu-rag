"""やねうら王エンジン連携モジュール"""

import subprocess
from typing import Optional


class YaneuraOuAnalyzer:
    """やねうら王エンジンとの連携を管理するクラス"""

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
        return {
            "best_move": "",
            "score_cp": 0,
            "pv": [],
        }
