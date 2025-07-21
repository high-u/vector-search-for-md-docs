# 設計

## ディレクトリ構成

```plain
  /
  ├── mcp-server/                   # MCPサーバーアプリ
  │   ├── src/
  │   │   ├── interfaces/           # I/O層・外部境界
  │   │   │   ├── database/         # DB接続・スキーマ管理
  │   │   │   ├── mcp/              # MCPサーバー通信
  │   │   │   └── vector/           # ベクトル検索エンジン
  │   │   ├── core/                 # ビジネスロジック
  │   │   │   ├── tools/            # 動的ツール管理
  │   │   │   ├── search/           # 検索処理
  │   │   │   └── embedding/        # ベクトル化処理
  │   │   ├── utilities/            # 汎用機能
  │   │   └── main.py               # DIコンテナ・エントリーポイント
  │   ├── tests/
  │   └── pyproject.toml
  │
  ├── manage-documents/             # ドキュメント管理アプリ
  │   ├── src/
  │   │   ├── interfaces/           # I/O層・外部境界
  │   │   │   ├── database/         # DB接続・スキーマ管理
  │   │   │   ├── filesystem/       # ファイル読み込み
  │   │   │   └── vector/           # ベクトル検索エンジン
  │   │   ├── core/                 # ビジネスロジック
  │   │   │   ├── import/           # ドキュメント取り込み
  │   │   │   ├── tools/            # ツール登録管理
  │   │   │   └── embedding/        # ベクトル化処理
  │   │   ├── utilities/            # 汎用機能
  │   │   └── main.py               # DIコンテナ・エントリーポイント
  │   ├── tests/
  │   │   ├── unit/           # 純粋関数のunit tests
  │   │   ├── integration/    # モジュール間連携tests
  │   │   └── e2e/           # エンドツーエンドtests
  │   └── pyproject.toml
  │
  └── docs/                         # 共通ドキュメント
      ├── SPEC.md
      ├── DEV_RULE.md
      └── README.md
```

## データベース設計

### ツール管理テーブル (tools)

```sql
CREATE TABLE tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,           -- ツール名
    description TEXT NOT NULL,           -- LLMへの説明
    source_directory TEXT NOT NULL,      -- 取り込み元ディレクトリ（絶対パス）
    is_active BOOLEAN DEFAULT 1,         -- 有効/無効フラグ
    app_version TEXT,                    -- アプリバージョン
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### ドキュメントベクトルテーブル (動的生成)

各ツール毎に documents_{tool_name}、vectors_{tool_name} テーブルを動的生成

```ddl
-- ドキュメントテーブル
CREATE TABLE documents_{tool_name} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,             -- source_directoryからの相対パス
    content_hash TEXT NOT NULL,          -- ファイル内容のハッシュ値（差分更新用）
    content TEXT NOT NULL,               -- ファイル全内容
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE CASCADE
);

-- ベクトルテーブル（チャンク単位）
CREATE TABLE vectors_{tool_name} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL,
    document_id INTEGER NOT NULL,        -- 元ドキュメント参照
    chunk_text TEXT NOT NULL,            -- チャンク内容
    start_position INTEGER NOT NULL,     -- 元ファイル内開始位置（文字数）
    end_position INTEGER NOT NULL,       -- 元ファイル内終了位置（文字数）
    embedding BLOB NOT NULL,             -- ベクトルデータ（BLOB型）
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES documents_{tool_name}(id) ON DELETE CASCADE
);

-- ベクトル検索用インデックス
CREATE INDEX idx_vectors_{tool_name}_embedding
ON vectors_{tool_name} (embedding);

-- JOIN性能向上用インデックス
CREATE INDEX idx_vectors_{tool_name}_tool_doc
ON vectors_{tool_name} (tool_id, document_id);

CREATE INDEX idx_documents_{tool_name}_tool
ON documents_{tool_name} (tool_id);

-- ハッシュ値による重複チェック用インデックス
CREATE UNIQUE INDEX idx_documents_{tool_name}_path_hash
ON documents_{tool_name} (tool_id, file_path, content_hash);

-- tool_id + file_path検索用インデックス（update処理等で使用）
CREATE INDEX idx_documents_{tool_name}_tool_path
ON documents_{tool_name} (tool_id, file_path);

-- 位置検索用インデックス
CREATE INDEX idx_vectors_{tool_name}_position
ON vectors_{tool_name} (document_id, start_position, end_position);
```

## コマンド設計

### コマンド名

- `mdvec`

### ツール管理コマンド

#### ツール追加

- `mdvec tool add --name <tool-name> --description <description> --source <directory>`
- `mdvec tool add -n <tool-name> -d <description> -s <directory>`

例: `mdvec tool add -n api-docs -d "API documentation for user authentication" -s ./docs/api`

#### ツール更新

- `mdvec tool update --name <tool-name> [--description <description>] [--source <directory>]`
- `mdvec tool update -n <tool-name> [-d <description>] [-s <directory>]`

#### ツール削除

- `mdvec tool delete --name <tool-name> [-y]`
- `mdvec tool delete -n <tool-name> [-y]`

オプション:

- `-y` : 確認をスキップして削除実行（デフォルトは確認プロンプト表示）

#### ツール有効化/無効化

- `mdvec tool enable --name <tool-name>`
- `mdvec tool enable -n <tool-name>`

- `mdvec tool disable --name <tool-name>`
- `mdvec tool disable -n <tool-name>`

#### ツール一覧

- `mdvec tool ls [--all] [--format <json|table>]`

動作:

- デフォルト: 有効なツール名のみ表示
- `--all` : 全ツール表示（richテーブル形式）
- `--format json` : JSON形式出力
- `--format table` : テーブル形式出力（Rich 利用）

### データ管理コマンド

#### ドキュメント取り込み

- `mdvec import --name <tool-name> [--mode <mode>] [options]`
- `mdvec import -n <tool-name> [-m <mode>] [options]`

モード:

- `--mode new` : 新規作成（デフォルト、ツールが存在する場合はエラー）
- `--mode replace` : 完全再構築（既存データ削除→再構築）
- `--mode update` : 差分更新（ファイルハッシュによる更新判定、存在しないファイルは削除）

オプション:

- `--database <path>` : データベースファイルパス
- `--chunk-size <size>` : チャンクサイズ（トークン数）
- `--chunk-overlap <size>` : チャンクオーバーラップ（トークン数）

例:

- `mdvec import -n api-docs` （デフォルト: --mode new）
- `mdvec import -n api-docs --mode replace`
- `mdvec import -n api-docs --mode update --database ./custom.sqlite`

動作: ツールに設定されたsource_directoryを自動使用、サブディレクトリを常に再帰探索、指定データベースが存在しない場合は自動作成

#### ステータス確認

- `mdvec status [--name <tool-name>]`
- `mdvec status [-n <tool-name>]`

表示内容:

- 引数なし: 全ツールの概要（名前、有効/無効、ドキュメント数、ベクトル数）、データベース情報
- ツール指定時: 該当ツールの詳細情報、最新取り込み日時、ドキュメント一覧、ベクトル統計

### 設定ファイル

config.toml

```toml
[database]
path = "vector-db.sqlite"

[chunking]
size = 1024
overlap = 64

[display]
default_format = "table"
```

## MCP サーバー設計

### 通信プロトコル

STDIO

### ツール登録

#### 動的ツール管理システム

- 起動時にツール情報を取得し、MCP ツールとして動的に登録する。
- ツール毎の処理は、 `vectors_{tool_name}` テーブルを検索するよう設定する。

#### ベクトル検索処理

- ユーザープロンプトベクトル化: MCP クライアントからのプロンプトをリアルタイムでベクトル化
- 類似度計算: SQLite の sqlite-vec 拡張で検索
- 結果返却: 検索結果のチャンクを返却
    - 一旦はチャンク返却で良いが、今後は、返却コンテンツの戦略が必要かも。
        - ベクトル検索結果から、元ファイルのコンテンツ（ `documents_{tool_name}` テーブルデータ）を取得し、該当の章（章の定義が必要）を抽出して返却。

## ベクトル化設計

### コマンドで利用するマークダウンのベクトル化

#### チャンク分割

- トークン単位でのチャンク分割
    - Transformers ライブラリのトークナイザーを使用する
    - デフォルトトークン数（チャンクサイズ）: 1024 (設定範囲: 512 - 4096)
- オーバーラップ
    - 『ファイル: 3000 トークン』、『チャンクサイズ: 1024 トークン』、『オーバーラップ: 64 トークン』の場合
        - chunk[0]: トークン 0    ～ 1023  (1024個)
        - chunk[1]: トークン 960  ～ 1983  (1024個) ← 64個重複
        - chunk[2]: トークン 1920 ～ 2943  (1024個) ← 64個重複
        - chunk[3]: トークン 2880 ～ 2999  (120個)  ← 最後は短くなる

#### チャンクの位置の保持

- 元ファイルのチャンクの位置をチャンクテキストの文字数から算出
    - チャンクの開始位置
    - チャンクの終了位置
- 初期リリースでは使用しないが、ベクトル検索後の、返却データ戦略で、元ファイルのコンテンツから返却用データ抽出で利用する。

#### ベクトル化処理

- transformers ライブラリ経由で PLaMo 埋め込みモデルを使用
- numpy 配列としてベクトル管理

#### データベース保存

- ベクトルデータは BLOB 型で格納
- sqlite-vec 拡張によるベクトルインデックス作成
- チャンク元情報の関連付け保持

### MCP で利用するユーザープロンプトのベクトル化

#### リアルタイム処理

- MCP クライアントからのプロンプト受信
- 同一埋め込みモデルによる即座のベクトル化
- メモリ上での一時保持（永続化不要）

#### 類似度検索

- コサイン類似度による検索
- sqlite-vecのコサイン類似度による KNN 検索
    - 上位 K 件取得

設定ファイル: config.toml

```toml
[search]
k = 5
```

#### 結果返却

- 基本: チャンク内容をそのまま返却
- 拡張: ドキュメント全体から該当章を抽出
- オプション: ファイル全体の返却も選択可能

### パフォーマンス最適化

#### メモリ管理

- メモリ解放をどこで行うか検討。
    - 同様のアプリで、テキストのベクトル化時に、メモリの使用量が増え続ける事象があった。
- （将来的に）MCPサーバー: 5-10 分間未使用でアンロード
    - 初めのリリース時は、MCP サーバー終了時にアンロード
- （将来的に）CLI コマンド: プロセス終了時に自動解放
- （将来的に）メモリ不足時: 自動アンロードで他アプリに譲る

#### モデルロード最適化

- 初回起動時のモデル読み込み
- メモリ常駐による後続処理高速化
- GPU 利用可能時の自動切り替え
    - CPU と Apple シリコン GPU（MPS 対応）の切り替え。Apple シリコン以外の GPU は非対応（環境が無い）。

設定ファイル: "config.toml"

```toml
[model]
auto_unload_minutes = 10  # 10分後にアンロード
memory_threshold = 0.8    # メモリ使用率80%超でアンロード
```

#### バッチ処理

- 複数ファイル同時処理（同期バッチ処理）
    - MacOS 用 MPS 対応では、バッチ処理は、百害あって一利無しだと検証で分かった。
- 並列処理による処理時間短縮
    - 検証の必要あり。ただし、初期リリースでは不要。

#### UI/UX

- プログレスバー表示（Rich活用）

#### キャッシュ戦略

検討・検証はしたいが、しばらくは不要。

- ファイル更新日時による差分更新
- 既存ベクトルの再利用
- 不要ベクトルの自動削除
