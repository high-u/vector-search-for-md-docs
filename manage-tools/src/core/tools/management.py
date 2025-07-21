from typing import Optional, List, Dict, Any, Callable, Tuple
from datetime import datetime
import re

from ...interfaces.database.connection import DatabaseConnection
from ...interfaces.database.schema import create_tool_tables, drop_tool_tables


def _validate_tool_name(name: str) -> None:
    """Validate tool name
    
    Args:
        name: Tool name to validate
        
    Raises:
        ValueError: If tool name is invalid
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
    validate_directory: Callable[[str], Tuple[bool, str, str]],
    app_version: Optional[str] = None
) -> int:
    """Add a new tool
    
    Args:
        db_conn: Database connection
        name: Tool name
        description: Tool description
        source_directory: Source directory path
        validate_directory: Function to validate directory path
        app_version: Application version
        
    Returns:
        Created tool ID
        
    Raises:
        ValueError: If tool name is invalid or already exists
        FileNotFoundError: If source directory validation fails
    """
    # Tool name validation
    _validate_tool_name(name)
    
    # Directory validation
    is_valid, resolved_path, error_msg = validate_directory(source_directory)
    if not is_valid:
        if "does not exist" in error_msg:
            raise FileNotFoundError(error_msg)
        else:
            raise ValueError(error_msg)
    
    # Check for duplicate tool name
    existing_tool = get_tool_by_name(db_conn, name)
    if existing_tool is not None:
        raise ValueError(f"Tool '{name}' already exists")
    
    # Add tool
    cursor = db_conn.execute(
        """
        INSERT INTO tools (name, description, source_directory, app_version)
        VALUES (?, ?, ?, ?)
        """,
        (name, description, resolved_path, app_version)
    )
    
    tool_id = cursor.lastrowid
    
    # Create tool tables
    create_tool_tables(db_conn, tool_id)
    
    db_conn.commit()
    return tool_id


def get_tool_by_name(db_conn: DatabaseConnection, name: str) -> Optional[Dict[str, Any]]:
    """Get tool by name
    
    Args:
        db_conn: Database connection
        name: Tool name
        
    Returns:
        Tool information (None if not found)
    """
    cursor = db_conn.execute(
        "SELECT * FROM tools WHERE name = ?",
        (name,)
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def get_tool_by_id(db_conn: DatabaseConnection, tool_id: int) -> Optional[Dict[str, Any]]:
    """Get tool by ID
    
    Args:
        db_conn: Database connection
        tool_id: Tool ID
        
    Returns:
        Tool information (None if not found)
    """
    cursor = db_conn.execute(
        "SELECT * FROM tools WHERE id = ?",
        (tool_id,)
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def list_tools(db_conn: DatabaseConnection, active_only: bool = False) -> List[Dict[str, Any]]:
    """Get list of tools
    
    Args:
        db_conn: Database connection
        active_only: Whether to get only active tools
        
    Returns:
        List of tools
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
    validate_directory: Callable[[str], Tuple[bool, str, str]],
    description: Optional[str] = None,
    source_directory: Optional[str] = None
) -> bool:
    """Update tool information
    
    Args:
        db_conn: Database connection
        name: Tool name
        validate_directory: Function to validate directory path
        description: New description (skip update if None)
        source_directory: New source directory (skip update if None)
        
    Returns:
        Whether update was successful
        
    Raises:
        FileNotFoundError: If source directory validation fails
    """
    # Check tool existence
    tool = get_tool_by_name(db_conn, name)
    if tool is None:
        return False
    
    # Prepare update fields
    update_fields = []
    params = []
    
    if description is not None:
        update_fields.append("description = ?")
        params.append(description)
    
    if source_directory is not None:
        is_valid, resolved_path, error_msg = validate_directory(source_directory)
        if not is_valid:
            if "does not exist" in error_msg:
                raise FileNotFoundError(error_msg)
            else:
                raise ValueError(error_msg)
        
        update_fields.append("source_directory = ?")
        params.append(resolved_path)
    
    if not update_fields:
        return True  # No fields to update
    
    update_fields.append("updated_at = ?")
    params.append(datetime.now().isoformat())
    params.append(name)
    
    query = f"UPDATE tools SET {', '.join(update_fields)} WHERE name = ?"
    db_conn.execute(query, params)
    db_conn.commit()
    
    return True


def delete_tool(db_conn: DatabaseConnection, name: str) -> bool:
    """Delete a tool
    
    Args:
        db_conn: Database connection
        name: Tool name
        
    Returns:
        Whether deletion was successful
    """
    # Check tool existence
    tool = get_tool_by_name(db_conn, name)
    if tool is None:
        return False
    
    tool_id = tool["id"]
    
    # Drop tool tables
    drop_tool_tables(db_conn, tool_id)
    
    # Delete tool
    db_conn.execute("DELETE FROM tools WHERE name = ?", (name,))
    db_conn.commit()
    
    return True


def enable_tool(db_conn: DatabaseConnection, name: str) -> bool:
    """Enable a tool
    
    Args:
        db_conn: Database connection
        name: Tool name
        
    Returns:
        Whether enabling was successful
    """
    return _set_tool_active_status(db_conn, name, True)


def disable_tool(db_conn: DatabaseConnection, name: str) -> bool:
    """Disable a tool
    
    Args:
        db_conn: Database connection
        name: Tool name
        
    Returns:
        Whether disabling was successful
    """
    return _set_tool_active_status(db_conn, name, False)


def _set_tool_active_status(db_conn: DatabaseConnection, name: str, is_active: bool) -> bool:
    """Set tool active/inactive status
    
    Args:
        db_conn: Database connection
        name: Tool name
        is_active: Active status
        
    Returns:
        Whether setting status was successful
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