-- =============================================================================
-- shogi-kif-rag プロジェクトの databricks Catalog 配下の Schema / Volume を初期構築するスクリプト。
-- dev / test / prod で catalog 名のみが異なるため、DABs (Databricks Asset Bundles)
-- ではなく本スクリプトで catalog/schema/volume のライフサイクルを個別管理する。
--
-- 【DABsで管理しない理由】
--   - bundle自身が生成するwheelの置き場（Volume）をbundleで管理すると、
--     初回デプロイ時に「Volumeが存在しない」エラーになる chicken-and-egg 問題がある
--   - mode: development ターゲットでは schema 名に自動で dev_<user>_ prefix が
--     付与されるため、artifact_path などの固定文字列参照が壊れやすい
--   - `databricks bundle destroy` 実行時に実データを持つ schema ごと
--     消えてしまうリスクがある
--   → catalog/schema/volume は本SQLで先に用意し、DABsはjob/pipelineの
--     デプロイに専念させる
--
-- 【実行方法】
--   Databricks SQL Editor にこのファイルの内容を貼り付けて実行する。
--   :catalog という named parameter が自動的に入力ウィジェットとして表示されるので、
--   環境に応じて以下のいずれかを入力してから実行する。
--     - dev  : shogi_dev
--     - test : shogi_test
--     - prod : shogi
--
--   すべて `IF NOT EXISTS` で書かれているため、複数回実行しても安全（冪等）。
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 0. catalog名をセッション変数に格納する
--
--    :catalog (named parameter marker) は単体の変数/リテラルとしてでないと
--    IDENTIFIER() や EXECUTE IMMEDIATE の式の中で直接 || 結合できない
--    (UNSUPPORTED_EXPR_FOR_PARAMETER エラーになる) ため、
--    一度セッション変数 catalog_name にコピーしてから使う。
-- -----------------------------------------------------------------------------
DECLARE OR REPLACE VARIABLE catalog_name STRING DEFAULT '';
SET VAR catalog_name = :catalog;


-- -----------------------------------------------------------------------------
-- 1. Schemaの作成
--
--    IDENTIFIER(catalog_name || '.xxx') は、文字列をSQLインジェクション安全な形で
--    オブジェクト名として解釈させるための構文。catalog名だけを外から差し替えられる。
-- -----------------------------------------------------------------------------

-- Bronze層 - 生データ格納
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(catalog_name || '.shogi_bronze')
  COMMENT 'Bronze層 - 生データ格納';

-- Silver層 - 解析済みデータ
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(catalog_name || '.shogi_silver')
  COMMENT 'Silver層 - 解析済みデータ';

-- Gold層 - RAG用特徴量
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(catalog_name || '.shogi_gold')
  COMMENT 'Gold層 - RAG用特徴量';

-- wheelなどのアーティファクト格納用（DABsのartifact_pathがこのVolumeを参照する）
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(catalog_name || '.artifacts')
  COMMENT 'アーティファクト格納用スキーマ';

-- integration/e2eテスト用
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(catalog_name || '.test')
  COMMENT 'integration/e2eテスト用スキーマ';

-- -----------------------------------------------------------------------------
-- 2. Volumeの作成
-- -----------------------------------------------------------------------------

-- KIFファイル（棋譜データ）のアップロード用。Bronze層への取り込み元。
CREATE VOLUME IF NOT EXISTS IDENTIFIER(catalog_name || '.shogi_bronze.landing')
  COMMENT 'KIFファイルアップロード用';

-- shogi-kif-rag wheel の配置用。databricks.yml の workspace.artifact_path が
-- このVolumeを指す（serverless computeでのキャッシュ問題を避けるためVolume経由にしている）。
CREATE VOLUME IF NOT EXISTS IDENTIFIER(catalog_name || '.artifacts.whl')
  COMMENT 'Wheelファイル格納用';

--  integration/e2eテストデータ格納用
CREATE VOLUME IF NOT EXISTS IDENTIFIER(catalog_name || '.test.data')
  COMMENT 'integration/e2eテストデータ格納用';