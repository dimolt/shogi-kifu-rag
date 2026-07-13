# Databricks notebook source
# MAGIC %md
# MAGIC # Databricks 初期環境構築
# MAGIC
# MAGIC ## 目的
# MAGIC - 初期環境構築用SQLを順番に実行する。
# MAGIC - SQLファイルはファイル名の昇順（10_*, 20_* ...）で実行される。
# MAGIC
# MAGIC ## 実行方法
# MAGIC 1. target_catalog を選択
# MAGIC 2. service_principal_id を入力
# MAGIC 3. Notebook を Run All
# MAGIC
# MAGIC ## 対象SQL
# MAGIC - 10_create.sql : Catalog配下のSchema・Volumeを作成
# MAGIC - 20_grant.sql  : Service Principalへ権限を付与

# COMMAND ----------
from pathlib import Path

# COMMAND ----------
# -----------------------------------------------------------------------------
# 実行パラメータ
#
# target_catalog
#   初期構築対象のCatalog
#
# service_principal_id
#   権限付与対象のService Principal名
# -----------------------------------------------------------------------------
dbutils.widgets.dropdown("target_catalog", "shogi_dev", ["shogi_dev", "shogi_test", "shogi"])
dbutils.widgets.text("service_principal_id", "")

target_catalog = dbutils.widgets.get("target_catalog")
service_principal_id = dbutils.widgets.get("service_principal_id")

# COMMAND ----------
# SQLテンプレートへ埋め込むパラメータ
params = {
    "catalog_name": target_catalog,
    "service_principal_id": service_principal_id,
}

SQL_DIR = Path("./").resolve()

# COMMAND ----------
def execute_sql_file(file_path: Path):
    """
    SQLファイルを実行する。

    処理内容
    --------
    1. SQLファイルを読み込む
    2. パラメータを置換する
    3. ';'区切りでSQLを順番に実行する

    Args:
        file_path: 実行するSQLファイル
    """
    sql = file_path.read_text(encoding="utf-8")
    sql = sql.format(**params)

    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            spark.sql(stmt)

# COMMAND ----------
# ファイル名順にSQLを実行
#
# 10_create.sql
# 20_grant.sql
# ...
#
# のように番号を付与することで実行順序を制御する。
for sql_file in sorted(SQL_DIR.glob("*.sql")):
    execute_sql_file(sql_file)