"""
A simple loader module to demonstrate property-based testing.
This module provides functionality for loading and processing data.
"""

import json
import pickle
import csv
from typing import Any, Dict, List, Union
from pathlib import Path


class DataLoader:
    """Loads data from various formats."""
    
    def __init__(self):
        self.cache = {}
        
    def load_json(self, data: str) -> Any:
        """Parse JSON string and return Python object."""
        return json.loads(data)
    
    def save_json(self, obj: Any) -> str:
        """Convert Python object to JSON string."""
        return json.dumps(obj)
    
    def merge_dicts(self, d1: Dict, d2: Dict) -> Dict:
        """Merge two dictionaries, with d2 values overwriting d1."""
        result = d1.copy()
        result.update(d2)
        return result
    
    def filter_by_key(self, data: List[Dict], key: str, value: Any) -> List[Dict]:
        """Filter list of dictionaries by a specific key-value pair."""
        return [item for item in data if item.get(key) == value]
    
    def normalize_path(self, path: str) -> str:
        """Normalize a file path by resolving .. and . components."""
        return str(Path(path).resolve())
    
    def split_by_delimiter(self, text: str, delimiter: str = ',') -> List[str]:
        """Split text by delimiter and strip whitespace."""
        if not delimiter:
            return [text]
        return [part.strip() for part in text.split(delimiter)]
    
    def join_with_delimiter(self, items: List[str], delimiter: str = ',') -> str:
        """Join list of strings with delimiter."""
        return delimiter.join(items)
    
    def encode_decode_bytes(self, text: str, encoding: str = 'utf-8') -> str:
        """Encode string to bytes and decode back."""
        return text.encode(encoding).decode(encoding)
    
    def remove_duplicates(self, items: List) -> List:
        """Remove duplicates while preserving order."""
        seen = set()
        result = []
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result
    
    def chunk_list(self, items: List, chunk_size: int) -> List[List]:
        """Split list into chunks of specified size."""
        if chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
    
    def flatten_list(self, nested: List[List]) -> List:
        """Flatten a list of lists into a single list."""
        return [item for sublist in nested for item in sublist]
    
    def get_nested_value(self, data: Dict, path: str, default=None):
        """Get value from nested dictionary using dot notation path."""
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set_nested_value(self, data: Dict, path: str, value: Any) -> Dict:
        """Set value in nested dictionary using dot notation path."""
        keys = path.split('.')
        result = data.copy()
        current = result
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        return result


def process_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Process configuration dictionary with defaults."""
    defaults = {
        'timeout': 30,
        'retries': 3,
        'debug': False
    }
    result = defaults.copy()
    result.update(config)
    return result


def validate_email(email: str) -> bool:
    """Basic email validation."""
    if '@' not in email:
        return False
    parts = email.split('@')
    if len(parts) != 2:
        return False
    local, domain = parts
    if not local or not domain:
        return False
    if '.' not in domain:
        return False
    return True


def parse_version(version: str) -> tuple:
    """Parse version string like '1.2.3' into tuple of integers."""
    parts = version.split('.')
    return tuple(int(p) for p in parts)


def compare_versions(v1: str, v2: str) -> int:
    """Compare two version strings. Returns -1 if v1 < v2, 0 if equal, 1 if v1 > v2."""
    t1 = parse_version(v1)
    t2 = parse_version(v2)
    
    if t1 < t2:
        return -1
    elif t1 > t2:
        return 1
    else:
        return 0