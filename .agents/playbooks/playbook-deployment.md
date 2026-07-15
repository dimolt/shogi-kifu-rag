# デプロイPlaybook

## 目的
開発環境から本番環境へのデプロイを安全かつ確実に実行するための定型手順

## 前提条件
- すべてのテストが通過している
- Databricks認証が完了している
- Gitの作業ディレクトリがクリーンである
- デプロイ先の環境（test/prod）が準備されている

## 手順

### 1. デプロイ前チェック

#### 1.1 コード品質チェック

```bash
# Lintチェック
uv run ruff check .

# フォーマットチェック
uv run ruff format --check .

# 型チェック
uv run mypy src/
```

#### 1.2 ユニットテスト実行

```bash
# ユニットテスト
uv run pytest tests/unit -v

# カバレッジ確認（オプション）
uv run pytest tests/unit --cov=src/shogi_kif_rag --cov-report=html
```

**成功基準**: すべてのテストが通過、カバレッジ80%以上

#### 1.3 統合テスト実行（dev環境）

```bash
# 環境切り替え
.\scripts\switch-env.ps1 dbx

# 統合テスト
uv run pytest tests/integration -v
```

**前提**: dev環境のパイプラインが直近24時間以内に実行されている

#### 1.4 バンドル検証

```bash
# dev環境検証
databricks bundle validate -t dev --profile shogi

# test環境検証
databricks bundle validate -t test --profile shogi

# prod環境検証
databricks bundle validate -t prod --profile shogi
```

**成功基準**: すべての環境で検証が通過

#### 1.5 Gitステータス確認

```bash
# 変更ファイルの確認
git status

# 未コミットの変更がないことを確認
git diff
```

### 2. ブランチとマージ

#### 2.1 featureブランチからmainへマージ

```bash
# mainブランチへ移動
git checkout main

# 最新の状態に更新
git pull origin main

# featureブランチをマージ
git merge feature/your-feature

# コンフリクトがあれば解決
# （コンフリクト解決後）
git add .
git commit -m "resolve: マージコンフリクト解決"
```

#### 2.2 マージ結果の確認

```bash
# ログ確認
_git log --oneline -5

# 変更内容確認
git diff origin/main
```

### 3. タグ付けとプッシュ

#### 3.1 バージョン番号の決定

**バージョン番号ルール**:
- `v0.1.0-test`: test環境デプロイ用
- `v0.1.0`: prod環境デプロイ用
- セマンティックバージョニング（Major.Minor.Patch）

#### 3.2 タグ作成

```bash
# test環境デプロイの場合
git tag v0.1.0-test

# prod環境デプロイの場合
git tag v0.1.0

# タグにメッセージを追加（オプション）
git tag -a v0.1.0 -m "Release version 0.1.0: 新規棋譜解析機能追加"
```

#### 3.3 プッシュ

```bash
# mainブランチをプッシュ
git push origin main

# タグをプッシュ
git push origin v0.1.0-test  # または v0.1.0
```

### 4. CDワークフロー実行

#### 4.1 GitHub Actionsの監視

```bash
# GitHubでActionsタブを開く
# https://github.com/your-org/shogi-kif-rag/actions

# ワークフローの実行状態を確認
```

**監視項目**:
- `deploy-dev` ジョブ（mainブランチマージ時）
- `deploy-test` ジョブ（`-test`タグ時）
- `deploy-prod` ジョブ（通常タグ時）

#### 4.2 ワークフローログの確認

**確認ポイント**:
- 依存関係インストール成功
- バンドル検証成功
- Databricksデプロイ成功
- E2Eテスト成功（test環境のみ）

### 5. デプロイ後検証

#### 5.1 環境接続確認

```bash
# test環境プロファイル確認
databricks auth profiles

# test環境接続
databricks current-user me --profile shogi_test
```

#### 5.2 リソース確認

```bash
# ジョブ確認
databricks jobs list --profile shogi_test

# パイプライン確認
databricks pipelines list --profile shogi_test

# テーブル確認
databricks tables list shogi_test shogi_silver --profile shogi_test
databricks tables list shogi_test shogi_gold --profile shogi_test
```

#### 5.3 パイプライン手動実行（test環境）

```bash
# Silverパイプライン実行
databricks bundle run silver_pipeline -t test --profile shogi_test

# Goldパイプライン実行
databricks bundle run gold_pipeline -t test --profile shogi_test
```

#### 5.4 データ品質確認

```bash
# Silverテーブルの行数確認
databricks sql execute --profile shogi_test "
SELECT COUNT(*) as row_count
FROM shogi_test.shogi_silver.positions
"

# Goldテーブルの行数確認
databricks sql execute --profile shogi_test "
SELECT COUNT(*) as row_count
FROM shogi_test.shogi_gold.position_features
"

# 最新データの確認
databricks sql execute --profile shogi_test "
SELECT *
FROM shogi_test.shogi_silver.positions
ORDER BY game_id DESC, move_number DESC
LIMIT 10
"
```

### 6. 本番環境デプロイ（test環境検証後）

#### 6.1 test環境でのE2Eテスト

```bash
# E2Eテスト実行
uv run pytest tests/e2e/ -v
```

**成功基準**: すべてのE2Eテストが通過

#### 6.2 prod環境タグ付け

```bash
# test環境で問題なければprod環境タグ作成
git tag v0.1.0
git push origin v0.1.0
```

#### 6.3 prod環境デプロイ監視

- GitHub Actionsの `deploy-prod` ジョブを監視
- デプロイ完了を待つ

#### 6.4 prod環境検証

```bash
# prod環境接続
databricks current-user me --profile shogi

# リソース確認
databricks jobs list --profile shogi
databricks pipelines list --profile shogi

# データ確認
databricks sql execute --profile shogi "
SELECT COUNT(*) as row_count
FROM shogi.shogi_silver.positions
"
```

### 7. リリースノート作成

```markdown
# Release v0.1.0

## 新機能
- 新規棋譜解析機能の追加
- やねうら王NNUE連携の強化

## バグ修正
- ChromaDB永続化問題の修正
- パイプライン実行時のメモリ不足対策

## 変更内容
- Silverパイプラインの最適化
- Goldテーブルのスキーマ更新

## 既知の問題
- なし

## アップグレード手順
1. デプロイ完了後、ChromaDB再構築が必要
2. 既存の検索インデックスは再作成されます
```

### 8. 通知と記録

#### 8.1 チーム通知

```markdown
# チャット通知（Slack/Teamsなど）

🚀 デプロイ完了通知

環境: prod
バージョン: v0.1.0
実行者: @your-name
完了時刻: 2026-07-15 14:00

変更内容:
- 新規棋譜解析機能追加
- ChromaDB永続化修正

検証結果:
- ✅ ユニットテスト: 通過
- ✅ 統合テスト: 通過
- ✅ E2Eテスト: 通過
- ✅ デプロイ: 成功

次のアクション:
- ChromaDB再構築が必要
- ユーザーへの通知
```

#### 8.2 ドキュメント更新

```bash
# CHANGELOG.md更新
git add CHANGELOG.md
git commit -m "docs: v0.1.0 リリースノート追加"
git push origin main
```

## ロールバック手順

### 緊急ロールバックが必要な場合

#### 1. 前のバージョンへのタグ付け

```bash
# 前の安定版を確認
git tag -l

# 前のバージョンでタグ作成
git tag v0.0.9-rollback
git push origin v0.0.9-rollback
```

#### 2. CDワークフロー実行

- GitHub Actionsで自動デプロイ
- 監視して完了を確認

#### 3. ロールバック検証

```bash
# デプロイされたバージョン確認
databricks bundle validate -t prod --profile shogi

# データ確認
databricks sql execute --profile shogi "
SELECT COUNT(*) as row_count
FROM shogi.shogi_silver.positions
"
```

#### 4. 通知

```markdown
🚨 緊急ロールバック実行

環境: prod
ロールバック先: v0.0.9
実行者: @your-name
理由: [理由を記述]

次のアクション:
- 問題調査
- 修正版の準備
```

## トラブルシューティング

### デプロイ失敗

**症状**: `databricks bundle deploy` が失敗

**原因と対策**:
- **認証エラー**: `databricks auth login --profile shogi` を再実行
- **バンドル検証エラー**: [databricks.yml](cci:7://file:///c:/shogi-kif-rag/databricks.yml:0:0-0:0) の構文を確認
- **リソース競合**: 既存リソースとの競合を確認

```bash
# 詳細エラー確認
databricks bundle deploy -t prod --profile shogi --debug

# バンドル検証
databricks bundle validate -t prod --strict --profile shogi
```

### パイプライン実行失敗

**症状**: デプロイ後のパイプラインが失敗

**原因と対策**:
- **スキーマ不一致**: テーブルスキーマを確認
- **データ不存在**: 入力データを確認
- **権限不足**: サービスプリンシパルの権限を確認

```bash
# event_log確認
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

### E2Eテスト失敗

**症状**: CDワークフロー内のE2Eテストが失敗

**原因と対策**:
- **環境設定ミス**: 環境変数を確認
- **データ不整合**: テストデータを再セットアップ
- **タイムアウト**: パイプライン実行時間を確認

```bash
# ローカルでE2Eテスト再実行
uv run pytest tests/e2e/ -v -s

# 環境変数確認
echo $DATABRICKS_HOST
echo $DATABRICKS_CLIENT_ID
```

## 成功基準

- [ ] すべてのテスト（unit/integration/e2e）が通過
- [ ] バンドル検証がすべての環境で通過
- [ ] CDワークフローが成功
- [ ] デプロイされたリソースが正常に動作
- [ ] データ品質チェックが通過
- [ ] チーム通知が完了
- [ ] ドキュメントが更新

## チェックリスト

### デプロイ前
- [ ] コードレビュー完了
- [ ] ユニットテスト通過
- [ ] 統合テスト通過
- [ ] バンドル検証通過
- [ ] Gitステータスクリーン
- [ ] CHANGELOG更新

### デプロイ中
- [ ] タグ作成・プッシュ
- [ ] CDワークフロー監視
- [ ] エラーログ確認

### デプロイ後
- [ ] リソース確認
- [ ] パイプライン実行
- [ ] データ品質確認
- [ ] E2Eテスト通過
- [ ] チーム通知
- [ ] ドキュメント更新

## 所要時間

- デプロイ前チェック: 15-20分
- タグ付け・プッシュ: 2-3分
- CDワークフロー（dev）: 10-15分
- CDワークフロー（test）: 15-20分
- CDワークフロー（prod）: 10-15分
- デプロイ後検証: 10-15分
- **合計**: 約60-90分

## 関連ドキュメント

- [docs/development.md](../../docs/development.md) - 開発手順全般
- [databricks-dabsスキル](../skills/databricks-dabs/SKILL.md) - バンドル管理
- [databricks-coreスキル](../skills/databricks-core/SKILL.md) - Databricks操作
- [shogi-rag-specificスキル](../skills/shogi-rag-specific/SKILL.md) - プロジェクト固有知識
- [databricks.yml](../../databricks.yml) - バンドル設定