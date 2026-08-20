# 異常系テストデータ

Integration Testの異常系テストデータ原本を格納するディレクトリ。

## ディレクトリ構造

- `schema_errors/`: スキーマ違反のテストデータ
  - `missing_game_id.csv`: game_id列が空のCSV（valid_game_id expectationテスト用）
  - `invalid_move_number.csv`: move_numberに文字列を含むCSV（valid_move_number expectationテスト用）
- `format_errors/`: フォーマットエラーのテストデータ（将来拡張用）

## 使用方法

これらのファイルはGit管理されたテストデータ原本です。
実際のテスト実行時は、pytest fixtureを通じてVolumeにコピーされます。

テストコードから直接参照せず、必ずfixture経由で使用してください。
