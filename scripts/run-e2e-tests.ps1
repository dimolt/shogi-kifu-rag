# e2eテスト実行スクリプト
# カタログ名を shogi_test に固定して実行

$env:TEST_CATALOG = "shogi_test"
uv run pytest ./tests/e2e/