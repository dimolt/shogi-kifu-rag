"""Job実行と統合テスト検証の一括実行スクリプト。

shogi_kif_rag_main_jobを実行し、その後に統合テストを実行を検証する。
"""
import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """コマンドを実行し、成功かどうかを返す。

    Args:
        cmd: 実行するコマンドリスト。
        description: コマンドの説明。

    Returns:
        bool: 成功した場合はTrue、失敗した場合はFalse。
    """
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print(f"Failed: {description}", file=sys.stderr)
        return False

    print(f"Success: {description}")
    return True


def main() -> int:
    """メイン処理。

    Returns:
        int: 終了コード（0: 成功, 1: 失敗）。
    """
    parser = argparse.ArgumentParser(
        description="Run shogi_kif_rag_main_job and execute integration tests"
    )
    parser.add_argument(
        "--target",
        default="dev",
        help="Databricks bundle target (default: dev)",
    )
    parser.add_argument(
        "--profile",
        default="shogi",
        help="Databricks bundle profile (default: shogi)",
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent.parent
    tests_dir = project_root / "tests"

    # Step 1: Job実行
    # databricks CLIコマンドを構築
    databricks_cmd = [
        "databricks",
        "jobs",
        "run-now",
        "--json",
        f'{{"job_id": $(databricks bundle summary --output json -t {args.target} -p {args.profile} | jq -r \'.resources.jobs.shogi_kif_rag_main_job.id\')}}',
    ]

    if not run_command(databricks_cmd, "Execute shogi_kif_rag_main_job"):
        return 1

    # Step 2: 統合テスト実行（uv run pytestを使用）
    test_path = tests_dir / "integration"
    pytest_cmd = [
        "uv",
        "run",
        "pytest",
        str(test_path),
        "-v",
    ]

    if not run_command(pytest_cmd, "Run integration tests"):
        return 1

    print("\n" + "="*60)
    print("All tests completed successfully!")
    print("="*60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
