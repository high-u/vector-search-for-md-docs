# 技術スタック

## 開発言語

- Python 3.12 (最低要件としては 3.9)

## 埋め込みモデル

- [pfnet/plamo-embedding-1b](https://huggingface.co/pfnet/plamo-embedding-1b)

## フレームワーク・ライブラリ

### コマンド開発

- [fastapi/typer](https://github.com/fastapi/typer)
    - Rich も使用（プログレスバー等）
    - `pip install typer[rich]`

### MCP サーバー開発

- [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)

### データベース・ベクトル検索

- sqlite3 (標準ライブラリー)
- [asg017/sqlite-vec](https://github.com/asg017/sqlite-vec)

### 埋め込みモデル

- [huggingface/transformers](https://github.com/huggingface/transformers)
- [pytorch/pytorch](https://github.com/pytorch/pytorch)

### ベクトル処理

- 標準 [numpy/numpy](https://github.com/numpy/numpy)

### 依存性注入／DI コンテナ

ライブラリ使用不使用

### ファイル処理

- 標準 pathlib

## テスト

### テストフレームワーク

- [pytest-dev/pytest](https://github.com/pytest-dev/pytest)

### モック

- [pytest-dev/pytest-mock](https://github.com/pytest-dev/pytest-mock)

## パッケージ管理

- [astral-sh/uv](https://github.com/astral-sh/uv)
