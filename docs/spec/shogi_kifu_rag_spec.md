# 将棋棋譜解析RAGアプリ 仕様書

**アプリ名**: 盤上問答（Banjou Mondo）  
**リポジトリ名**: `shogi-kifu-rag`  
**最終更新**: 2026-06-19

---

## 1. プロジェクト概要

### 目的

将棋の棋譜を入力として、各局面の形勢グラフ表示・推奨手の説明・実際の指し手への質問回答を行うRAGアプリケーション。

### ターゲットユーザー

中級者（初段〜三段）。「なぜその手が良いか」を言語化したいニーズが高く、RAGの価値が最大化される層。

### 技術スタック

| 区分 | 採用技術 | 選定理由 |
|---|---|---|
| 実行環境 | Databricks Community Edition (CE) | 無料・Delta Table・Spark利用可能 |
| 言語 | Python 3.12 | CE標準 |
| 依存関係管理 | uv + pyproject.toml | 高速・再現性高・lockファイル管理 |
| 棋譜パーサ | python-shogi 1.1.1 | KIF/CSA対応・SFEN変換可能 |
| ローカル解析 | やねうら王 7.63 Windows版（NNUE） | 高精度評価値取得用・ローカルPCで実行 |
| Vector Store | ChromaDB（ローカル） | CE環境ではMosaic AI Vector Search利用不可 |
| Embedding | paraphrase-multilingual-MiniLM-L12-v2 | 日本語対応・117MB・CE RAM内に収まる |
| LLM | Gemini 2.5 Flash（無料枠） + Groq Llama 3.3 70B（フォールバック） | 無料・日本語品質良好 |
| UI | Gradio + ngrok | CE環境ではDatabricks Apps利用不可 |
| データレイク | Delta Table（Medallionアーキテクチャ） | CE標準 |

---

## 2. 全体アーキテクチャ

### データフロー

```
【ローカルPC (Windows)】
  KIFファイル
    ↓ python-shogi でパース
    ↓ やねうら王 NNUE で go infinite + stop（3秒）方式で解析（エンジン再利用）
    → analysis.csv（game_id, move_number, sfen, prev_sfen, move_usi,
                    player, black_player, white_player, best_move,
                    score_cp, pv）
    ↓ Volumes（/Volumes/shogi/landing/kif/）にアップロード

【Databricks CE (ARM64)】

  Bronze層
    Volumes（/Volumes/shogi/landing/kif/）
      - KIFファイル原本（生データ）

  Silver層
    shogi.shogi_silver.positions
      - analysis.csvを直接登録（Bronze経由なし）
      - ローカルPCの高精度評価値を保持

  Gold層
    shogi.shogi_gold.game_summary
      - 棋譜単位の集約（先手/後手の悪手数・形勢グラフ用JSON）
      - UI強化時（悪手サマリー表示）に活用予定
    shogi.shogi_gold.position_features
      - 局面単位の特徴量（move_quality, search_text 等）
      - GradioのUIデータソース（Silver Tableは参照しない）
    shogi.shogi_gold.floodgate_positions
      - Floodgate棋譜（直近1ヶ月・1日最大10局）

  Vector Store（ChromaDB / /tmp/shogi/chromadb）
    positions           ← shogi_gold.position_features
    floodgate_positions ← shogi_gold.floodgate_positions
    joseki_knowledge    ← Wikipedia戦法解説（20戦法・374チャンク）

  RAGチェーン
    build_combined_context()
      ① positions（常時・3件）
      ② joseki_knowledge（戦法キーワード検出時・2件）
      ③ floodgate_positions（形勢キーワード検出時・2件）
    → Gemini 2.5 Flash / Groq Llama 3.3 70B

  Gradio UI（ngrok公開）
    棋譜解析タブ: 対局選択 → 形勢グラフ
    局面質問タブ: 手数選択 → 推奨手・読み筋 → 質問回答
```

### CE制約と対応方針

| 機能 | CE制約 | 対応 |
|---|---|---|
| Mosaic AI Vector Search | 利用不可 | ChromaDB（ローカル）で代替 |
| Databricks Apps | 利用不可 | Gradio + ngrok で代替 |
| Job Scheduler | 利用不可 | ノートブック手動実行 |
| DBFS | Serverlessクラスターで非対応 | Volumes（/Volumes/）を使用 |
| /tmp 永続化 | セッション再起動で消滅 | ChromaDBは毎セッション再構築 |
| やねうら王 NNUE | ARM64でSegfault | ローカルPC（Windows x64）で解析 |

---

## 3. プロジェクト構成

### ディレクトリ構造

```
ShogiApp/
├─ pyproject.toml          # 依存関係管理（唯一の定義元）
├─ uv.lock                 # lockファイル（必ずコミット）
├─ requirements-local.txt  # local環境用（export結果）
├─ requirements-remote.txt  # remote環境用（export結果）
├─ .venv_local/            # local仮想環境（コミットしない）
├─ .venv_remote/           # remote仮想環境（コミットしない）
├─ local/                  # ローカル実行用モジュール
│  └─ src/
│     ├─ config/           # 設定管理
│     ├─ engine_analyzer/  # やねうら王連携
│     ├─ kif_parser/       # sharedのimportラッパー
│     └─ local_analyze.py  # メインスクリプト
├─ shared/                 # 共通モジュール
│  └─ src/
│     └─ kif_parser/       # KIFパーサ・日本語変換
├─ scripts/                # ユーティリティスクリプト
│  ├─ export-requirements.ps1
│  └─ sync-env.ps1
├─ spec/                   # 仕様書
└─ tests/                  # テスト
```

### 依存関係管理

**pyproject.tomlグループ定義**:

```toml
[dependency-groups]
local = [
    "pyspark",
]
remote = [
    "databricks-connect>=15.4,<15.5",
]
dev = [
    "pytest",
    "ruff",
    "mypy",
    "ipykernel",
]
```

**運用ルール**:
- pyproject.toml を依存関係の唯一の定義元とする
- uv.lock を必ずコミットする
- requirements-local.txt は export 結果として管理する
- requirements-remote.txt は export 結果として管理する
- 仮想環境はコミットしない
- local環境で Databricks Connect を利用しない
- remote環境で PySpark単体実行を行わない
- ライブラリ追加時は必ず uv lock を更新する

---

## 4. コンポーネント仕様

### 4-1. ローカルPC解析（local_analyze.py）

**役割**: KIFファイルをやねうら王NNUEで解析してanalysis.csvを出力する。

**設計意図**: CE環境（ARM64）ではやねうら王NNUEがSegfaultで動作しない（x86 SIMD命令依存）。ローカルPC（Windows x64）で解析してCSVをVolumeにアップロードする方式を採用。

**設定パラメータ**:

| パラメータ | デフォルト値 | 説明 |
|---|---|---|
| `YANEURAOU_BIN` | ShogiGUIインストールパス | やねうら王実行ファイルのフルパス |
| `EVAL_DIR` | ShogiGUIのevalディレクトリ | nn.binが格納されたディレクトリ |
| `THINK_TIME` | 3.0秒 | 局面あたりの思考時間。深さ10相当 |
| `USI_HASH` | 256MB | ハッシュテーブルサイズ |

**パフォーマンス最適化**:
- エンジンを1回だけ起動して全局面を解析（エンジン再利用）
- `initialize_usi()` でUSI初期化を1回実行
- `analyze_position_reusable()` で各局面を解析（quit/communicateなし）
- 全局面解析後にエンジンを停止

**主な実装上の注意点**:

- やねうら王TOURNAMENT版は`MinimumThinkingTime`の最小値が1000msに固定されており`go depth`が機能しない。`go infinite` + `stop`（THINK_TIME秒後）方式で回避する。
- `ResignValue`をデフォルト（99999）のままにすると終盤局面で`score cp 0`が返る。`score mate N`を検出して±30000cpに変換する処理を追加する。
- KIFファイルのエンコードはShift-JISとUTF-8が混在する。`chardet`で自動判定し`cp932`に統一する（cp1006はcp932のエイリアスとして扱う）。
- 複数KIFを一括処理する場合はディレクトリ内の全`.kif`ファイルをループ処理してCSVを結合する。
- analysis.csvの生成後はDatabricks UIから手動でVolumeにアップロードする（`/Volumes/shogi/landing/kif/analysis.csv`）。

### 4-2. KIFパーサ（kif_to_positions）

**役割**: KIFファイルをパースして局面リストを生成する。

**設計意図**: `python-shogi`の`shogi.KIF.Parser.parse_str()`でパース。`shogi.CSA`も同様の構造のためFloodgate棋譜（CSA形式）にも同じパターンを適用できる。

**主な実装上の注意点**:

- `shogi.move_from_usi()`は存在しない。`shogi.Move.from_usi()`を使う。
- `kif.get("names")`はリスト形式（`['先手名', '後手名']`）で返る。辞書形式ではない。
- `prev_sfen`（指す前の局面）を各局面に付与する。日本語変換（`usi_to_japanese()`）はこの値を使う。指した後のSFENを渡すと駒が存在しないためNoneが返る。

### 4-3. USIエンジンクライアント（UsiEngineClient）

**役割**: USIエンジンとのUSIプロトコル通信を管理する。

**メソッド**:

| メソッド | 説明 |
|---|---|
| `start()` | エンジンプロセスを起動 |
| `initialize_usi(usi_hash)` | USI初期化コマンドを送信（1回のみ実行） |
| `analyze_position_with_time()` | 単発解析用（quit/communicateで終了） |
| `analyze_position_reusable()` | 再利用解析用（エンジンを維持） |
| `stop()` | エンジンプロセスを停止 |

**パフォーマンス最適化**:
- 複数局面解析時は `start()` → `initialize_usi()` → `analyze_position_reusable()` × N → `stop()` の順序で実行
- `analyze_position_reusable()` は `quit` を送信せず、`bestmove` 受信後に次の局面解析を開始

### 4-4. Medallionパイプライン

**役割**: Silver → Gold へデータを変換・集約する。

**設計意図**: ローカルPC解析結果（analysis.csv）をSilver Tableに直接登録し、Gold TableではRAG用の特徴量（`move_quality`・`search_text`・`score_delta`）を付加する。GradioのUIデータソースはGold Tableの`position_features`に統一する。Silver Tableを直接参照しない。

**move_qualityの判定基準**:

| 値 | 条件 |
|---|---|
| `start` | 手数0（初期局面） |
| `best` | 実際の指し手 = 推奨手 |
| `blunder` | 評価値変化の絶対値 ≥ 200cp |
| `normal` | 上記以外 |

**game_summaryの位置づけ**: 棋譜単位の集約（先手/後手の悪手数・形勢グラフ用JSON）を保持する。現在のUIでは未使用だが、UI強化時（棋譜解析タブへの悪手サマリー表示）で活用予定。

### 4-5. ChromaDB（Vector Store）

**役割**: 3種類のコレクションで局面・戦法知識の類似検索を提供する。

**設計意図**: コレクションを分離することで検索クエリの性質の違い（SFEN類似 vs 自然言語）に対応する。質問内容に応じて動的にコレクションを選択する。

**コレクション一覧**:

| コレクション | 件数（目安） | Embedding対象 | 検索タイミング | 取得件数 |
|---|---|---|---|---|
| `positions` | 対局数 × 平均手数 | `search_text`（SFEN+評価値） | 常時 | 3件 |
| `floodgate_positions` | 約36,000局面 | `search_text`（SFEN+エンジン名） | 形勢キーワード検出時 | 2件 |
| `joseki_knowledge` | 約374チャンク | Wikipedia本文（段落単位） | 戦法キーワード検出時 | 2件 |

**注意点**: `/tmp`はセッション再起動で消えるため毎セッション再登録が必要。Gold Tableから再構築する処理をセッション初期化セルに組み込む。

### 4-6. RAGチェーン（build_combined_context / get_rag_answer）

**役割**: 3コレクションの検索結果を質問内容に応じて統合してLLMに渡す。

**設計意図**: 全コレクションを常時検索するとプロンプトが肥大化しGemini無料枠を圧迫する。正規表現キーワードマッチで検索対象を動的に絞る。

**キーワード判定**:

| コレクション | トリガーキーワード例 |
|---|---|
| `joseki_knowledge` | 戦法・定跡・矢倉・四間飛車・棒銀・振り飛車・囲い・手筋 等 |
| `floodgate_positions` | 形勢・評価・有利・不利・互角・比較・強豪・エンジン 等 |

### 4-7. 日本語表記変換（usi_to_japanese / pv_to_japanese）

**役割**: USI形式の指し手（`7g7f`・`S*6c`等）を日本語表記（`７六歩(７七)`・`６三銀打`等）に変換する。

**設計意図**: LLMへのプロンプトと画面表示の両方でUSI形式を排除し、将棋として自然な表現にする。

**主な実装上の注意点**:

- `board.kif_str(move)`は引数なしの盤面文字列化メソッドであり指し手変換には使えない。独自実装（`_move_to_ja()`）が必要。
- `usi_to_japanese()`には必ず`prev_sfen`（**指す前**の局面）を渡す。指した後のSFENを渡すと`board.piece_at(from_square)`がNoneを返す。
- `pv_to_japanese()`は`prev_sfen`から順番に`board.push()`して各手の局面を進めながら変換する。

### 4-8. LLM生成（generate_with_fallback）

**役割**: Gemini 2.5 Flashで回答を生成し、レート制限時はGroqにフォールバックする。

**設計意図**: Gemini無料枠は20 RPM制限があり、連続質問でレート制限に達する。Groq（Llama 3.3 70B）を自動フォールバックとして設定することでユーザー体験を維持する。

**フォールバック順序**: Gemini 2.5 Flash（1回リトライ・35秒待機）→ Groq Llama 3.3 70B

**品質差**: Groqフォールバック時はLlama 3.3 70BのためGeminiより日本語品質が若干低下する場合がある。LLM呼び出し部分の改善はTODO（セクション7参照）。

### 4-9. Gradio UI

**役割**: Gold Tableから対局を選択して形勢グラフ表示・局面質問回答を行う。

**設計意図**: KIFアップロードではなくGold Table（`position_features`）を直接参照する。ローカルPC解析とDatabricks側の処理を明確に分離することで、UI起動時の解析待ち時間をゼロにする。Silver Tableは参照しない。

**タブ構成**:

| タブ | 機能 |
|---|---|
| 棋譜解析 | 対局選択（Dropdown）→ 形勢グラフ（Plotly）|
| 局面質問 | 手数選択 → 推奨手・読み筋（日本語表記）→ 質問入力 → RAG回答 |

---

## 5. データ仕様

### 5-1. shogi.shogi_silver.positions

analysis.csvをそのまま登録したテーブル。ローカルPCの高精度評価値を保持する中間テーブル。GradioのUIは本テーブルを直接参照しない（Gold Tableを使用）。

| カラム名 | 型 | 説明 |
|---|---|---|
| `game_id` | string | KIFファイル名ベースの対局ID |
| `move_number` | integer | 手数（0 = 初期局面） |
| `sfen` | string | 指し手**後**の局面（SFEN形式） |
| `prev_sfen` | string | 指し手**前**の局面（日本語変換・エンジン解析用） |
| `move_usi` | string | 実際の指し手（USI形式） |
| `player` | string | 手番（"black" / "white"） |
| `black_player` | string | 先手プレイヤー名 |
| `white_player` | string | 後手プレイヤー名 |
| `best_move` | string | エンジン推奨手（USI形式） |
| `score_cp` | integer | 評価値（先手視点センチポーン） |
| `pv` | string | 読み筋（スペース区切りUSI形式・最大8手） |

### 5-2. shogi.shogi_gold.position_features

Silver Tableに特徴量を付加したRAG用テーブル。GradioのUIデータソース。

Silver Tableの全カラムに加えて以下を追加:

| カラム名 | 型 | 説明 |
|---|---|---|
| `score_from_turn` | integer | 手番視点の評価値（後手番は符号反転） |
| `score_delta` | integer | 前手からの評価値変化（悪手検出用） |
| `is_best_move` | boolean | 実際の指し手 = 推奨手かどうか |
| `is_blunder` | boolean | `abs(score_delta) >= 200` |
| `move_quality` | string | start / best / blunder / normal |
| `search_text` | string | ChromaDB登録用テキスト（SFEN+評価値+指し手） |

### 5-3. shogi.shogi_gold.game_summary

棋譜単位の集約テーブル。現在のUIでは未使用。UI強化時に活用予定。

| カラム名 | 型 | 説明 |
|---|---|---|
| `game_id` | string | 対局ID |
| `black_player` | string | 先手プレイヤー名 |
| `white_player` | string | 後手プレイヤー名 |
| `total_moves` | integer | 総手数 |
| `final_score_cp` | integer | 最終局面の評価値 |
| `black_blunders` | integer | 先手の悪手数（score_delta ≥ 200cp） |
| `white_blunders` | integer | 後手の悪手数（score_delta ≥ 200cp） |
| `score_series_json` | string | 全局面の評価値系列（形勢グラフ用JSON） |

### 5-4. shogi.shogi_gold.floodgate_positions

Floodgate棋譜（CSA形式）から生成した参考局面集。

Silver Tableと共通カラムに加えて以下を追加・変更:

| カラム名 | 型 | 説明 |
|---|---|---|
| `black_engine` | string | 先手エンジン名（CSAのnamesリスト[0]） |
| `white_engine` | string | 後手エンジン名（CSAのnamesリスト[1]） |
| `score_cp` | integer | 0固定（CSAコメントに評価値なし） |
| `search_text` | string | `局面: {sfen} 指し手: ... 対局者: {black} vs {white}` |

### 5-5. ChromaDBコレクション

| コレクション | ID形式 | メタデータ主要フィールド |
|---|---|---|
| `positions` | `{game_id}__move{move_number:04d}` | game_id, move_number, sfen, move_usi, best_move, score_cp, move_quality, pv |
| `floodgate_positions` | `{game_id}__move{move_number:04d}` | game_id, move_number, sfen, prev_sfen, move_usi, black_engine, white_engine |
| `joseki_knowledge` | `{joseki_name}__chunk{chunk_index:04d}` | joseki_name, chunk_index, source="wikipedia" |

---

## 6. 外部連携仕様

### 6-1. Floodgate棋譜

| 項目 | 内容 |
|---|---|
| URL | `https://wdoor.c.u-tokyo.ac.jp/shogi/x/{year}/{month}/{day}/` |
| 形式 | CSA形式（`wdoor+floodgate-*.csa`） |
| 取得範囲 | 直近1ヶ月・1日最大10局（計約310局） |
| 注意点（ネットワーク） | HTTPSのみ対応（HTTPは301リダイレクト） |
| 注意点（パース） | CSAの`names`キーはリスト形式（KIFと同様） |
| 評価値 | CSAコメントに含まれないため0固定 |
| セッション再取得 | 不要（Gold Tableに保存済み） |
| CSAキャッシュ | `/tmp/floodgate/csa/`（セッション内のみ有効） |

### 6-2. Wikipedia戦法解説

| 項目 | 内容 |
|---|---|
| API | `https://ja.wikipedia.org/w/api.php?action=query&prop=extracts` |
| 対象 | 20戦法（四間飛車・矢倉・棒銀・美濃囲い 等） |
| 注意点 | `User-Agent`ヘッダ必須（未設定だとHTTP 403） |
| レート制限対応 | 戦法ごとに0.5秒スリープ |
| チャンク | 段落単位・最大500文字・見出し行除外 |
| 取得失敗 | 一手損角換わり・定跡・終盤（将棋）は404/空のため対象外 |
| 戦法リスト管理 | コード内定数（`JOSEKI_LIST`）で管理 |
| セッション再構築 | Gold Table非対応のため毎セッションWikipedia APIから再取得 |

### 6-3. Gemini API

| 項目 | 内容 |
|---|---|
| モデル | gemini-2.5-flash |
| 無料枠 | 20 RPM |
| フォールバック | Groq Llama 3.3 70B（429発生時・35秒待機後） |
| プロンプト | 200文字以内・USI形式禁止・日本語表記指定 |

### 6-4. やねうら王（ローカルPC）

| 項目 | 内容 |
|---|---|
| バイナリ | YaneuraOu_NNUE-tournament-clang++-avx2.exe |
| 評価関数 | nn.bin（HalfKP形式・約60MB） |
| 解析方式 | `go infinite` + `stop`（THINK_TIME秒後） |
| 思考時間 | 3秒（深さ10相当・`THINK_TIME`定数で変更可能） |
| 注意点 | `MinimumThinkingTime`最小値1000msのため`go depth`は動作しない |
| 投了回避 | `score mate N`を±30000cpに変換 |
| パフォーマンス最適化 | エンジン再利用（1回起動で全局面解析） |

---

## 7. 既知の制約と対応

### 7-1. やねうら王 NNUE（CE ARM64環境）

**制約**: ARM64でNNUEがSegfaultする（x86 SIMD命令依存）。  
**対応**: ローカルPC（Windows x64）で解析してCSVをVolumeにアップロードする方式に変更。  
**着手条件**: Azure Databricks（x64）に移行すればCE上でNNUEが動作する。

### 7-2. ChromaDBの永続化

**制約**: `/tmp`はセッション再起動で消滅する。  
**対応**: セッション初期化セルでGold Tableから毎回再構築する（所要時間はセクション8参照）。  
**着手条件**: Azure Databricks移行時にMosaic AI Vector Searchに切り替えれば解決。

### 7-3. Geminiレート制限

**制約**: 無料枠20 RPM。連続質問で上限に達する。  
**対応**: Groq Llama 3.3 70Bに自動フォールバック（日本語品質は若干低下）。  
**着手条件**: Gemini有料プランに移行すれば解決。

### 7-4. Floodgate棋譜の評価値

**制約**: CSAファイルにエンジンの評価値コメントが含まれていない。  
**対応**: `score_cp`は0固定。ChromaDBの`search_text`にはSFEN・指し手・エンジン名のみ含める。  
**着手条件**: 評価値付きCSAファイルが入手できれば改善可能。

### 7-5. python-shogi APIの非直感的な仕様

**制約**: バージョンによってAPIが異なり直感的でない挙動がある。  
**対応**:
- `move_from_usi()` → 存在しない。`shogi.Move.from_usi()`を使う。
- `kif.get("names")` → 辞書ではなくリスト`['先手名', '後手名']`で返る。
- `board.kif_str(move)` → 引数なしのメソッド。指し手の日本語変換には使えない。

---

## 8. 今後の改善候補（TODO）

### フェーズ1: 評価精度向上

| 項目 | 着手条件 |
|---|---|
| NNUE評価関数のCE適用 | Azure Databricks（x64）への移行後 |
| 悪手閾値のチューニング（現在200cp固定） | NNUE評価値が取得できてから |
| 評価値の後手視点正規化の精度向上 | フェーズ1完了後 |

### フェーズ2: 知識ベース拡充

| 項目 | 着手条件 |
|---|---|
| Floodgate棋譜のフィルタリング（レート帯指定） | いつでも着手可能 |
| Floodgate棋譜の評価値追加 | 評価値付きCSAファイルの入手後 |
| Wikipedia対象戦法の拡充 | 現行20戦法で品質確認後 |
| 戦法名自動判定（局面 → 戦法ラベル） | フェーズ2基盤完成後 |

### フェーズ3: UI強化

| 項目 | 着手条件 |
|---|---|
| 将棋盤表示（局面の視覚化） | いつでも着手可能 |
| 手順再生機能（前後ナビゲーション） | いつでも着手可能 |
| 解析レポートPDF出力（悪手一覧） | いつでも着手可能 |
| 棋譜解析タブへの悪手サマリー表示（game_summary活用） | いつでも着手可能 |

### フェーズ4: LLM改善

| 項目 | 着手条件 |
|---|---|
| Groqフォールバック時の品質改善（プロンプト最適化） | いつでも着手可能 |
| LLMの日本語将棋特化ファインチューニング検討 | フェーズ4基盤完成後 |

### フェーズ5: 本番移行（Azure Databricks）

| 項目 | 着手条件 |
|---|---|
| ChromaDB → Mosaic AI Vector Search | Azure Databricks移行後 |
| Gradio + ngrok → Databricks Apps | Azure Databricks移行後 |
| Job Schedulerによる棋譜自動取込 | Azure Databricks移行後 |

---

## 9. 運用手順

### 9-1. 開発環境セットアップ

**仮想環境作成**:

```powershell
# local環境
uv venv .venv_local --python 3.12
.\.venv_local\Scripts\python.exe -m ensurepip --upgrade

# remote環境
uv venv .venv_remote --python 3.12
.\.venv_remote\Scripts\python.exe -m ensurepip --upgrade
```

**依存関係同期**:

```powershell
# local環境
.\scripts\sync-env.ps1 local

# remote環境
.\scripts\sync-env.ps1 remote
```

**ライブラリ追加時の手順**:

```powershell
# 1. pyproject.tomlにライブラリを追加
# 2. uv lock
# 3. .\scripts\export-requirements.ps1
# 4. .\scripts\sync-env.ps1 local
# 5. .\scripts\sync-env.ps1 remote
```

### 9-2. 初回セットアップ手順

以下の順序で実行する。

```
1. ローカルPC: local_analyze.py を実行して analysis.csv を生成
2. Databricks UI: analysis.csv を /Volumes/shogi/landing/kif/ にアップロード
3. Silver Table登録ノートブック実行
4. Gold Table構築ノートブック（step3_gold_table.py）実行
5. Floodgate取得ノートブック（task2_floodgate_chromadb.py）実行
   ※ Gold Table登録 + ChromaDB登録（所要時間: 約15〜20分）
6. Wikipedia取得ノートブック（task3_wikipedia_chromadb.py）実行
   ※ Wikipedia取得 + ChromaDB登録（所要時間: 約3〜5分）
7. RAGチェーン + Gradio UI（task10_rag_3collections.py）実行
```

### 9-3. セッション再起動時の最小手順

ChromaDBは`/tmp`に保存されているため毎セッション再構築が必要。  
`task10_rag_3collections.py`のセル3（初期化セル）を実行するだけで自動判定・再構築される。

| 処理 | 所要時間 | 自動/手動 |
|---|---|---|
| positions再構築（Gold Table → ChromaDB） | 約2〜3分 | 自動（セル3内） |
| floodgate_positions再構築 | 約10〜15分 | 自動（セル3内） |
| joseki_knowledge再取得・再構築 | 約3〜5分 | 自動（セル3内） |

### 9-4. 新規棋譜追加手順

```
1. ローカルPC: local_analyze.py を新規KIFファイルに対して実行
2. Databricks UI: analysis.csv を上書きアップロード
   ※ 既存対局を含む全局面のCSVを出力する（追記ではなく全件）
3. Silver Table更新（mode="overwrite"）
4. Gold Table再構築（step3_gold_table.py）
5. ChromaDB再登録（task10_rag_3collections.py セル3）
```
