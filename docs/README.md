
# Python開発環境構築・運用ルール

## 概要

本プロジェクトでは以下の2種類の実行環境を利用する。

| 環境     | 用途                                  |
| ------ | ----------------------------------- |
| local  | ローカルPySparkによるユニットテスト・開発            |
| remote | Databricks Connectを利用したDatabricks実行 |

依存関係は `pyproject.toml` と `uv.lock` を唯一の管理対象とし、各仮想環境はそこから再生成する。

---

# ディレクトリ構成

```text
ShogiApp/
├─ pyproject.toml
├─ uv.lock
├─ requirements-local.txt
├─ requirements-remote.txt
├─ .venv_local/
├─ .venv_remote/
├─ code/
│  ├─ local/
│  ├─ remote/
│  └─ shared/
├─ tests/
├─ infrastructure/
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

local = [
    "pyspark",
]

remote = [
    "databricks-connect>=15.4,<15.5",
    "databricks-dlt",
]

dev = [
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
uv export --group local --group dev -o requirements-local.txt
```

---

## remote

```powershell
uv export --group remote --group dev -o requirements-remote.txt
```

---

# 仮想環境作成

## local

```powershell
uv venv .venv_local --python 3.12
```

pip追加

```powershell
.\.venv_local\Scripts\python.exe -m ensurepip --upgrade
```

依存関係同期

```powershell
uv pip sync requirements-local.txt --python .\.venv_local\Scripts\python.exe
```

有効化

```powershell
.venv_local\Scripts\activate
```

---

## remote

```powershell
uv venv .venv_remote --python 3.12
```

pip追加

```powershell
.\.venv_remote\Scripts\python.exe -m ensurepip --upgrade
```

依存関係同期

```powershell
uv pip sync requirements-remote.txt --python .\.venv_remote\Scripts\python.exe
```

有効化

```powershell
.venv_remote\Scripts\activate
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
uv export --group local --group dev -o requirements-local.txt

uv export --group remote --group dev -o requirements-remote.txt
```

```powershell
uv pip sync requirements-local.txt --python .\.venv_local\Scripts\python.exe

uv pip sync requirements-remote.txt --python .\.venv_remote\Scripts\python.exe
```

---

# ライブラリ一覧確認

現在の環境

```powershell
uv pip list
```

特定環境

```powershell
uv pip list --python .\.venv_local\Scripts\python.exe
```

```powershell
uv pip list --python .\.venv_remote\Scripts\python.exe
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
Remove-Item .venv_local -Recurse -Force
```

```powershell
Remove-Item .venv_remote -Recurse -Force
```

再作成

```powershell
uv venv .venv_local --python 3.12
uv venv .venv_remote --python 3.12
```

```powershell
.\.venv_local\Scripts\python.exe -m ensurepip --upgrade
.\.venv_remote\Scripts\python.exe -m ensurepip --upgrade
```

```powershell
uv pip sync requirements-local.txt --python .\.venv_local\Scripts\python.exe

uv pip sync requirements-remote.txt --python .\.venv_remote\Scripts\python.exe
```

これにより開発環境を完全再現できる。

---

# 運用ルール

* pyproject.toml を依存関係の唯一の定義元とする
* uv.lock を必ずコミットする
* requirements-local.txt は export 結果として管理する
* requirements-remote.txt は export 結果として管理する
* 仮想環境はコミットしない
* local環境で Databricks Connect を利用しない
* remote環境で PySpark単体実行を行わない
* ライブラリ追加時は必ず uv lock を更新する
* 開発者は requirements から環境を再生成できる状態を維持する

この運用なら、将来的に CI/CD や Databricks Asset Bundle を導入してもそのまま拡張できます。
特に「local=PySpark」「remote=Databricks Connect」の分離は、データエンジニアの実務でも保守しやすい構成です。
