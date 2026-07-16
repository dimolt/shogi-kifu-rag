# デプロイフロー詳細

本プロジェクトのデプロイフローは以下の通りです。

## 1. 開発段階

### 環境
- **カタログ**: `shogi_dev`
- **目的**: 機能開発・単体テスト・データ検証

### 実行内容
- **CI（自動）**: 
  - [ci-python-checks.yml](cci:7://file:///c:/shogi-kif-rag/.github/workflows/ci-python-checks.yml:0:0-0:0) で unitテスト、linting、type checking を実行
  - PR作成時に自動実行
- **手動（必要に応じて）**:
  - [ci-integration.yml](cci:7://file:///c:/shogi-kif-rag/.github/workflows/ci-integration.yml:0:0-0:0) で integrationテストを実行
  - dev環境の既存データに対するデータ検証ロジックの確認
  - GitHub Actionsタブから手動実行

### 運用フロー
1. 機能開発を行う
2. PRを作成 → CIが自動実行（unitテスト）
3. 必要に応じて [ci-integration.yml](cci:7://file:///c:/shogi-kif-rag/.github/workflows/ci-integration.yml:0:0-0:0) を手動実行し、dev環境データ検証
4. CIが通過したらmainブランチにマージ

## 2. Test環境デプロイ

### 環境
- **カタログ**: `shogi_test`
- **目的**: 本番デプロイ前の完全検証

### トリガー
```bash
git tag v0.1.0-test
git push origin v0.1.0-test
```

### 自動実行フロー（CD）
1. `deploy-test` ジョブ実行
2. test環境にデプロイ（`databricks bundle deploy -t test`）
3. E2Eテスト実行
   - Silver/Goldパイプラインを起動
   - パイプライン完了まで待機（timeout 900秒）
   - データ品質検証（expectations、データ存在確認）
4. integrationテスト実行
   - test環境データに対する追加のデータ検証
   - スキーマ整合性、行数整合性、null検証

### 手動実行フロー
1. CDが成功したことを確認
2. test環境で手動テストを実施
   - Gradio UIの動作確認
   - データ品質の目視確認
   - その他機能テスト

### 成功条件
- CDジョブが成功すること
- 手動テストで問題がないこと

## 3. Prod環境デプロイ

### 環境
- **カタログ**: `shogi_prod`
- **目的**: 本番環境へのリリース

### トリガー
```bash
git tag v0.1.0
git push origin v0.1.0
```

### 自動実行フロー（CD）
1. `deploy-prod` ジョブ実行
2. prod環境にデプロイ（`databricks bundle deploy -t prod`）

### 前提条件
- test環境での検証が完了していること
- test環境で問題がないことが確認されていること

### 事後確認
1. デプロイが成功したことを確認
2. prod環境で動作確認
3. 本番運用開始

## テストレイヤーと実行タイミング

| テストレイヤー | 実行タイミング | 環境 | 自動/手動 |
|---|---|---|---|
| Layer 1: unit | PR時（CI） | ローカル | 自動 |
| Layer 2: integration | 開発中（必要時） | shogi_dev | 手動 |
| Layer 2: integration | testデプロイ時（CD） | shogi_test | 自動 |
| Layer 3: e2e | testデプロイ時（CD） | shogi_test | 自動 |

## 運用上の注意点

### 開発段階
- unitテストはCIで必ず実行されるため、PRマージ前に品質を担保
- integrationテストは必要に応じて手動実行し、dev環境データ検証を行う
- スキーマ変更を含むPRは、dev環境データ更新後にintegrationテストを実行して確認

### Test環境デプロイ
- test環境で完全な検証を行うため、パイプライン実行〜データ検証まで一気通貫で実行
- 手動テストも含めて、test環境で問題がないことを確認してからprodデプロイへ進む

### Prod環境デプロイ
- prodデプロイはtest環境検証完了後に行う
- prodデプロイ自体はデプロイのみで、追加の自動テストは行わない（test環境での検証が前提）

## トラブルシューティング

### CI失敗時
- unitテスト失敗: コードの修正が必要
- lint/type check失敗: コードスタイルや型の修正が必要

### Integrationテスト失敗時
- dev環境データが古い可能性: パイプラインを再実行してデータ更新
- スキーマ不整合: スキーマ定義を確認

### E2Eテスト失敗時
- パイプライン失敗: パイプラインログを確認し、問題を修正
- データ検証失敗: transformロジックやexpectationsを確認

### CD失敗時
- bundle validate失敗: bundle設定を確認
- deploy失敗: Databricks環境設定を確認