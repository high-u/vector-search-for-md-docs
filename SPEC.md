# アプリケーション仕様

## 機能

### マークダウンファイルをベクトル化してデータベースに登録

- 複数のマークダウンファイルの一括取り込み
    - サブディレクトリも再帰探索
- ドキュメント種別毎に処理
    - MCP サーバーでは、ドキュメント種別毎にツールを提供
    - データベースへの取り込み時（ベクトル化時）に取り込む先（ツール）を選択
- 対象のツール（ドキュメント種別）毎のテーブル再構築（テーブル削除 → テーブル構築）
- データ追加対応
    - "ファイルパス" と "ファイル内容のハッシュ値" を保存
        - ファイルを取り込むディレクトリをツール毎に設定
    - 存在しないファイルのデータは削除

### MCP サーバーでドキュメント種別毎にツールを提供

- ドキュメントの種別毎に、ツールを分けるため、ツール管理テーブルを持つ
- ツール管理テーブルは 1 テーブルだが、ベクトルデータを登録するテーブルは、ツール毎に分ける
- アプリ起動時に、データベースからツール情報を取得し、動的なツール登録
- ツール管理テーブルで、有効／無効（ツール登録するか、しないか）を管理できても良い。今、MCP クライアント側に、有効／無効のフラグあるけど、ここでも持つ？

テーブルを 1 つにするか、分けるか、の検討

- アプリのバージョンアップ（スキーマ変更を含む）を考えた場合、テーブルを分けて、ツール管理テーブルにアプリバージョンを入れておくことで、データ移行不要で、後方互換性を保ちやすいか。
- 分けることのデメリットは特に無い？

### ベクトル検索と全文検索

- ベクトル検索をまずは実装
- （将来的に）全文検索
    - MCP クライアント側の LLM に単語抽出をやってもらう、か、形態素解析を導入するか

## コマンド

### ベクトル化とデータベース登録

- 引数
    - ドキュメントが存在するフォルダ
    - ツール（取り込み先）
    - 出力データベース（新規 or 既存）
    - （将来的に）モデル選択

### ツール登録

- 引数
    - ツール名
    - ツール詳細（LLM への説明）

## 制約

- 最大ファイル数、最大トータルファイルサイズ、など決める？ → 一旦無しで良いか。
- CPU もしくは Apple シリコンの GPU 利用（MPS 対応）のみ。MacOS 以外の GPU 対応は追々。
- モデル選択は無し。
- MCP サーバーは STDIO インターフェース
