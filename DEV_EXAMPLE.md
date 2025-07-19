# 開発実装例

## 依存性注入パターン

### DI コンテナ（関数型）

```python
from typing import Callable, Dict, Any, Protocol
from pathlib import Path

# 型定義
class EmbeddingModel(Protocol):
    def encode(self, text: str) -> list[float]: ...

class DatabaseConnection(Protocol):
    def save_vector(self, doc_id: str, vector: list[float]) -> None: ...

EmbeddingService = Callable[[str], list[float]]
DatabaseService = Callable[[str, list[float]], None]
DocumentProcessor = Callable[[str, str], None]

# 依存関係レジストリ
def create_dependencies(config: Dict[str, Any]) -> Dict[str, Any]:
    """アプリケーションの依存関係を作成する"""
    # モデル読み込み（重い処理は一度だけ）
    model = load_embedding_model(config['model_path'])
    db_conn = create_database_connection(config['db_path'])
    
    return {
        'embedding_service': create_embedding_service(model),
        'database_service': create_database_service(db_conn),
        'config': config
    }

# 依存関係の取得
def get_dependency(deps: Dict[str, Any], key: str) -> Any:
    """依存関係を型安全に取得する"""
    if key not in deps:
        raise ValueError(f"Dependency '{key}' not found")
    return deps[key]
```

### ファクトリー関数

```python
# サービス層のファクトリー
def create_embedding_service(model: EmbeddingModel) -> EmbeddingService:
    """埋め込みサービスを作成する"""
    def embed_text(text: str) -> list[float]:
        # 純粋関数：外部状態に依存しない
        return model.encode(text)
    
    return embed_text

def create_database_service(db_conn: DatabaseConnection) -> DatabaseService:
    """データベースサービスを作成する"""
    def save_vector(doc_id: str, vector: list[float]) -> None:
        # I/O操作：副作用あり
        db_conn.save_vector(doc_id, vector)
    
    return save_vector

# アプリケーション層のファクトリー
def create_document_processor(deps: Dict[str, Any]) -> DocumentProcessor:
    """ドキュメント処理器を作成する"""
    embedding_service = get_dependency(deps, 'embedding_service')
    database_service = get_dependency(deps, 'database_service')
    
    def process_document(doc_id: str, content: str) -> None:
        # ビジネスロジック：純粋関数 + 副作用の組み合わせ
        vector = embedding_service(content)  # 純粋関数
        database_service(doc_id, vector)     # 副作用
    
    return process_document

def create_mcp_server(deps: Dict[str, Any]) -> Callable:
    """MCP サーバーを作成する"""
    document_processor = create_document_processor(deps)
    
    def mcp_server():
        # MCP サーバーの実装
        pass
    
    return mcp_server
```

### アプリケーション初期化

```python
# main.py
def main() -> None:
    """アプリケーションのエントリーポイント"""
    # 1. 設定読み込み
    config = load_config()
    
    # 2. 依存関係構築
    deps = create_dependencies(config)
    
    # 3. アプリケーション作成
    document_processor = create_document_processor(deps)
    mcp_server = create_mcp_server(deps)
    
    # 4. アプリケーション実行
    run_application(mcp_server)

# CLI エントリーポイント
def cli_main() -> None:
    """CLI コマンドのエントリーポイント"""
    config = load_cli_config()
    deps = create_dependencies(config)
    
    # CLI 固有の処理
    cli_processor = create_cli_processor(deps)
    cli_processor.run()

if __name__ == "__main__":
    main()
```

### テスト時の依存関係差し替え

```python
# tests/test_document_processor.py
import pytest
from unittest.mock import Mock

def test_document_processor():
    """ドキュメント処理のテスト"""
    # モック作成
    mock_embedding_service = Mock(return_value=[0.1, 0.2, 0.3])
    mock_database_service = Mock()
    
    # テスト用依存関係
    test_deps = {
        'embedding_service': mock_embedding_service,
        'database_service': mock_database_service,
        'config': {'test': True}
    }
    
    # テスト対象作成
    processor = create_document_processor(test_deps)
    
    # テスト実行
    processor("doc1", "test content")
    
    # アサーション
    mock_embedding_service.assert_called_once_with("test content")
    mock_database_service.assert_called_once_with("doc1", [0.1, 0.2, 0.3])
```

## 関数型コア / 命令型シェルパターン

### core/ 層（純粋関数）

```python
# core/embedding.py
def embed_text(text: str, model: EmbeddingModel) -> list[float]:
    """テキストを埋め込みベクトルに変換する（純粋関数）"""
    return model.encode(text)

def calculate_similarity(vector1: list[float], vector2: list[float]) -> float:
    """ベクトル間の類似度を計算する（純粋関数）"""
    # コサイン類似度の計算
    pass
```

### interfaces/ 層（副作用あり）

```python
# interfaces/database.py
def save_vector_to_db(doc_id: str, vector: list[float], db_path: str) -> None:
    """ベクトルをデータベースに保存する（副作用あり）"""
    # SQLite への保存処理
    pass

def load_model_from_file(model_path: str) -> EmbeddingModel:
    """ファイルからモデルを読み込む（副作用あり）"""
    # ファイルI/O + モデル初期化
    pass
```
