# 新規棋譜追加Playbook

## 目的
新しいKIFファイルをシステムに追加し、解析からRAG検索可能状態にするまでの一連の手順を定型化

## 前提条件
- やねうら王NNUEがインストールされている（Windows環境）
- Databricks認証が完了している（`databricks auth profiles` で確認）
- dbx環境が構築されている（`.\scripts\switch-env.ps1 dbx` 実行済み）
- Databricks Volume `/Volumes/{catalog}/landing/kif/` が存在する

## 手順

### 1. KIFファイル準備

```bash
# KIFファイルをdata/kif_files/に配置
cp /path/to/new_game.kif data/kif_files/

# ファイル形式確認（UTF-8, Shift-JIS対応）
file data/kif_files/new_game.kif
```

### 2. やねうら王解析（ローカルWindows環境）

```powershell
# 環境切り替え（PySpark環境）
.\scripts\switch-env.ps1 pyspark

# 環境変数設定（.envファイルから読み込み）
Get-Content .env | ForEach-Object { if ($_ -match '^([^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }

# 解析実行
uv run python -m shogi_kif_rag.kif.local_analyze data/kif_files/new_game.kif
```

**出力**: `data/kif_files/analysis.csv` が生成される

**解析内容**:
- 各局面のSFEN
- 評価値
- 最善手
- 読み筋

### 3. 解析結果の確認

```bash
# CSVファイルの確認
head -n 20 data/kif_files/analysis.csv

# 行数確認
wc -l data/kif_files/analysis.csv
```

### 4. Databricksへのアップロード

```powershell
# 環境切り替え（Databricks環境）
.\scripts\switch-env.ps1 dbx

# プロファイル確認
databricks auth profiles

# Volumeにアップロード
databricks fs cp data/kif_files/analysis.csv /Volumes/shogi_dev/landing/kif/ --profile shogi

# アップロード確認
databricks fs ls /Volumes/shogi_dev/landing/kif/ --profile shogi
```

### 5. Silverパイプライン実行

```bash
# パイプライン検証
databricks bundle validate -t dev --profile shogi

# Silverパイプライン実行
databricks bundle run silver_pipeline -t dev --profile shogi

# 実行状態確認
databricks pipelines list --profile shogi
databricks pipelines get <pipeline_id> --profile shogi
```

**待機時間**: 約5-10分（データ量による）

### 6. Goldパイプライン実行

```bash
# Goldパイプライン実行
databricks bundle run gold_pipeline -t dev --profile shogi

# 実行状態確認
databricks pipelines get <pipeline_id> --profile shogi
```

**待機時間**: 約10-15分（特徴量計算による）

### 7. パイプライン完了確認

```bash
# event_logで成功確認
databricks sql execute --profile shogi "
SELECT 
    pipeline_id,
    update_id,
    state,
    completed_at
FROM system.pipeline.execution.event_log(
    pipeline_id => '<silver_pipeline_id>'
)
ORDER BY completed_at DESC
LIMIT 5
"
```

**期待結果**: `state = COMPLETED`

### 8. ChromaDB再構築

```bash
# Databricks Notebookで実行
# dbx_bundle/notebooks/ntb_ui_demo.py を開く

# 以下のセルを実行:
# 1. セッション初期化
# 2. ChromaDBクライアント設定
# 3. データロード（Silver/Goldテーブルから）
# 4. Embedding生成
# 5. ChromaDBに追加
```

**Notebook実行手順**:
1. `ensure_chromadb()` 関数呼び出し
2. `load_positions_from_silver()` でデータ取得
3. `add_to_chromadb()` でベクトル化と追加
4. `query_chromadb()` で検索テスト

### 9. 動作確認

```bash
# 統合テスト実行
uv run pytest tests/integration/test_silver_pipeline.py -v

# RAG検索テスト（Notebookで）
# 新しい局面で検索を試す
```

### 10. ドキュメント更新

```bash
# README.mdに追加した棋譜情報を記録
git add README.md
git commit -m "docs: 新規棋譜 new_game.kif を追加"
```

## トラブルシューティング

### やねうら王解析失敗

**症状**: `local_analyze.py` がエラーになる

**原因と対策**:
- **パス設定エラー**: `.env` の `YANEURAOU_PATH` を確認
- **エンジン起動失敗**: やねうら王の実行権限を確認
- **文字コード問題**: KIFファイルのエンコーディングを確認（UTF-8/Shift-JIS）

```bash
# エンコーディング確認
file -i data/kif_files/new_game.kif

# 変換が必要な場合
iconv -f SHIFT_JIS -t UTF-8 input.kif > output.kif
```

### Databricksアップロード失敗

**症状**: `databricks fs cp` が失敗

**原因と対策**:
- **認証エラー**: `databricks auth login --profile shogi` を再実行
- **Volume不存在**: Volume作成スクリプトを実行
- **権限不足**: 管理者に権限付与を依頼

```bash
# Volume作成
databricks volumes create --catalog shogi_dev --schema landing --name kif --profile shogi
```

### パイプライン失敗

**症状**: パイプラインが `FAILED` になる

**原因と対策**:
- **データフォーマット不一致**: `analysis.csv` の列名を確認
- **スキーマ不一致**: Silverテーブルのスキーマを確認
- **リソース不足**: クラスタのサイズを確認

```bash
# event_logでエラー詳細確認
databricks sql execute --profile shogi "
SELECT 
    level,
    message,
    error_context
FROM system.pipeline.execution.event_log(
    pipeline_id => '<pipeline_id>'
)
WHERE level = 'ERROR'
ORDER BY timestamp DESC
LIMIT 10
"
```

### ChromaDBエラー

**症状**: ChromaDBへの追加が失敗

**原因と対策**:
- **メモリ不足**: セッションを再起動
- **Embeddingエラー**: `sentence-transformers` の再インストール
- **永続化パス問題**: [/tmp](cci:9://file:///tmp:0:0-0:0) の権限を確認

```bash
# セッション再起動
# Databricks Notebookで「Detach and re-attach」

# 依存関係再インストール
%pip install --upgrade sentence-transformers chromadb
```

## 成功基準

- [ ] やねうら王解析が正常完了（`analysis.csv` 生成）
- [ ] Databricks Volumeへのアップロード成功
- [ ] Silverパイプラインが `COMPLETED` になる
- [ ] Goldパイプラインが `COMPLETED` になる
- [ ] ChromaDBへのデータ追加成功
- [ ] RAG検索で新しい局面がヒットする
- [ ] 統合テストが通過する

## 所要時間

- やねうら王解析: 5-10分
- Databricksアップロード: 1-2分
- Silverパイプライン: 5-10分
- Goldパイプライン: 10-15分
- ChromaDB再構築: 5-10分
- **合計**: 約30-50分

## 関連ドキュメント

- [docs/development.md](../../docs/development.md) - 開発手順全般
- [docs/spec/shogi_kifu_rag_spec.md](../../docs/spec/shogi_kifu_rag_spec.md) - システム仕様
- [databricks-coreスキル](../skills/databricks-core/SKILL.md) - Databricks操作
- [shogi-rag-specificスキル](../skills/shogi-rag-specific/SKILL.md) - プロジェクト固有知識