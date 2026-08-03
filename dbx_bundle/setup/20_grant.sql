-- =============================================================================
-- Service Principalへの権限付与
--
-- 前提
--   - 10_create.sql 実行後に実行する
--   - Catalog/Schema/Volume が作成済みであること
--
-- Notebookから以下の値が埋め込まれる
--   {catalog_name}
--   {service_principal_id}
--
-- GRANTは複数回実行しても安全（冪等）。
-- =============================================================================

-- Catalog/Schemaへの使用権限
GRANT USE CATALOG ON CATALOG IDENTIFIER('{catalog_name}')
  TO `{service_principal_id}`;

GRANT USE SCHEMA ON CATALOG IDENTIFIER('{catalog_name}')
  TO `{service_principal_id}`;

-- テスト用スキーマへの個別権限（テーブル・MVの削除用）
GRANT USE SCHEMA ON SCHEMA IDENTIFIER('{catalog_name}.shogi_silver')
  TO `{service_principal_id}`;

GRANT USE SCHEMA ON SCHEMA IDENTIFIER('{catalog_name}.shogi_gold')
  TO `{service_principal_id}`;

GRANT CREATE TABLE ON SCHEMA IDENTIFIER('{catalog_name}.shogi_silver')
  TO `{service_principal_id}`;

GRANT CREATE MATERIALIZED VIEW ON SCHEMA IDENTIFIER('{catalog_name}.shogi_silver')
  TO `{service_principal_id}`;

GRANT MANAGE ON SCHEMA IDENTIFIER('{catalog_name}.shogi_silver')
  TO `{service_principal_id}`;

GRANT CREATE TABLE ON SCHEMA IDENTIFIER('{catalog_name}.shogi_gold')
  TO `{service_principal_id}`;

GRANT CREATE MATERIALIZED VIEW ON SCHEMA IDENTIFIER('{catalog_name}.shogi_gold')
  TO `{service_principal_id}`;

GRANT MANAGE ON SCHEMA IDENTIFIER('{catalog_name}.shogi_gold')
  TO `{service_principal_id}`;

-- Volumeへの読み書き権限
GRANT READ VOLUME, WRITE VOLUME ON VOLUME IDENTIFIER('{catalog_name}.landing.analyzed')
  TO `{service_principal_id}`;

GRANT READ VOLUME, WRITE VOLUME ON VOLUME IDENTIFIER('{catalog_name}.artifacts.whl')
  TO `{service_principal_id}`;

-- テスト用Volumeへの読み書き権限
GRANT READ VOLUME, WRITE VOLUME ON VOLUME IDENTIFIER('{catalog_name}.test.data')
  TO `{service_principal_id}`;