from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

from ...interfaces.database.connection import DatabaseConnection
from ...interfaces.database.schema import create_tool_tables, drop_tool_tables


def _validate_tool_name(name: str) -> None:
    """ツール名のバリデーションを行う
    
    Args:
        name: ツール名
        
    Raises:
        ValueError: ツール名が無効な場合
    """
    if not name:
        raise ValueError("Tool name cannot be empty")
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        raise ValueError("Tool name can only contain letters, numbers, hyphens (-), and underscores (_)")
    
    if len(name) > 64:
        raise ValueError("Tool name must be 64 characters or less")


def add_tool(
    db_conn: DatabaseConnection,
    name: str,
    description: str,
    source_directory: str,
    app_version: Optional[str] = None
) -> int:
    """新しいツールを追加する
    
    Args:
        db_conn: データベース接続
        name: ツール名
        description: ツールの説明
        source_directory: ソースディレクトリ（絶対パス）
        app_version: アプリバージョン
        
    Returns:
        作成されたツールのID
        
    Raises:
        ValueError: ツール名が既に存在する場合や無効な場合
        FileNotFoundError: ソースディレクトリが存在しない場合
    """
    # ツール名のバリデーション
    _validate_tool_name(name)
    
    # ソースディレクトリの存在確認
    source_path = Path(source_directory).resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source_directory}")
    if not source_path.is_dir():
        raise ValueError(f"Source path is not a directory: {source_directory}")
    
    # ツール名の重複確認
    existing_tool = get_tool_by_name(db_conn, name)
    if existing_tool is not None:
        raise ValueError(f"Tool '{name}' already exists")
    
    # ツール追加
    cursor = db_conn.execute(
        """
        INSERT INTO tools (name, description, source_directory, app_version)
        VALUES (?, ?, ?, ?)
        """,
        (name, description, str(source_path), app_version)
    )
    
    tool_id = cursor.lastrowid
    
    # ツール用テーブル作成
    create_tool_tables(db_conn, tool_id)
    
    db_conn.commit()
    return tool_id


def get_tool_by_name(db_conn: DatabaseConnection, name: str) -> Optional[Dict[str, Any]]:
    """名前でツールを取得する
    
    Args:
        db_conn: データベース接続
        name: ツール名
        
    Returns:
        ツール情報（存在しない場合はNone）
    """
    cursor = db_conn.execute(
        "SELECT * FROM tools WHERE name = ?",
        (name,)
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def get_tool_by_id(db_conn: DatabaseConnection, tool_id: int) -> Optional[Dict[str, Any]]:
    """IDでツールを取得する
    
    Args:
        db_conn: データベース接続
        tool_id: ツールID
        
    Returns:
        ツール情報（存在しない場合はNone）
    """
    cursor = db_conn.execute(
        "SELECT * FROM tools WHERE id = ?",
        (tool_id,)
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def list_tools(db_conn: DatabaseConnection, active_only: bool = False) -> List[Dict[str, Any]]:
    """ツール一覧を取得する
    
    Args:
        db_conn: データベース接続
        active_only: 有効なツールのみ取得するかどうか
        
    Returns:
        ツール一覧
    """
    query = "SELECT * FROM tools"
    params = ()
    
    if active_only:
        query += " WHERE is_active = 1"
    
    query += " ORDER BY name"
    
    cursor = db_conn.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def update_tool(
    db_conn: DatabaseConnection,
    name: str,
    description: Optional[str] = None,
    source_directory: Optional[str] = None
) -> bool:
    """ツール情報を更新する
    
    Args:
        db_conn: データベース接続
        name: ツール名
        description: 新しい説明（Noneの場合は更新しない）
        source_directory: 新しいソースディレクトリ（Noneの場合は更新しない）
        
    Returns:
        更新が成功したかどうか
        
    Raises:
        FileNotFoundError: ソースディレクトリが存在しない場合
    """
    # ツールの存在確認
    tool = get_tool_by_name(db_conn, name)
    if tool is None:
        return False
    
    # 更新フィールドの準備
    update_fields = []
    params = []
    
    if description is not None:
        update_fields.append("description = ?")
        params.append(description)
    
    if source_directory is not None:
        source_path = Path(source_directory).resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Source directory does not exist: {source_directory}")
        if not source_path.is_dir():
            raise ValueError(f"Source path is not a directory: {source_directory}")
        
        update_fields.append("source_directory = ?")
        params.append(str(source_path))
    
    if not update_fields:
        return True  # 更新する項目がない場合は成功とする
    
    update_fields.append("updated_at = ?")
    params.append(datetime.now().isoformat())
    params.append(name)
    
    query = f"UPDATE tools SET {', '.join(update_fields)} WHERE name = ?"
    db_conn.execute(query, params)
    db_conn.commit()
    
    return True


def delete_tool(db_conn: DatabaseConnection, name: str) -> bool:
    """ツールを削除する
    
    Args:
        db_conn: データベース接続
        name: ツール名
        
    Returns:
        削除が成功したかどうか
    """
    # ツールの存在確認
    tool = get_tool_by_name(db_conn, name)
    if tool is None:
        return False
    
    tool_id = tool["id"]
    
    # ツール用テーブル削除
    drop_tool_tables(db_conn, tool_id)
    
    # ツール削除
    db_conn.execute("DELETE FROM tools WHERE name = ?", (name,))
    db_conn.commit()
    
    return True


def enable_tool(db_conn: DatabaseConnection, name: str) -> bool:
    """ツールを有効化する
    
    Args:
        db_conn: データベース接続
        name: ツール名
        
    Returns:
        有効化が成功したかどうか
    """
    return _set_tool_active_status(db_conn, name, True)


def disable_tool(db_conn: DatabaseConnection, name: str) -> bool:
    """ツールを無効化する
    
    Args:
        db_conn: データベース接続
        name: ツール名
        
    Returns:
        無効化が成功したかどうか
    """
    return _set_tool_active_status(db_conn, name, False)


def _set_tool_active_status(db_conn: DatabaseConnection, name: str, is_active: bool) -> bool:
    """ツールの有効/無効状態を設定する
    
    Args:
        db_conn: データベース接続
        name: ツール名
        is_active: 有効状態
        
    Returns:
        設定が成功したかどうか
    """
    tool = get_tool_by_name(db_conn, name)
    if tool is None:
        return False
    
    db_conn.execute(
        "UPDATE tools SET is_active = ?, updated_at = ? WHERE name = ?",
        (is_active, datetime.now().isoformat(), name)
    )
    db_conn.commit()
    
    return True