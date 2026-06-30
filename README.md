
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
│  │  └─ gold_table.py
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

### Silver Pipeline (silver_table.py)

- CSVファイルから棋譜データを読み込み
- Silverテーブル（positions）を作成

### Gold Pipeline (gold_table.py)

- Silverテーブルからデータを読み込み
- 特徴量計算（局面特徴量、ゲームサマリー）
- Goldテーブル（position_features, game_summary）を作成

## Python Wheel Tasks

### floodgate.py

- Floodgate APIから棋譜を取得
- CSA形式の棋譜をパース
- floodgate_positionsテーブルに書き込み

### wikipedia.py

- Wikipediaから戦法解説を取得
- joseki_knowledgeテーブルに書き込み
