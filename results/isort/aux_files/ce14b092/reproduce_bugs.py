"""Minimal reproducers for the bugs found in isort.core"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort.format import format_natural, format_simplified
from isort.settings import Config
import isort.core

print("Bug 1: format_natural with empty string")
print("="*50)
result = format_natural("")
print(f"format_natural('') = '{result}'")
print(f"Expected: ''")
print(f"Actual: '{result}'")
print(f"Bug: Returns 'import ' for empty input instead of empty string\n")

print("Bug 2: Round-trip failure for dotted imports")
print("="*50)
import_line = "import a.a"
simplified = format_simplified(import_line)
restored = format_natural(simplified)
print(f"Original: '{import_line}'")
print(f"Simplified: '{simplified}'")
print(f"Restored: '{restored}'")
print(f"Bug: 'import a.a' becomes 'from a import a' (semantically different!)\n")

print("Bug 3: _indented_config with empty indent")
print("="*50)
config = Config(line_length=0)
indented = isort.core._indented_config(config, "")
print(f"Original config lines_after_imports: {config.lines_after_imports}")
print(f"Indented config lines_after_imports: {indented.lines_after_imports}")
print(f"Expected lines_after_imports: 1")
print(f"Bug: When indent is empty, _indented_config returns original config instead of modified one")