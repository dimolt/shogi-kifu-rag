#!/usr/bin/env python3
"""GitHub Issueを一括作成する再利用可能なスクリプト。

具体的なIssue内容（REPO, PARENT_ISSUE, PLAN_REF, ISSUES）は、このスクリプトの
引数で指定するPythonファイルに定義する。登録したいIssue内容ごとに新しいファイルを
作成し、このスクリプトと `issue_definitions.py` は変更せずに使い回す。

Issue内容ファイルが満たすべきインターフェースは `issue_definitions.py` を参照。

前提:
    - `gh` CLI v2.94.0 以降がインストール済み・認証済みであること（`gh auth login`）
      （`--parent` フラグは2026年6月リリースのv2.94.0で追加されたサブIssue機能を利用）
    - リポジトリへの write 権限があること
    - Issue内容ファイルで指定した親Issueが対象リポジトリに存在すること

使い方:
    python3 create_issues.py <Issue内容ファイル>            # 実際に作成する
    python3 create_issues.py <Issue内容ファイル> --dry-run  # 内容確認のみ（作成しない）

例:
    python3 create_issues.py issue_content_integration_test_plan.py --dry-run
"""

import argparse
import subprocess
import sys
from typing import TypedDict


class IssueDefinition(TypedDict, total=False):
    """1件のIssue定義。

    Attributes:
        title: Issueのタイトル。
        labels: 付与するラベルのリスト。省略時は空リスト扱い。
        body: Issue本文（Markdown）。
    """

    title: str
    labels: list[str]
    body: str


def build_gh_command(
    repo: str, parent_issue: int, title: str, body: str, labels: list[str]
) -> list[str]:
    """`gh issue create` コマンドを組み立てる。

    Args:
        repo: 対象リポジトリ（`owner/repo` 形式）。
        parent_issue: 親IssueのIssue番号。
        title: Issueタイトル。
        body: Issue本文。
        labels: 付与するラベルのリスト。

    Returns:
        `subprocess.run()` にそのまま渡せるコマンドのリスト。
    """
    cmd = [
        "gh", "issue", "create",
        "--repo", repo,
        "--title", title,
        "--body", body,
        "--parent", str(parent_issue),
    ]
    for label in labels:
        cmd += ["--label", label]
    return cmd


def create_issue(
    repo: str, parent_issue: int, title: str, body: str, labels: list[str]
) -> tuple[bool, str]:
    """`gh` CLI経由でIssueを1件作成する。

    Args:
        repo: 対象リポジトリ（`owner/repo` 形式）。
        parent_issue: 親IssueのIssue番号。
        title: Issueタイトル。
        body: Issue本文。
        labels: 付与するラベルのリスト。

    Returns:
        (成功したか, 標準出力または標準エラーの内容) のタプル。
    """
    cmd = build_gh_command(repo, parent_issue, title, body, labels)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False, result.stderr.strip()
    return True, result.stdout.strip()


def register_issues(
    repo: str,
    parent_issue: int,
    issues: list[IssueDefinition],
    plan_ref: str = "",
    is_dry_run: bool = False,
) -> int:
    """複数のIssueをまとめて登録する。

    Args:
        repo: 対象リポジトリ（`owner/repo` 形式）。
        parent_issue: 親IssueのIssue番号。
        issues: 作成するIssue定義のリスト。
        plan_ref: 各Issue本文の末尾に付与する参照文言。
        is_dry_run: Trueの場合、実際には作成せずタイトル一覧のみ表示する。

    Returns:
        作成に失敗したIssueの件数。
    """
    print(f"合計 {len(issues)} 件のIssueを {repo} に作成します。")

    failure_count = 0
    for i, issue in enumerate(issues, start=1):
        title = issue["title"]
        body = issue["body"].strip() + plan_ref
        labels = issue.get("labels", [])

        if is_dry_run:
            print(f"[{i}/{len(issues)}] (dry-run) {title}")
            continue

        print(f"[{i}/{len(issues)}] Creating: {title}")
        is_success, message = create_issue(repo, parent_issue, title, body, labels)
        if is_success:
            print(f"  -> {message}")
        else:
            failure_count += 1
            print(f"  !! 失敗: {message}", file=sys.stderr)

    return failure_count


def main() -> int:
    """CLIエントリポイント。引数で指定されたIssue内容ファイルを登録する。"""
    from issue_definitions import load_issue_content

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "content_path",
        help=(
            "Issue内容（REPO, PARENT_ISSUE, PLAN_REF, ISSUES）を定義した"
            "Pythonファイルのパス"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="作成せず、タイトル一覧のみ表示する",
    )
    args = parser.parse_args()

    content = load_issue_content(args.content_path)
    failure_count = register_issues(
        content.repo, content.parent_issue, content.issues, content.plan_ref,
        args.dry_run,
    )
    return 1 if failure_count > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
