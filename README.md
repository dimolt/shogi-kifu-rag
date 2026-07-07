# Python開発環境構築・運用ルール

## 概要

本プロジェクトでは以下の2種類のpyproject.dependency-groupsを利用する。

| 環境     | 用途                                  |
| ------ | ----------------------------------- |
| pyspark  | ローカルPySparkによるユニットテスト・開発 |
| dbx | Databricks Connectを利用したDatabricks実行（コア） |
| rag | RAG/ベクトル検索（ChromaDB, sentence-transformers） |
| web | Webスクレイピング/HTTP（requests, beautifulsoup4） |
| ui | UI（Gradio） |
| llm | AI/LLM（Gemini, Groq） |

依存関係は `pyproject.toml` と `uv.lock` を唯一の管理対象とし、各仮想環境はそこから再生成する。
環境切り替え用スクリプト: `switch-env.ps1`

## プロジェクト概要

将棋棋譜解析RAGシステム。以下の機能を提供する。

- **データパイプライン**: Floodgate APIからの棋譜取得、Wikipediaからの戦法知識取得
- **特徴量抽出**: PySpark Pipelineによる局面特徴量の計算
- **RAGチェーン**: ChromaDBによる類似局面検索とLLMによる局面解説生成
- **Notebook UI**: Gradioによる対話型検索インターフェース

---

# ディレクトリ構成

```text
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

---

# Pythonバージョン

```toml
requires-python = ">=3.12,<3.13"
```

Python 3.12 系を利用する。

確認方法

```powershell
python --version
```

---

# 依存関係管理

## pyproject.toml

依存関係はグループで管理する。

```toml
[dependency-groups]

pyspark = [
    "pyspark",
]

dbx = [
    "databricks-connect>=15.4,<15.5",
    "databricks-sdk",
]

rag = [
    "chromadb",
    "sentence-transformers",
]

web = [
    "requests",
    "beautifulsoup4",
]

ui = [
    "gradio",
]

llm = [
    "google-generativeai",
    "groq",
]

devTools = [
    "pytest",
    "ruff",
    "mypy",
    "ipykernel",
]
```

---

## グループの役割

### pyspark

ローカルPySparkによるユニットテスト・開発用。

```text
PySpark
```

を利用する。

Databricks接続は行わない。

---

### dbx

Databricks Connectを利用したDatabricks実行用（コア機能）。

```text
Databricks Connect
Databricks SDK
```

を利用する。

---

### rag

RAG/ベクトル検索用。

```text
ChromaDB
sentence-transformers
```

を利用する。

---

### web

Webスクレイピング/HTTP用。

```text
requests
beautifulsoup4
```

を利用する。

---

### ui

UI用。

```text
Gradio
```

を利用する。

---

### llm

AI/LLM用。

```text
google-generativeai
groq
```

を利用する。

---

### devTools

共通開発ツール。

```text
pytest
ruff
mypy
ipykernel
```

を利用する。


---

# 仮想環境切り替え

単一の `.venv` を使用し、環境切り替え時は再構築します。

## (PySpark

```powershell
.\scripts\switch-env.ps1 pyspark
```

## Databricks Connect

```powershell
.\scripts\switch-env.ps1 dbx
```

このスクリプトは以下を実行します:
- 既存の `.venv` を削除
- 新しい `.venv` を作成
- 指定したグループで `uv sync` を実行

---

# 運用ルール
* 環境切り替えは `switch-env.ps1` を使用する
* 開発者は pyproject.toml から環境を再生成できる状態を維持する

---

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

本プロジェクトのテストは3層構成とし、それぞれ検証対象・実行環境・実行タイミングを分離する。

```text
tests/
├─ conftest.py           # Layer 1（unit）共有フィクスチャ
├─ unit/                 # Layer 1: 単体テスト
│  └─ ...                # src/ の構成をミラーリング
├─ integration/          # Layer 2: 統合テスト
│  ├─ conftest.py        # Databricks Connect経由の共有フィクスチャ
│  ├─ test_silver_pipeline.py
│  ├─ test_gold_pipeline.py
│  └─ test_pipeline_expectations.py
└─ e2e/                  # Layer 3: E2Eテスト
   └─ ...
```

## Layer 1: 単体テスト（unit）

- ローカルPySpark（`local[1]`）で完結し、Databricksへの接続は行わない
- CSVパースロジックや`silver_transforms.py` / `gold_transforms.py`の純粋関数を検証
- `tests/` は `src/` / `databricks/pipelines/` の構成をミラーリングする
- **CIで毎回実行**する

## Layer 2: 統合テスト（integration）

- Databricks Connect経由（`.databrickscfg`の`shogi`プロファイル、`serverless_compute_id = auto`）でUnity Catalog上に実体化されたテーブルへ接続する
- パイプライン自体は**起動しない**。検証対象のテーブル・event_logは、事前に以下いずれかの方法で生成されている必要がある：
  1. CIの定期実行（post-merge scheduled run）
  2. 手動での `databricks bundle run <pipeline_name> -t dev -p shogi`
- 主な検証内容：
  - `test_silver_pipeline.py`: Silverテーブル（`positions`）のスキーマ整合性・連番・sfenチェーン等、単体テストでは検証できないビジネス不変条件
  - `test_gold_pipeline.py`: Goldテーブル（`position_features` / `game_summary`）のスキーマ整合性・行数整合性・null検証
  - `test_pipeline_expectations.py`: `event_log()` TVF経由で`@dp.expect`が実際に発火し`failed_records=0`であることを確認する品質ゲート検証。`silver_pipeline` / `gold_pipeline`はresource keyが分かれているため、`silver_pipeline_id` / `gold_pipeline_id`の2fixtureで個別に検証する
- event_logの鮮度は24時間以内の実行を前提とし、古い場合は該当テストを`skip`する
- **post-merge / 定期実行**（CIでは毎回実行しない）

### 実行前の前提条件

```bash
# 1. devターゲットへのデプロイが完了していること
databricks bundle deploy -t dev -p shogi

# 2. 対象パイプラインが直近24時間以内に実行されていること
databricks bundle run silver_pipeline -t dev -p shogi
databricks bundle run gold_pipeline -t dev -p shogi
```

```bash
# 実行方法
uv run pytest tests/integration/ -v
```

## Layer 3: E2Eテスト（`tests/e2e/`）

DABs devターゲットへの実デプロイ後、Silver/Goldパイプラインを実際に起動し、
完了まで待機したうえでデータ品質・データ存在を検証する。

**前提条件:**

- CDワークフロー（`deploy-dev` ジョブ）内で `databricks bundle deploy -t dev` が
  実行済みであること（E2Eテスト自体はデプロイを行わない）
- `DATABRICKS_HOST` / `DATABRICKS_CLIENT_ID` / `DATABRICKS_CLIENT_SECRET` が
  環境変数として設定済みであること

**実行方法:**

```bash
uv run pytest tests/e2e/ -v
```

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

## Layer 2 vs Layer 3 の使い分け

| 観点 | Layer 2（integration） | Layer 3（e2e） |
|---|---|---|
| 実行トリガー | 手動 / post-mergeまたはscheduled | CD `deploy-dev` ジョブ内（実デプロイ直後） |
| 対象 | 既存データに対するSQL/DataFrameロジックの検証 | 実際のパイプライン起動〜完了までの一気通貫の検証 |
| データ | 既存のdev環境データを使用 | Volumes配置済みデータ + スキーマは毎回クリーン |
| 実行時間 | 秒〜分単位 | パイプライン完了待ちのため数分〜（timeout 900秒） |
| 環境 | devカタログ（テーブルは既存のまま） | devカタログのSilver/Goldスキーマを毎回再作成 |

> **既知の制約:** 現状はdevターゲットを都度クリーンする運用としている。
> 将来的には専用のstg環境を用意し、devとE2E検証用環境を分離することが望ましい。