-- -----------------------------------------------------------------------------
-- 権限付与（GRANT）
--
--    GRANT ... TO の principal 位置は IDENTIFIER() / 関数呼び出しに未対応
--    (GRANT自体がIDENTIFIER対応ステートメントの一覧に含まれていない) ため、
--    EXECUTE IMMEDIATE でSQL文字列を組み立てて実行する。
--
--    EXECUTE IMMEDIATE の引数も「単体の変数/リテラル」しか受け付けないため、
--    結合済みのGRANT文をいったん変数(grant_stmt_*)に格納してから渡す。
--
--    付与先は current_user()、つまりこのスクリプトを実行した本人。
--    デプロイ担当者が変わる場合は grant_stmt_* の組み立て部分を
--    IDENTIFIER(:grantee) 相当のパラメータに差し替えればよい。
-- -----------------------------------------------------------------------------

-- -- landing Volumeへの読み書き権限
-- DECLARE OR REPLACE VARIABLE grant_stmt_landing STRING;
-- SET VAR grant_stmt_landing =
--   'GRANT READ VOLUME, WRITE VOLUME ON VOLUME ' || catalog_name ||
--   '.shogi_bronze.landing TO `' || current_user() || '`';
-- EXECUTE IMMEDIATE grant_stmt_landing;

-- -- whl Volumeへの読み書き権限
-- DECLARE OR REPLACE VARIABLE grant_stmt_whl STRING;
-- SET VAR grant_stmt_whl =
--   'GRANT READ VOLUME, WRITE VOLUME ON VOLUME ' || catalog_name ||
--   '.artifacts.whl TO `' || current_user() || '`';
-- EXECUTE IMMEDIATE grant_stmt_whl;

-- -- test.data Volumeへの読み書き権限
-- DECLARE OR REPLACE VARIABLE grant_stmt_test_data STRING;
-- SET VAR grant_stmt_test_data =
--   'GRANT READ VOLUME, WRITE VOLUME ON VOLUME ' || catalog_name ||
--   '.test.data TO `' || current_user() || '`';
-- EXECUTE IMMEDIATE grant_stmt_test_data;

DECLARE OR REPLACE VARIABLE catalog_name STRING DEFAULT '';
SET VAR catalog_name = :catalog;

DECLARE OR REPLACE VARIABLE service_principale_id STRING DEFAULT '';
SET VAR service_principale_id = :service_principale_id;

DECLARE OR REPLACE VARIABLE grant_stmt STRING;

-- Catalog/Schemaへの使用権限
SET VAR grant_stmt =
  'GRANT USE CATALOG ON CATALOG ' || catalog_name ||
  ' TO `' || service_principale_id || '`';
EXECUTE IMMEDIATE grant_stmt;

SET VAR grant_stmt =
  'GRANT USE SCHEMA ON CATALOG ' || catalog_name ||
  ' TO `' || service_principale_id || '`';
EXECUTE IMMEDIATE grant_stmt;


-- Volumeへの読み書き権限
SET VAR grant_stmt =
  'GRANT READ VOLUME, WRITE VOLUME ON VOLUME ' || catalog_name || '.artifacts.whl' ||
  ' TO `' || service_principale_id || '`';
EXECUTE IMMEDIATE grant_stmt;