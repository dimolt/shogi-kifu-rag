"""Lakeflow Declarative Pipeline の `@dp.expect` 検証共通ロジック。

`event_log()` TVF を用いて Silver/Gold パイプラインの expectations 結果を取得し、
failed_records が 0 であることを確認する。integration層（Layer 2）と e2e層（Layer 3）の
両方から参照される。
"""

from pyspark.sql import DataFrame, SparkSession

# Silver層で定義されている expectations 一覧。
# キー: テーブル名、値: そのテーブルに設定された expectation 名のセット。
SILVER_EXPECTATIONS: dict[str, set[str]] = {
    "positions": {"valid_game_id", "valid_move_number", "valid_player"},
}

# Gold層で定義されている expectations 一覧。
GOLD_EXPECTATIONS: dict[str, set[str]] = {
    "position_features": {"valid_move_quality"},
    "game_summary": {"final_score_not_null", "valid_players"},
}


def _get_latest_expectations_df(spark: SparkSession, pipeline_id: str) -> DataFrame:
    """指定パイプラインの最新updateにおけるexpectations結果を取得する。

    `event_log()` の `details` 列はSTRING型でJSON文字列を保持しているため、
    `details:path` のコロン記法だけではARRAY型にならず `explode()` に直接渡せない
    （`DATATYPE_MISMATCH.UNEXPECTED_INPUT_TYPE` になる）。そのため
    `from_json()` で明示的にスキーマを指定して配列型へキャストしてから展開する。

    実機検証済み（2026-07-07、pipeline_id=f3a193ea-...）:
        `expectations` 配列の各要素は `name` / `dataset` / `passed_records` /
        `failed_records` の4フィールドを持ち、`dataset` は展開後の各要素自身が
        個別に保持している（配列の0番目要素で代表させる必要はない）。
        `dataset` は `catalog.schema.table` 形式のFQNで返る
        （例: `shogi.shogi_silver.positions`）ため、末尾のテーブル名部分のみを
        抽出するsplit処理は引き続き必要。

    Args:
        spark: SparkSession。
        pipeline_id: 対象パイプラインのID。

    Returns:
        `dataset`（テーブル名のみ）, `name`, `passed_records`, `failed_records`
        列を持つDataFrame。
    """
    expectation_schema = (
        "array<struct<name:string,dataset:string,passed_records:long,failed_records:long>>"
    )
    return spark.sql(f"""
        SELECT
            split(expectation.dataset, '\\\\.')[
                size(split(expectation.dataset, '\\\\.')) - 1
            ] AS dataset,
            expectation.name AS name,
            expectation.passed_records AS passed_records,
            expectation.failed_records AS failed_records
        FROM event_log('{pipeline_id}')
        LATERAL VIEW explode(
            from_json(details:flow_progress.data_quality.expectations, '{expectation_schema}')
        ) t AS expectation
        WHERE event_type = 'flow_progress'
          AND details:flow_progress.data_quality IS NOT NULL
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY dataset, name ORDER BY timestamp DESC
        ) = 1
    """)


def _get_event_log_errors(spark: SparkSession, pipeline_id: str, update_id: str) -> str:
    """event_log()からERRORレベルのイベントメッセージを抽出して整形する。

    パイプライン更新がFAILEDになった際、テスト失敗メッセージに含めるための
    デバッグ情報を生成する。

    Args:
        spark: SparkSession。
        pipeline_id: 対象パイプラインのID。
        update_id: 対象のupdate ID。

    Returns:
        タイムスタンプ付きのエラーメッセージを改行区切りで連結した文字列。
        該当イベントがない場合はその旨を示す文字列を返す。
    """
    rows = spark.sql(f"""
        SELECT timestamp, message
        FROM event_log('{pipeline_id}')
        WHERE origin.update_id = '{update_id}'
          AND level = 'ERROR'
        ORDER BY timestamp
    """).collect()

    if not rows:
        return "(event_logにERRORレベルのイベントなし)"
    return "\n".join(f"[{row['timestamp']}] {row['message']}" for row in rows)


def assert_expectations_pass(
    spark: SparkSession, pipeline_id: str, expected: dict[str, set[str]]
) -> None:
    """全expectationsのfailed_recordsが0であることを確認する。

    Args:
        spark: SparkSession。
        pipeline_id: 対象パイプラインのID。
        expected: テーブル名をキー、expectation名のセットを値とする辞書。
            `SILVER_EXPECTATIONS` または `GOLD_EXPECTATIONS` を渡す想定。

    Raises:
        AssertionError: 1件でもfailed_recordsが0でないexpectationがある場合。
    """
    actual_df = _get_latest_expectations_df(spark, pipeline_id)
    actual_rows = {(row["dataset"], row["name"]): row for row in actual_df.collect()}

    failures: list[str] = []
    for table, expectation_names in expected.items():
        for name in expectation_names:
            row = actual_rows.get((table, name))
            if row is None:
                failures.append(f"{table}.{name}: event_logに結果が記録されていない")
            elif row["failed_records"] > 0:
                failures.append(f"{table}.{name}: failed_records={row['failed_records']}")

    assert not failures, "Expectations failed:\n" + "\n".join(failures)
