from pathlib import Path
from typing import Dict, Any
import tomllib


def load_config(config_path: str = "config.toml") -> Dict[str, Any]:
    """設定ファイルを読み込む
    
    Args:
        config_path: 設定ファイルのパス
        
    Returns:
        設定辞書
        
    Raises:
        FileNotFoundError: 設定ファイルが存在しない場合
        ValueError: 必須設定が不足している場合
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, "rb") as f:
        config = tomllib.load(f)
    
    _validate_config(config)
    return config


def _validate_config(config: Dict[str, Any]) -> None:
    """設定ファイルの必須項目をチェックする
    
    Args:
        config: 設定辞書
        
    Raises:
        ValueError: 必須設定が不足している場合
    """
    required_sections = ["database", "chunking", "display"]
    required_keys = {
        "database": ["path"],
        "chunking": ["size", "overlap"],
        "display": ["default_format"]
    }
    
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Required configuration section '{section}' is missing")
        
        for key in required_keys[section]:
            if key not in config[section]:
                raise ValueError(f"Required configuration key '{section}.{key}' is missing")