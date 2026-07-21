#!/usr/bin/env python3
"""Issue内容ファイルを動的に読み込むローダー。

Issue内容ファイルとは、以下4つのモジュールレベル変数を定義したPythonファイルを指す。

    REPO: str
        対象リポジトリ（`owner/repo` 形式）。
    PARENT_ISSUE: int
        親IssueのIssue番号。
    PLAN_REF: str
        各Issue本文の末尾に付与する参照文言。
    ISSUES: list[IssueDefinition]
        作成するIssue定義のリスト（`create_issues.IssueDefinition` を参照）。

新しいIssueセットを登録したい場合は、上記4変数を持つ新規ファイルを作成するだけでよい。
このファイルと `create_issues.py` は変更不要。
"""

import importlib.util
from dataclasses import dataclass
from pathlib import Path

from create_issues import IssueDefinition

REQUIRED_ATTRS = ("REPO", "PARENT_ISSUE", "PLAN_REF", "ISSUES")


@dataclass(frozen=True)
class IssueContent:
    """Issue内容ファイルから読み込んだ内容。

    Attributes:
        repo: 対象リポジトリ（`owner/repo` 形式）。
        parent_issue: 親IssueのIssue番号。
        plan_ref: 各Issue本文の末尾に付与する参照文言。
        issues: 作成するIssue定義のリスト。
    """

    repo: str
    parent_issue: int
    plan_ref: str
    issues: list[IssueDefinition]


def load_issue_content(content_path: str) -> IssueContent:
    """Issue内容ファイルを動的インポートして読み込む。

    Args:
        content_path: Issue内容を定義したPythonファイルのパス。

    Returns:
        読み込んだIssue内容。

    Raises:
        FileNotFoundError: content_path が存在しない場合。
        ValueError: ファイルに必須変数（REPO, PARENT_ISSUE, PLAN_REF, ISSUES）が
            不足している場合。
    """
    path = Path(content_path)
    if not path.is_file():
        raise FileNotFoundError(f"Issue内容ファイルが見つかりません: {content_path}")

    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Issue内容ファイルを読み込めません: {content_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    missing = [attr for attr in REQUIRED_ATTRS if not hasattr(module, attr)]
    if missing:
        raise ValueError(
            f"{content_path} に必須変数が不足しています: {', '.join(missing)}"
        )

    return IssueContent(
        repo=module.REPO,
        parent_issue=module.PARENT_ISSUE,
        plan_ref=module.PLAN_REF,
        issues=module.ISSUES,
    )
