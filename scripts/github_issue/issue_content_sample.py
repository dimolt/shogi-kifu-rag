#!/usr/bin/env python3
"""dimolt/shogi-kifu-rag に Integration Test 拡張計画のIssue内容を定義する。

このファイルは `issue_definitions.load_issue_content()` が読み込む
「Issue内容ファイル」。REPO, PARENT_ISSUE, PLAN_REF, ISSUES の4変数のみを
定義し、登録処理そのものは持たない（登録処理は `create_issues.py` を参照）。

使い方:
    uv run python create_issues.py issue_content_sample.py --dry-run
"""

from create_issues import IssueDefinition

REPO = "dimolt/shogi-kifu-rag"
PARENT_ISSUE = 147

# 各Issueの本文に共通で末尾に付ける、計画ドキュメントへの参照
PLAN_REF = (
    "\n\n---\n"
    "参照: Integration Test 拡張計画（Issue #113 残課題ドキュメント）\n"
)

ISSUES: list[IssueDefinition] = [
    # ============================================================
    # 異常系テスト / Input Data Issues
    # ============================================================
    {
        "title": "[異常系][InputData][Unit] Empty input file handling",
        "labels": ["test", "abnormal"],
        "body": """## 概要
ヘッダーのみ・本文0行のCSVを `build_positions()` に渡した際の挙動を確認する。

## Layer
unit（`tests/unit/dbx_bundle/pipelines/test_silver_transforms.py` に追加）

## 検証方法
`write_analysis_csv()` でヘッダーのみ・本文0行のCSVを生成し `build_positions()` に渡す。

## 期待結果
例外を投げず、0行のDataFrameが返る。スキーマは `get_analysis_schema()` と一致する。
""",
    },
    {
        "title": "[異常系][InputData][Unit] Malformed CSV data handling",
        "labels": ["test", "abnormal"],
        "body": """## 概要
カラム数不足・引用符崩れなど、フォーマットが壊れた行を含むCSVを `build_positions()` に
渡した際の挙動を確認し、期待値として固定する。

## Layer
unit（`tests/unit/dbx_bundle/pipelines/test_silver_transforms.py` に追加）

## 検証方法
カラム数不足の行、引用符崩れの行を含むCSVを生成し `build_positions()` に渡す。

## 期待結果
`spark.read.csv()` は schema 指定 + デフォルト `PERMISSIVE` モードのため、
型不一致は例外ではなく該当カラムが null になる想定。実際の挙動（null化 or 読み飛ばし）を
確認し、テストの期待値として固定する。
""",
    },
    # ============================================================
    # 別Issue化項目
    # ============================================================
    {
        "title": "[異常系][別Issue] Retry logic validation",
        "labels": ["test", "abnormal"],
        "body": """## 概要
現状 `dbx_bundle/resources/workflows/jobs.yml` に `max_retries` 等のリトライ設定が
存在しない。リトライの仕組み自体が未実装のため、まずリトライ機構の要否・設計から
検討する。

## 作業内容
- [ ] リトライ機構の要否を検討（対象タスク: `silver_pipeline` / `gold_pipeline` /
      `floodgate` / `wikipedia`）
- [ ] 必要と判断した場合、`jobs.yml` にリトライ設定を追加
- [ ] リトライ設定追加後、Retry logic validation のテストを実装
      （リトライが実際に発火し、最終的な成功/失敗判定が正しく行われることを確認）
""",
    },
]
