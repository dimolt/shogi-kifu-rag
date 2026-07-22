---
name: python-coding
description: |
  Pythonコードを書く・レビューする・修正するすべての場面で必ず参照するコーディング規約。
  新規コード生成時、既存コードの修正・リファクタリング時、コードレビューのフィードバック時に適用する。
  Databricksパイプライン、pytest、汎用Pythonスクリプトが主な対象。
  ユーザーがPythonコードの生成・修正・レビューを依頼した場合は常にこのスキルを使うこと。
---

# Python コーディング規約

ベース: **Google Python Style Guide** + プロジェクト固有ルール
対象: Databricksパイプライン / pytest / 汎用Pythonスクリプト
docstring言語: **日本語**

このファイルは規約全体の目次。詳細は責務ごとに `references/` へ分割されているので、該当する作業をする際に読み込むこと。すべてを毎回読む必要はない。

---

## リファレンス一覧（責務単位）

| ファイル | 内容 | 読むタイミング |
|---|---|---|
| `references/naming.md` | 変数・関数・クラス・定数の命名規則 | 命名で迷ったとき、レビュー時 |
| `references/type_hints.md` | 型ヒントの書き方（`X \| None`, TypedDict等） | 関数シグネチャを書くとき |
| `references/docstring.md` | Google Style docstring（日本語） | 関数・クラスにdocstringを書くとき |
| `references/error_handling.md` | bare except禁止、カスタム例外設計 | try/except や例外クラスを書くとき |
| `references/imports.md` | isortベースのimport順序 | importを整理するとき |
| `references/style_misc.md` | 行長・クォート・print禁止・マジックナンバー等 | 全般的なスタイルチェック時 |
| `references/databricks.md` | Spark/Delta Table固有の規約 | Databricksパイプラインを書くとき |
| `references/testing.md` | pytestのテスト命名・AAA・フィクスチャ・モック | テストコードを書くとき |

---

## クイックリファレンス（チェックリスト）

コードを書いたら以下を確認:

- [ ] 全関数に型ヒントがある（`references/type_hints.md`）
- [ ] docstringが日本語で書かれている（`references/docstring.md`）
- [ ] `bare except` がない（`references/error_handling.md`）
- [ ] カスタム例外を使っている（組み込み以外）（`references/error_handling.md`）
- [ ] import が3グループに整理されている（`references/imports.md`）
- [ ] bool変数に `is_` / `has_` プレフィックスがある（`references/naming.md`）
- [ ] マジックナンバーが定数化されている（`references/style_misc.md`）
- [ ] （Databricksコードの場合）`references/databricks.md` のルールに準拠している
- [ ] （テストコードの場合）`references/testing.md` のルールに準拠している
