# プロジェクトルール

## テストデータ管理方針

Integration Testのテストデータは「原本」と「実行用データ」を分離して管理します。

### データの役割

| 場所 | 役割 | cleanup |
|------|------|---------|
| `tests/integration/data` | テストデータ原本（Git管理） | しない |
| Volume `analyzed/` | Pipeline実行用データ | する |
| Bronze/Silver/Gold | Pipeline生成データ | する |
| `dev` target | 実行環境 | 変更なし |

### ディレクトリ構造

```
tests/integration/data/
├── normal/
│   ├── basic/          # 基本的な正常系テストデータ
│   └── edge_cases/     # 境界値の正常系テストデータ（将来拡張用）
└── abnormal/
    ├── schema_errors/  # スキーマ違反のテストデータ
    └── format_errors/  # フォーマットエラーのテストデータ（将来拡張用）
```

### Fixture使用ガイドライン

Integration Testでは以下のfixtureを使用します：

- `volume_setup` (scope="session"): セッション開始時にVolume初期化
- `clean_volume` (scope="function"): 各テスト前後のVolume/テーブルクリーンアップ
- `normal_test_data` (scope="function"): 正常系データのVolumeコピー
- `abnormal_test_data` (scope="function"): 異常系データのVolumeコピー

**重要**:
- テストコードから直接テストデータ原本を参照せず、必ずfixture経由で使用してください
- 正常系・異常系の差異はソースデータのみで、pipeline起動関数は共通を使用してください
- データ分離はclean_volume fixtureによる毎回のクリアで行い、専用スキーマは使用しないでください

### テスト実行環境

- **dev / test / prod** の3 targetのみを使用
- Integration Testはdev環境で実行
- テストfixtureでsetup/teardownする
- データのクリーンアップはスキーマ、Volumeの削除をしない。MV、テーブルはDrop、Volume内のファイルを削除

## ビルド・テスト・検証コマンド

### テスト実行

```bash
# Unitテスト
uv run pytest tests/unit -v

# Integrationテスト（正常系のみ）
uv run pytest tests/integration -v -m "not abnormal"

# Integrationテスト（異常系のみ）
uv run pytest tests/integration -v -m "abnormal"

# 全Integrationテスト
uv run pytest tests/integration -v

# E2Eテスト
uv run pytest tests/e2e -v
```

### Lint・型チェック

```bash
# Ruff lint
ruff check src/ tests/

# Ruff format
ruff format src/ tests/

# MyPy type check
mypy src/ tests/
```

### Bundle操作

```bash
# Bundle validation
databricks bundle validate --strict --target dev

# Bundle deployment
databricks bundle deploy --target dev
```
