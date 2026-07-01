"""local_analyze.py のユニットテスト。"""

from pathlib import Path

import pytest

from shogi_kif_rag.kif.local_analyze import (
    AnalysisRow,
    AnalyzeError,
    PositionRecord,
    _analyze_positions,
    _load_positions,
    _parse_args,
    _write_csv,
)


class TestParseArgs:
    """_parse_args のテスト。"""

    def test_parse_args_引数なしの場合_デフォルトパスを返す(self) -> None:
        # Act
        kif_path, out_csv = _parse_args(["local_analyze.py"])

        # Assert
        assert kif_path == Path("data/kif_files/sample.kif")
        assert out_csv == Path("data/output/analysis.csv")

    def test_parse_args_引数を2つ渡すと_指定したパスを返す(self) -> None:
        # Arrange
        argv = ["local_analyze.py", "my.kif", "out/result.csv"]

        # Act
        kif_path, out_csv = _parse_args(argv)

        # Assert
        assert kif_path == Path("my.kif")
        assert out_csv == Path("out/result.csv")

    def test_parse_args_kifパスのみ渡すと_出力先はデフォルトを返す(self) -> None:
        # Act
        _, out_csv = _parse_args(["local_analyze.py", "my.kif"])

        # Assert
        assert out_csv == Path("data/output/analysis.csv")


class TestLoadPositions:
    """_load_positions のテスト。"""

    def test_load_positions_ファイルが存在しないと_AnalyzeErrorを送出する(
        self, tmp_path: Path
    ) -> None:
        # Arrange
        missing_path = tmp_path / "not_exist.kif"

        # Act & Assert
        with pytest.raises(AnalyzeError):
            _load_positions(missing_path)

    def test_load_positions_パース中に例外が発生すると_AnalyzeErrorを送出する(
        self, tmp_path: Path, mocker
    ) -> None:
        # Arrange
        kif_path = tmp_path / "sample.kif"
        kif_path.write_text("dummy")
        mock_parser_cls = mocker.patch("shogi_kif_rag.kif.local_analyze.KifParser")
        mock_parser_cls.return_value.load_file.side_effect = ValueError("パース失敗")

        # Act & Assert
        with pytest.raises(AnalyzeError):
            _load_positions(kif_path)

    def test_load_positions_有効なファイルを渡すと_局面リストを返す(
        self,
        tmp_path: Path,
        mocker,
        sample_positions: list[PositionRecord],
    ) -> None:
        # Arrange
        kif_path = tmp_path / "sample.kif"
        kif_path.write_text("dummy")
        mock_parser_cls = mocker.patch("shogi_kif_rag.kif.local_analyze.KifParser")
        mock_parser_cls.return_value.load_file.return_value = sample_positions

        # Act
        result = _load_positions(kif_path)

        # Assert
        assert result == sample_positions


class TestAnalyzePositions:
    """_analyze_positions のテスト。"""

    def test_analyze_positions_全局面が成功すると_局面数分の結果を返す(
        self,
        mocker,
        sample_positions: list[PositionRecord],
        mock_engine_result: dict,
    ) -> None:
        # Arrange
        mock_analyzer = mocker.Mock()
        mock_analyzer.analyze_position_reusable.return_value = mock_engine_result

        # Act
        rows = _analyze_positions(mock_analyzer, sample_positions, game_id="game_001")

        # Assert
        assert len(rows) == len(sample_positions)

    def test_analyze_positions_成功すると_各行にgame_idと解析結果を含む(
        self,
        mocker,
        sample_positions: list[PositionRecord],
        mock_engine_result: dict,
    ) -> None:
        # Arrange
        mock_analyzer = mocker.Mock()
        mock_analyzer.analyze_position_reusable.return_value = mock_engine_result

        # Act
        rows = _analyze_positions(mock_analyzer, sample_positions, game_id="game_001")

        # Assert
        assert rows[0]["game_id"] == "game_001"
        assert rows[0]["best_move"] == mock_engine_result["best_move"]
        assert rows[0]["score_cp"] == mock_engine_result["score_cp"]
        assert rows[0]["pv"] == mock_engine_result["pv"]

    def test_analyze_positions_エンジン解析に失敗すると_AnalyzeErrorを送出する(
        self, mocker, sample_positions: list[PositionRecord]
    ) -> None:
        # Arrange
        mock_analyzer = mocker.Mock()
        mock_analyzer.analyze_position_reusable.side_effect = RuntimeError("解析失敗")

        # Act & Assert
        with pytest.raises(AnalyzeError):
            _analyze_positions(mock_analyzer, sample_positions, game_id="game_001")

    def test_analyze_positions_各局面ごとに_analyze_position_reusableが呼ばれる(
        self,
        mocker,
        sample_positions: list[PositionRecord],
        mock_engine_result: dict,
    ) -> None:
        # Arrange
        mock_analyzer = mocker.Mock()
        mock_analyzer.analyze_position_reusable.return_value = mock_engine_result

        # Act
        _analyze_positions(mock_analyzer, sample_positions, game_id="game_001")

        # Assert
        assert mock_analyzer.analyze_position_reusable.call_count == len(
            sample_positions
        )


class TestWriteCsv:
    """_write_csv のテスト。"""

    def test_write_csv_出力先ディレクトリが存在しないと_ディレクトリを作成する(
        self, tmp_path: Path, sample_analysis_row: AnalysisRow
    ) -> None:
        # Arrange
        out_csv = tmp_path / "nested" / "dir" / "analysis.csv"

        # Act
        _write_csv([sample_analysis_row], out_csv)

        # Assert
        assert out_csv.parent.exists()

    def test_write_csv_書き込み後_ヘッダー行を含むCSVファイルが生成される(
        self, tmp_path: Path, sample_analysis_row: AnalysisRow
    ) -> None:
        # Arrange
        out_csv = tmp_path / "analysis.csv"

        # Act
        _write_csv([sample_analysis_row], out_csv)
        content = out_csv.read_text(encoding="utf-8")

        # Assert
        assert content.startswith("game_id,move_number,sfen")

    def test_write_csv_書き込んだ内容を再読込すると_元の行数と一致する(
        self, tmp_path: Path, sample_analysis_row: AnalysisRow
    ) -> None:
        # Arrange
        import csv

        out_csv = tmp_path / "analysis.csv"
        rows = [sample_analysis_row, sample_analysis_row]

        # Act
        _write_csv(rows, out_csv)
        with open(out_csv, encoding="utf-8") as f:
            read_rows = list(csv.DictReader(f))

        # Assert
        assert len(read_rows) == len(rows)