import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any


class DatabaseConnection:
    """データベース接続管理クラス"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._connection: Optional[sqlite3.Connection] = None
    
    def connect(self) -> sqlite3.Connection:
        """データベースに接続する"""
        if self._connection is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    def close(self) -> None:
        """データベース接続を閉じる"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """クエリを実行する"""
        conn = self.connect()
        return conn.execute(query, params)
    
    def executemany(self, query: str, params: List[tuple]) -> sqlite3.Cursor:
        """複数のクエリを実行する"""
        conn = self.connect()
        return conn.executemany(query, params)
    
    def commit(self) -> None:
        """変更をコミットする"""
        if self._connection:
            self._connection.commit()
    
    def rollback(self) -> None:
        """変更をロールバックする"""
        if self._connection:
            self._connection.rollback()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()


def create_database_connection(db_path: str) -> DatabaseConnection:
    """データベース接続を作成する"""
    return DatabaseConnection(db_path)