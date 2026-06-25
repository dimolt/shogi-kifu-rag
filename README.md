
# Python開発環境構築・運用ルール

## 概要

本プロジェクトでは以下の2種類の実行環境を利用する。

| 環境     | 用途                                  |
| ------ | ----------------------------------- |
| local  | ローカルPySparkによるユニットテスト・開発            |
| remote | Databricks Connectを利用したDatabricks実行 |

依存関係は `pyproject.toml` と `uv.lock` を唯一の管理対象とし、各仮想環境はそこから再生成する。

## プロジェクト概要

将棋棋譜解析RAGシステム。以下の機能を提供する。

- **データパイプライン**: Floodgate APIからの棋譜取得、Wikipediaからの戦法知識取得
- **特徴量抽出**: PySpark Pipelineによる局面特徴量の計算
- **RAGチェーン**: ChromaDBによる類似局面検索とLLMによる局面解説生成
- **Notebook UI**: Gradioによる対話型検索インターフェース

---

# ディレクトリ構成

```text
ShogiApp/
├─ pyproject.toml
├─ uv.lock
├─ requirements-pyspark.txt
├─ requirements-dbx.txt
├─ .venv_pyspark/
├─ .venv_dbx/
├─ code/
│  ├─ local/
│  ├─ remote/
│  │  ├─ src/
│  │  │  └─ shogi_app/
│  │  │     ├─ jobs/         # Python Wheel Tasks
│  │  │     │  ├─ floodgate.py
│  │  │     │  ├─ wikipedia.py
│  │  │     │  └─ chromadb.py
│  │  │     └─ rag/          # RAG共通モジュール
│  │  │        ├─ llm_client.py
│  │  │        ├─ retriever.py
│  │  │        ├─ generator.py
│  │  │        ├─ secrets.py
│  │  │        └─ rag.py
│  │  ├─ pipelines/          # PySpark Pipelines
│  │  │  ├─ silver_table.py
│  │  │  └─ gold_table.py
│  │  └─ notebooks/          # Databricks Notebooks
│  │     ├─ step7_rag_chain.ipynb
│  │     └─ step8_gradio_ui.ipynb
│  └─ shared/
├─ tests/
├─ infrastructure/
│  └─ resources/
│     └─ workflows/
│        ├─ jobs.yml
│        ├─ sdp_pipeline.yml
│        └─ data_pipeline.yml
├─ docs/
└─ data/
```

---

# 採用方針

## なぜ uv を採用するのか

uv を採用する理由は以下の通り。

* Python環境構築が高速
* lockファイルによる再現性が高い
* pip互換コマンドを提供
* Databricks公式でも利用例が増えている
* pyproject.toml を中心に依存関係を管理できる

---

## なぜ pyenv + requirements.txt ではないのか

pyenv は

* Pythonバージョン管理

を目的とするツールであり、

* パッケージ管理
* 依存関係管理
* lock管理

は提供しない。

一方 uv は

* Pythonバージョン管理
* 仮想環境管理
* パッケージ管理
* lock管理

を統合している。

そのため本プロジェクトでは uv を利用する。

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
    "databricks-dlt",
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

### local

ローカル実行用。

```text
PySpark
```

を利用する。

Databricks接続は行わない。

---

### remote

Databricks実行用。

```text
Databricks Connect
Databricks DLT
```

を利用する。

---

### dev

共通開発ツール。

```text
pytest
ruff
mypy
ipykernel
```

を利用する。

---

# lockファイル更新

依存関係を変更した場合

```powershell
uv lock
```

を実行する。

---

# requirements生成

## local

```powershell
uv export --group pyspark --group devTools -o requirements-pyspark.txt
```

---

## remote

```powershell
uv export --group dbx --group devTools -o requirements-dbx.txt
```

---

# 仮想環境作成

## local

```powershell
uv venv .venv_pyspark --python 3.12
```

pip追加

```powershell
.\.venv_pyspark\Scripts\python.exe -m ensurepip --upgrade
```

依存関係同期

```powershell
uv pip sync requirements-pyspark.txt --python .\.venv_pyspark\Scripts\python.exe
```

有効化

```powershell
.venv_pyspark\Scripts\activate
```

---

## remote

```powershell
uv venv .venv_dbx --python 3.12
```

pip追加

```powershell
.\.venv_dbx\Scripts\python.exe -m ensurepip --upgrade
```

依存関係同期

```powershell
uv pip sync requirements-dbx.txt --python .\.venv_dbx\Scripts\python.exe
```

有効化

```powershell
.venv_dbx\Scripts\activate
```

---

# ライブラリ追加手順

例: pytest追加

```toml
[dependency-groups]

dev = [
    "pytest",
]
```

追加後

```powershell
uv lock
```

```powershell
uv export --group pyspark --group devTools -o requirements-pyspark.txt

uv export --group dbx --group devTools -o requirements-dbx.txt
```

```powershell
uv pip sync requirements-pyspark.txt --python .\.venv_pyspark\Scripts\python.exe

uv pip sync requirements-dbx.txt --python .\.venv_dbx\Scripts\python.exe
```

---

# ライブラリ一覧確認

現在の環境

```powershell
uv pip list
```

特定環境

```powershell
uv pip list --python .\.venv_pyspark\Scripts\python.exe
```

```powershell
uv pip list --python .\.venv_dbx\Scripts\python.exe
```

---

# テスト実行

local環境を有効化後

```powershell
pytest
```

---

# 環境再作成

仮想環境削除

```powershell
Remove-Item .venv_pyspark -Recurse -Force
```

```powershell
Remove-Item .venv_dbx -Recurse -Force
```

再作成

```powershell
uv venv .venv_pyspark --python 3.12
uv venv .venv_dbx --python 3.12
```

```powershell
.\.venv_pyspark\Scripts\python.exe -m ensurepip --upgrade
.\.venv_dbx\Scripts\python.exe -m ensurepip --upgrade
```

```powershell
uv pip sync requirements-pyspark.txt --python .\.venv_pyspark\Scripts\python.exe

uv pip sync requirements-dbx.txt --python .\.venv_dbx\Scripts\python.exe
```

これにより開発環境を完全再現できる。

---

# 運用ルール

* pyproject.toml を依存関係の唯一の定義元とする
* uv.lock を必ずコミットする
* requirements-pyspark.txt は export 結果として管理する
* requirements-dbx.txt は export 結果として管理する
* 仮想環境はコミットしない
* local環境で Databricks Connect を利用しない
* remote環境で PySpark単体実行を行わない
* ライブラリ追加時は必ず uv lock を更新する
* 開発者は requirements から環境を再生成できる状態を維持する

この運用なら、将来的に CI/CD や Databricks Asset Bundle を導入してもそのまま拡張できます。
特に「local=PySpark」「remote=Databricks Connect」の分離は、データエンジニアの実務でも保守しやすい構成です。

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

### code/remote/src/shogi_app/rag/

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

Databricks Notebookで `step8_gradio_ui.ipynb` を開いて実行します。

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

### chromadb.py

- Deltaテーブルからデータを読み込み
- ChromaDBベクトルストアを構築

---

# Databricks Asset Bundle

## デプロイ

```bash
databricks bundle deploy
```

## ジョブ実行

```bash
databricks bundle run shogi_kif_rag_main_job
```
