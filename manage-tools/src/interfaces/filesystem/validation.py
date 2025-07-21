from pathlib import Path
from typing import Tuple


def validate_directory_path(directory_path: str) -> Tuple[bool, str, str]:
    """Validate if the given path is a valid directory
    
    Args:
        directory_path: Path to validate
        
    Returns:
        Tuple of (is_valid, resolved_path, error_message)
        - is_valid: True if directory is valid
        - resolved_path: Absolute path as string (empty if invalid)
        - error_message: Error message (empty if valid)
    """
    try:
        path = Path(directory_path).resolve()
        
        if not path.exists():
            return False, "", f"Directory does not exist: {directory_path}"
        
        if not path.is_dir():
            return False, "", f"Path is not a directory: {directory_path}"
        
        return True, str(path), ""
    
    except Exception as e:
        return False, "", f"Invalid path: {directory_path} ({str(e)})"