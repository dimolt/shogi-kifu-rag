# プロジェクト概要

将棋棋譜解析RAGシステム。以下の機能を提供する。

- **データパイプライン**: Floodgate APIからの棋譜取得、Wikipediaからの戦法知識取得
- **特徴量抽出**: PySpark Pipelineによる局面特徴量の計算
- **RAGチェーン**: ChromaDBによる類似局面検索とLLMによる局面解説生成
- **Notebook UI**: Gradioによる対話型検索インターフェース

## 開発手順

詳細な開発手順（セットアップ、ワークフロー、トラブルシューティング）は
[docs/development.md](docs/development.md) を参照してください。

## デプロイフロー

詳細なデプロイフローは
[docs/deployment_flow.md](docs/deployment_flow.md) を参照してください。


---

# ディレクトリ構成

```
shogi-kif-rag/
├─ pyproject.toml
├─ uv.lock
├─ .venv/
├─ scripts/
│  ├─ switch-env.ps1
├─ src/
│  └─ shogi_kif_rag/
│     ├─ tasks/        # Python Wheel Tasks
│     │  ├─ floodgate.py
│     │  └─ wikipedia.py
│     ├─ rag/          # RAG共通モジュール
│     │  ├─ llm_client.py
│     │  ├─ retriever.py
│     │  ├─ generator.py
│     │  ├─ secrets.py
│     │  └─ rag.py
│     └─ vector/       # ChromaDBサービス
│        └─ chromadb_service.py
├─ databricks/
│  ├─ pipelines/          # PySpark Pipelines
│  │  ├─ silver_table.py
│  │  ├─ silver_transforms.py
│  │  ├─ gold_table.py
│  │  └─ gold_transforms.py
│  ├─ notebooks/          # Databricks Notebooks
│  │  └─ ntb_ui_demo.py
│  └─ resources/
│     └─ workflows/
│        ├─ jobs.yml
│        └─ sdp_pipeline.yml
├─ tests/
├─ docs/
```


# RAGシステム

## 概要

RAG（Retrieval-Augmented Generation）システムは、ChromaDBによる類似局面検索とLLMによる局面解説生成を組み合わせたシステムです。

## アーキテクチャ

```
ユーザー質問
    ↓
Gradio UI (Notebook)
    ↓
RAG共通モジュール
    ├─ retriever.py: ChromaDBから類似局面検索
    ├─ generator.py: LLMによる回答生成
    ├─ llm_client.py: LLMクライアント（Gemini/Groq）
    └─ secrets.py: Databricks SecretsからAPIキー取得
    ↓
回答 + 参照ドキュメント
```

## モジュール構成

### src/shogi_kif_rag/rag/

- **llm_client.py**: LLMクライアント（Gemini 2.5 Flash with Groq Llama 3.3 70B fallback）
- **retriever.py**: ChromaDBから類似局面検索
- **generator.py**: LLMによる回答生成
- **secrets.py**: Databricks SecretsからAPIキー取得
- **rag.py**: RAGクエリ統合関数

## Databricks Secretsの設定

### スコープ作成

```bash
databricks secrets create-scope llm
```

### シークレット設定

```bash
databricks secrets put-secret llm gemini_api_key
databricks secrets put-secret llm groq_api_key
```

### ローカル実行時

ローカル実行時は環境変数からAPIキーを取得します。

```bash
export LLM_GEMINI_API_KEY=your_gemini_api_key
export LLM_GROQ_API_KEY=your_groq_api_key
```

## Gradio UI (Notebook)

### 実行方法

Databricks Notebookで `ntb_ui_demo.py` を開いて実行します。

### 機能

- 検索対象コレクション選択（positions, floodgate_positions, joseki_knowledge）
- 取得するドキュメント数設定
- 質問入力と回答表示
- 参照ドキュメントの表示

---

# データパイプライン

## 概要

データパイプラインはPySpark Pipelineを使用して、SilverテーブルとGoldテーブルを作成します。

## Pipeline構成

### アーキテクチャ

パイプライン定義とtransformロジックを分離し、whlパッケージ依存を回避しています。

- **パイプライン定義** (`*_table.py`): Lakeflowパイプラインのテーブル定義
- **Transformロジック** (`*_transforms.py`): 純粋関数によるデータ変換処理

### Silver Pipeline

- **silver_table.py**: パイプライン定義
- **silver_transforms.py**: Transformロジック
  - CSVファイルから棋譜データを読み込み
  - Silverテーブル（positions）を作成

### Gold Pipeline

- **gold_table.py**: パイプライン定義
- **gold_transforms.py**: Transformロジック
  - Silverテーブルからデータを読み込み
  - 特徴量計算（局面特徴量、ゲームサマリー）
  - Goldテーブル（position_features, game_summary）を作成

## デプロイ

```bash
databricks bundle deploy
```

Pipeline設定（`sdp_pipeline.yml`）にtransformファイルを含めることで、whl依存なしでデプロイ可能です。

## 残課題

### whl依存の問題

現在の実装ではtransformロジックがPySpark標準機能のみを使用しているためwhl依存は発生していませんが、将来的に以下のケースでwhl依存が再発する可能性があります：

- transformロジックから `src` モジュールを参照する場合
- カスタムライブラリを利用する場合

その場合は、参照するモジュールを `databricks/pipelines/` 内に移動するか、別の依存解決方法を検討する必要があります。

## Python Wheel Tasks

### floodgate.py

- Floodgate APIから棋譜を取得
- CSA形式の棋譜をパース
- floodgate_positionsテーブルに書き込み

### wikipedia.py

- Wikipediaから戦法解説を取得
- joseki_knowledgeテーブルに書き込み

---

# テスト戦略

## 概要

本プロジェクトのテストは4層構成とし、それぞれ検証対象・実行環境・実行タイミングを分離する。

```text
tests/
├─ conftest.py           # Layer 1（unit）共有フィクスチャ
├─ unit/                 # Layer 1: 単体テスト
│  └─ ...                # src/ の構成をミラーリング
├─ integration/          # Layer 2: 統合テスト（データ検証のみ）
│  ├─ conftest.py        # Databricks Connect経由の共有フィクスチャ
│  ├─ test_silver_tables.py
│  ├─ test_gold_tables.py
│  └─ test_expectations_pipeline.py
├─ integration-exec/     # Layer 2.5: 統合テスト（Job/パイプライン実行検証）
│  ├─ conftest.py        # Job実行フィクスチャ
│  ├─ test_execution_main_job.py
│  ├─ test_execution_fooldgante_task.py
│  └─ test_execution_wikipedia.py
└─ e2e/                  # Layer 3: E2Eテスト
   └─ ...
```

## Layer 1: 単体テスト（unit）

- ローカルPySpark（`local[1]`）で完結し、Databricksへの接続は行わない
- CSVパースロジックや`silver_transforms.py` / `gold_transforms.py`の純粋関数を検証
- `tests/` は `src/` / `databricks/pipelines/` の構成をミラーリングする
- **CIで毎回実行**する

## Layer 2: 統合テスト（integration）

- Databricks Connect経由でUnity Catalog上に実体化されたテーブルへ接続する
- **使用カタログ**: 環境変数 `TEST_CATALOG` で指定（test環境では `shogi_test`、dev環境では `shogi_dev`）
- **パイプライン/Jobは起動しない**。既存データに対するSQL/DataFrameロジックの検証のみを行う。
- 主な検証内容：
  - `test_silver_tables.py`: Silverテーブル（`positions`）のスキーマ整合性・連番・sfenチェーン等、単体テストでは検証できないビジネス不変条件
  - `test_gold_tables.py`: Goldテーブル（`position_features` / `game_summary`）のスキーマ整合性・行数整合性・null検証
  - `test_expectations_pipeline.py`: `event_log()` TVF経由で`@dp.expect`が実際に発火し`failed_records=0`であることを確認する品質ゲート検証。`silver_pipeline` / `gold_pipeline`はresource keyが分かれているため、[silver_pipeline_id](cci:1://file:///c:/shogi-kif-rag/tests/conftest.py:91:0-103:79) / [gold_pipeline_id](cci:1://file:///c:/shogi-kif-rag/tests/conftest.py:106:0-118:77)の2fixtureで個別に検証する
- **実行タイミング**:
  - test環境: CD `deploy-test` ジョブ内でe2eテスト後に自動実行
  - dev環境: 手動実行（`ci-integration.yml` ワークフロー）

## Layer 2.5: 統合テスト（integration-exec）

Job/パイプラインの起動〜完了を検証するテストレイヤー。
Layer 2がデータ検証のみであるのに対し、本レイヤーは実際の実行を検証する。

- Databricks SDK経由でJobを起動し、完了まで待機
- **使用カタログ**: `shogi_dev`（固定）
- 主な検証内容：
  - `test_execution_main_job.py`: Job全体の実行検証（全タスクがSUCCESSで完了すること）
  - `test_execution_fooldgante_task.py`: floodgateタスクの実行検証
  - `test_execution_wikipedia.py`: wikipediaタスクの実行検証
- **注意**: E2Eテスト（Layer 3）がパイプライン実行を含むため、本レイヤーは基本的に使用しない。dev環境でのJob実行検証が必要な場合にのみ手動実行する

## Layer 3: E2Eテスト（`tests/e2e/`）

DABs testターゲットへの実デプロイ後、Silver/Goldパイプラインを実際に起動し、
完了まで待機したうえでデータ品質・データ存在を検証する。

**前提条件:**

- CDワークフロー（`deploy-test` ジョブ）内で `databricks bundle deploy -t test` が
  実行済みであること（E2Eテスト自体はデプロイを行わない）
- `DATABRICKS_HOST` / `DATABRICKS_CLIENT_ID` / `DATABRICKS_CLIENT_SECRET` が
  環境変数として設定済みであること
- **使用カタログ**: `shogi_test`（固定）

**フロー:**

1. Silver/Goldスキーマをdrop & recreate（`clean_schemas` フィクスチャ、autouse）
   - テーブル・MVはLakeflowパイプライン実行時に自動作成されるため、
     ここではスキーマの器のみをクリーンにする
   - Bronze層の取り込みはフルスキャン方式（チェックポイントなし）のため、
     チェックポイントの個別クリーンアップは不要
2. Silverパイプラインを起動し、`COMPLETED` になるまでポーリング待機
   （interval 15秒、timeout 900秒）
3. Silver完了後、Goldパイプラインを起動し、同様に完了待機
4. `event_log()` TVFベースの `assert_expectations_pass()` で
   Silver/Gold双方のexpectations（failed_records=0）を確認
5. Silver/Goldの主要テーブルにデータが存在することを最小限確認

**失敗時の挙動:**

パイプライン更新が `FAILED` / `CANCELED` で終了した場合、`event_log()` から
ERRORレベルのイベントメッセージを抽出し、テスト失敗メッセージに含める。
これによりCIログのみでパイプライン内部の失敗原因まで追跡できる。

## 各レイヤーの使い分け

| 観点 | Layer 2（integration） | Layer 2.5（integration-exec） | Layer 3（e2e） |
|---|---|---|---|
| 実行トリガー | test: CD自動 / dev: 手動 | 基本的に使用しない（dev環境でのJob実行検証が必要な場合のみ手動） | CD `deploy-test` ジョブ内（実デプロイ直後） |
| 対象 | 既存データに対するSQL/DataFrameロジックの検証 | Job/パイプラインの起動〜完了検証 | 実際のパイプライン起動〜完了までの一気通貫の検証 |
| パイプライン起動 | しない | する | する |
| データ | 既存データを使用 | 既存のdev環境データを使用 | Volumes配置済みデータ + スキーマは毎回クリーン |
| 実行時間 | 秒〜分単位 | 数分〜（Job完了待ち） | 数分〜（パイプライン完了待機、timeout 900秒） |
| 環境 | test: shogi_test / dev: shogi_dev | shogi_dev | shogi_test |

## デプロイフロー

本プロジェクトのデプロイフローは以下の通り：

### 1. 開発段階
- **環境**: shogi_dev
- **CI**: unitテスト（`ci-python-checks.yml`）
- **手動**: integrationテスト（`ci-integration.yml`）が必要に応じて実行

### 2. Test環境デプロイ
- **トリガー**: `v*.*.*-test` タグ作成
- **環境**: shogi_test
- **フロー**:
  1. `deploy-test` ジョブ実行
  2. test環境にデプロイ
  3. E2Eテスト実行（パイプライン起動〜完了待機）
  4. integrationテスト実行（データ検証）
- **手動**: その他最終テスト

### 3. Prod環境デプロイ
- **トリガー**: `v*.*.*` タグ作成
- **環境**: shogi_prod
- **フロー**:
  1. `deploy-prod` ジョブ実行
  2. prod環境にデプロイ
- **前提**: test環境での検証が完了していること