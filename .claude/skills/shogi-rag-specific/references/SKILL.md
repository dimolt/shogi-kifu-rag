---
name: shogi-rag-specific
description: |
  将棋棋譜解析RAGシステム固有の開発手順・トラブルシューティング・
  やねうら王連携・ChromaDB管理などのプロジェクト固有知識。
  本プロジェクトの開発・デバッグ・デプロイ時に必ず参照する。
---

# 新規棋譜追加Playbook

## 目的
新しいKIFファイルをシステムに追加し、解析からRAG検索可能状態にする

## 前提条件
- やねうら王がインストールされている
- Databricks認証が完了している
- dbx環境が構築されている

## 手順

### 1. KIFファイル準備
```bash
# KIFファイルをdata/kif_files/に配置
cp /path/to/new_game.kif data/kif_files/
```

### 2. やねうら王解析
```bash
# 環境切り替え
.\scripts\switch-env.ps1 pyspark

# 解析実行（スクリプトを作成済みの場合）
uv run python src/shogi_kif_rag/kif/local_analyze.py data/kif_files/new_game.kif
```

### 3. Databricksへのアップロード
```bash
# 環境切り替え
.\scripts\switch-env.ps1 dbx

# Volumeにアップロード
databricks fs cp analysis.csv /Volumes/shogi_dev/landing/kif/ --profile shogi
```

### 4. パイプライン実行
```bash
# Silverパイプライン
databricks bundle run silver_pipeline -t dev --profile shogi

# Goldパイプライン
databricks bundle run gold_pipeline -t dev --profile shogi
```

### 5. ChromaDB再構築
```bash
# Databricks Notebookで実行
# dbx_bundle/notebooks/ntb_ui_demo.py の初期化セルを実行
```

### 6. 動作確認
```bash
# テスト実行
uv run pytest tests/integration/test_silver_pipeline.py -v
```

## トラブルシューティング
- パイプライン失敗: event_logを確認
- ChromaDBエラー: セッション再起動