# 開発手順ガイド

## 新規開発者向けセットアップ

### 0. 前提
- windows 環境でのセットアップ手順
- コマンド、バッチがpowerShell用。適宜、環境に合わせて読み換えて

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-org/shogi-kif-rag.git
cd shogi-kif-rag
```

### 2. Python環境の確認

Python 3.12系がインストールされていることを確認

```powershell
python --version  # Python 3.12.x
```

### 3. 仮想環境の構築

```powershell
# PySpark環境（ローカル開発用）
.\scripts\switch-env.ps1 pyspark

# Databricks環境（Databricks接続用）
.\scripts\switch-env.ps1 dbx
```

### 4. Pre-commitフックの有効化

```bash
uv run pre-commit install
```

### 5. 環境変数の設定

`.env`ファイルを作成し、必要な環境変数を設定

```bash
# Databricks認証設定
DATABRICKS_CONFIG_PROFILE=shogi

# やねうら王エンジン設定
YANEURAOU_PATH="C:\Program Files (x86)\ShogiGUI\Yaneura\YaneuraOu_NNUE-tournament-clang++-avx2.exe"
YANEURAOU_OPTIONS=EvalDir "C:\Program Files (x86)\ShogiGUI\Yaneura\eval"
ANALYSIS_DEPTH=20
ANALYSIS_NODES=1000000
```
- やねうら王 のローカル環境構築は必須ではない
- やねうら王 は棋譜解析用のエンジン、Databricks側にエンジンを載せることができないため、ローカルで実行する
- 解析済みのファイルは ./data/output に配置している

環境変数を有効化するには、以下のいずれかの方法を使用してください：

**PowerShell:**
```powershell
Get-Content .env | ForEach-Object { if ($_ -match '^([^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
```

**または手動で設定:**
```powershell
$env:DATABRICKS_CONFIG_PROFILE="shogi"
```

## 開発ワークフロー

### 1. ブランチの作成

```bash
git checkout -b feature/機能名
# または
git checkout -b fix/バグ修正内容
```

### 2. 開発とテスト

```bash
# コード変更後、ローカルでテスト実行
uv run pytest tests/unit -v

# Lintと型チェック
uv run ruff check .
uv run ruff format .
uv run mypy src/
```

### 3. コミット

Pre-commitフックが自動で実行され、問題があればコミットがブロックされます

```bash
git add .
git commit -m "feat: 機能の説明"
```

### 4. プッシュとPR作成

```bash
git push origin feature/機能名
```

GitHubでPRを作成し、CIチェックが通るのを待ちます

### 5. マージ

CIチェックが通ったら、mainブランチにマージします

## 環境切り替え

### PySpark環境（ローカル開発）

```powershell
.\scripts\switch-env.ps1 pyspark
```

用途:
- ユニットテスト実行
- ローカルでのデータ処理
- PySpark Pipelineの開発

### Databricks環境

```powershell
.\scripts\switch-env.ps1 dbx
```

用途:
- Databricks Connect経由の開発
- 統合テスト実行
- デプロイ作業

## テスト実行

### ユニットテスト

```bash
uv run pytest tests/unit -v
```

### 統合テスト

- 事前にデプロイが必要
- 統合テストでは `shogi_dev` カタログを使用します。

```bash
# 環境変数を設定して実行（推奨）
$env:TEST_CATALOG = "shogi_dev"
uv run pytest tests/integration -v

# または .env ファイルに TEST_CATALOG=shogi_dev を設定
```

### E2Eテスト
- 事前にデプロイが必要
- E2Eテストでは `shogi_test` カタログを使用します。

```bash
# 環境変数を設定して実行（推奨）
$env:TEST_CATALOG = "shogi_test"
uv run pytest tests/e2e/ -v

# または .env ファイルに TEST_CATALOG=shogi_test を設定
```

### テストカタログの運用ルール

- **integration テスト**: `shogi_dev` カタログを使用
- **e2e テスト**: `shogi_test` カタログを使用
- 環境変数 `TEST_CATALOG` でカタログ名を指定
- 未設定時のデフォルト値は `shogi_dev`
```

## デプロイ手順

### dev環境へのデプロイ

mainブランチにマージすると自動でデプロイされます

### test/prod環境へのデプロイ

```bash
# test環境
git tag v0.1.0-test
git push origin v0.1.0-test

# prod環境
git tag v0.1.0
git push origin v0.1.0
```
- tag push で自動デプロイされます
- tagのバージョンは適宜アップ

## トラブルシューティング

### Pre-commitフックが失敗する場合

```bash
# 手動で実行して詳細を確認
uv run pre-commit run --all-files
```

### 依存関係の問題

```bash
# 仮想環境を再構築
.\scripts\switch-env.ps1 pyspark  # または dbx
```

### Databricks接続エラー

```bash
# 認証設定を確認
databricks auth login --profile shogi
```

### テスト実行時のエラー

```bash
# 特定のテストのみ実行して詳細を確認
uv run pytest tests/unit/test_specific.py -v

# デバッグモードで実行
uv run pytest tests/unit -v -s
```

## コーディング規約

### 自動フォーマット

```bash
uv run ruff format .
```

### Lintチェック

```bash
uv run ruff check .
```

### 型チェック

```bash
uv run mypy src/
```

### コミットメッセージ規約

Conventional Commits形式を使用します：

- `feat:` 新機能
- `fix:` バグ修正
- `refactor:` リファクタリング
- `docs:` ドキュメント更新
- `test:` テスト追加・修正
- `chore:` ビルドプロセスやツールの変更

例：
```bash
git commit -m "feat: ChromaDBの永続化機能を追加"
git commit -m "fix: Wikipedia APIのレート制限対応"
git commit -m "docs: 開発手順ガイドを追加"
```

## 運用ルール

- 環境切り替えは [switch-env.ps1](cci:7://file:///c:/shogi-kif-rag/scripts/switch-env.ps1:0:0-0:0) を使用する
- 開発者は pyproject.toml から環境を再生成できる状態を維持する
- コミット前に必ずローカルテストを実行する
- PR作成時にCIチェックがすべて通ることを確認する
- mainブランチへの直接コミットは避ける（緊急時を除く）

## 依存関係管理

### ライブラリの追加

```bash
# 特定のグループに追加
uv add --group pyspark ライブラリ名
uv add --group dbx ライブラリ名
uv add --group rag ライブラリ名

# 複数のグループに追加
uv add --group pyspark --group devTools ライブラリ名
```

### 依存関係の確認

```bash
# 依存関係ツリーを表示
uv pip tree

# ロックファイルの更新
uv lock
```

## 参考資料

- プロジェクト仕様書: [docs/spec/shogi_kifu_rag_spec.md](spec/shogi_kifu_rag_spec.md)
- README: [../README.md](../README.md)
- テスト戦略詳細: READMEの「テスト戦略」セクションを参照
```