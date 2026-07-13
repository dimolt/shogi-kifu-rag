-- =============================================================================
-- shogi-kif-rag プロジェクトの databricks Catalog 配下の Schema / Volume を初期構築するスクリプト。
-- DABs ではなく本スクリプトで catalog/schema/volume のライフサイクルを個別管理する。
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
--   - ntb_setup_environment.py を Databricks Notebook として開き、上部のウィジェットで
--     {catalog_name} と {service_principal_id} の値を入力してから実行する。
--
--   すべて `IF NOT EXISTS` で書かれているため、複数回実行しても安全（冪等）。
-- =============================================================================
-- 本SQLではCatalogは作成しない。
--
-- Catalogは管理者が事前に作成することを前提とし、
-- 本スクリプトではCatalog配下のSchemaおよびVolumeのみを管理する。
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Schemaの作成
-- -----------------------------------------------------------------------------

-- landing層 - ファイル格納
CREATE SCHEMA IF NOT EXISTS IDENTIFIER('{catalog_name}.landing')
  COMMENT 'landing層 - ファイル格納';

-- Bronze層 - 生データ格納
CREATE SCHEMA IF NOT EXISTS IDENTIFIER('{catalog_name}.shogi_bronze')
  COMMENT 'Bronze層 - 生データ格納';

-- Silver層 - 解析済みデータ
CREATE SCHEMA IF NOT EXISTS IDENTIFIER('{catalog_name}.shogi_silver')
  COMMENT 'Silver層 - 解析済みデータ';

-- Gold層 - RAG用特徴量
CREATE SCHEMA IF NOT EXISTS IDENTIFIER('{catalog_name}.shogi_gold')
  COMMENT 'Gold層 - RAG用特徴量';

-- wheelなどのアーティファクト格納用（DABsのartifact_pathがこのVolumeを参照する）
CREATE SCHEMA IF NOT EXISTS IDENTIFIER('{catalog_name}.artifacts')
  COMMENT 'アーティファクト格納用スキーマ';

-- integration/e2eテスト用
CREATE SCHEMA IF NOT EXISTS IDENTIFIER('{catalog_name}.test')
  COMMENT 'integration/e2eテスト用スキーマ';

-- -----------------------------------------------------------------------------
-- 2. Volumeの作成
-- -----------------------------------------------------------------------------

-- KIFファイル（棋譜データ）のアップロード用。Bronze層への取り込み元。
CREATE VOLUME IF NOT EXISTS IDENTIFIER('{catalog_name}.landing.analyzed')
  COMMENT '解析済棋譜アップロード用';

-- shogi-kif-rag wheel の配置用。databricks.yml の workspace.artifact_path が
-- このVolumeを指す（serverless computeでのキャッシュ問題を避けるためVolume経由にしている）。
CREATE VOLUME IF NOT EXISTS IDENTIFIER('{catalog_name}.artifacts.whl')
  COMMENT 'Wheelファイル格納用';

--  integration/e2eテストデータ格納用
CREATE VOLUME IF NOT EXISTS IDENTIFIER('{catalog_name}.test.data')
  COMMENT 'integration/e2eテストデータ格納用';