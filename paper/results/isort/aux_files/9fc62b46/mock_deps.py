"""Minimal mock implementations needed to test place.py"""
from pathlib import Path
from typing import FrozenSet, List, Tuple, Any
import re

# Mock sections module constants
class sections:
    FUTURE = "FUTURE"
    STDLIB = "STDLIB"
    THIRDPARTY = "THIRDPARTY"
    FIRSTPARTY = "FIRSTPARTY"
    LOCALFOLDER = "LOCALFOLDER"


# Mock Config class
class Config:
    def __init__(self, 
                 forced_separate=None,
                 known_patterns=None,
                 src_paths=None,
                 namespace_packages=None,
                 auto_identify_namespace_packages=False,
                 supported_extensions=None,
                 sections=None,
                 default_section="THIRDPARTY"):
        self.forced_separate = forced_separate or []
        self.known_patterns = known_patterns or []
        self.src_paths = src_paths or [Path(".")]
        self.namespace_packages = namespace_packages or frozenset()
        self.auto_identify_namespace_packages = auto_identify_namespace_packages
        self.supported_extensions = supported_extensions or frozenset(["py", "pyi", "pyx"])
        self.sections = sections or {
            "FUTURE", "STDLIB", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"
        }
        self.default_section = default_section


DEFAULT_CONFIG = Config()


# Mock utils module
def exists_case_sensitive(path: str) -> bool:
    """Mock implementation that just checks if path exists."""
    return Path(path).exists()