from .connection import DatabaseConnection


def initialize_database(db_conn: DatabaseConnection) -> None:
    """データベースを初期化する（toolsテーブルを作成）"""
    db_conn.execute("""
        CREATE TABLE IF NOT EXISTS tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL,
            source_directory TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            app_version TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db_conn.commit()


def create_tool_tables(db_conn: DatabaseConnection, tool_id: int) -> None:
    """指定されたツール用のテーブルを作成する
    
    Args:
        db_conn: データベース接続
        tool_id: ツールID
    """
    # documentsテーブル
    db_conn.execute(f"""
        CREATE TABLE IF NOT EXISTS documents_{tool_id} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE CASCADE
        )
    """)
    
    # vectorsテーブル
    db_conn.execute(f"""
        CREATE TABLE IF NOT EXISTS vectors_{tool_id} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_id INTEGER NOT NULL,
            document_id INTEGER NOT NULL,
            chunk_text TEXT NOT NULL,
            start_position INTEGER NOT NULL,
            end_position INTEGER NOT NULL,
            embedding BLOB NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE CASCADE,
            FOREIGN KEY (document_id) REFERENCES documents_{tool_id}(id) ON DELETE CASCADE
        )
    """)
    
    # インデックス作成
    db_conn.execute(f"""
        CREATE INDEX IF NOT EXISTS idx_vectors_{tool_id}_embedding
        ON vectors_{tool_id} (embedding)
    """)
    
    db_conn.execute(f"""
        CREATE INDEX IF NOT EXISTS idx_vectors_{tool_id}_tool_doc
        ON vectors_{tool_id} (tool_id, document_id)
    """)
    
    db_conn.execute(f"""
        CREATE INDEX IF NOT EXISTS idx_documents_{tool_id}_tool
        ON documents_{tool_id} (tool_id)
    """)
    
    db_conn.execute(f"""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_{tool_id}_path_hash
        ON documents_{tool_id} (tool_id, file_path, content_hash)
    """)
    
    db_conn.execute(f"""
        CREATE INDEX IF NOT EXISTS idx_documents_{tool_id}_tool_path
        ON documents_{tool_id} (tool_id, file_path)
    """)
    
    db_conn.execute(f"""
        CREATE INDEX IF NOT EXISTS idx_vectors_{tool_id}_position
        ON vectors_{tool_id} (document_id, start_position, end_position)
    """)
    
    db_conn.commit()


def drop_tool_tables(db_conn: DatabaseConnection, tool_id: int) -> None:
    """指定されたツール用のテーブルを削除する
    
    Args:
        db_conn: データベース接続
        tool_id: ツールID
    """
    db_conn.execute(f"DROP TABLE IF EXISTS vectors_{tool_id}")
    db_conn.execute(f"DROP TABLE IF EXISTS documents_{tool_id}")
    db_conn.commit()