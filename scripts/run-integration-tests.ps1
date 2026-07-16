# integrationテスト実行スクリプト
# カタログ名を shogi_dev に固定して実行

$env:TEST_CATALOG = "shogi_dev"
uv run pytest ./tests/integration/