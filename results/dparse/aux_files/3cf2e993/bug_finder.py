#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

print("Bug Hunting in dparse.parser...")
print("=" * 60)

# Import modules
from dparse.parser import Parser
from dparse.dependencies import Dependency, DependencyFile
from packaging.specifiers import SpecifierSet
import re
from dparse.regex import HASH_REGEX

# Bug Hunt 1: parse_index_server edge cases
print("\n1. Testing parse_index_server with edge cases...")
edge_cases = [
    "",  # Empty string
    "   ",  # Whitespace only
    "--index-url",  # No URL provided
    "-i",  # No URL provided
    "--index-url=",  # Empty URL
    "-i=",  # Empty URL
    "--index-url    ",  # Trailing spaces
]

for test_input in edge_cases:
    try:
        result = Parser.parse_index_server(test_input)
        print(f"  Input: '{test_input}' -> Result: {result}")
    except Exception as e:
        print(f"  Input: '{test_input}' -> EXCEPTION: {e}")

# Bug Hunt 2: parse_hashes with special characters
print("\n2. Testing parse_hashes with special inputs...")
special_cases = [
    "",  # Empty
    "--hash=:",  # Missing parts
    "--hash=sha256:",  # Missing value
    "--hash=:abc123",  # Missing algorithm
    "text --hash=sha256:abc --hash=sha256:abc",  # Duplicate hashes
]

for test_input in special_cases:
    try:
        cleaned, hashes = Parser.parse_hashes(test_input)
        print(f"  Input: '{test_input}'")
        print(f"    Cleaned: '{cleaned}', Hashes: {hashes}")
    except Exception as e:
        print(f"  Input: '{test_input}' -> EXCEPTION: {e}")

# Bug Hunt 3: resolve_file with path traversal
print("\n3. Testing resolve_file with path traversal...")
traversal_cases = [
    (".", "."),
    ("..", ".."),
    ("../../../etc/passwd", "../../../etc/passwd"),
    ("", ""),
    ("/", "/"),
    ("//", "//"),
]

for base_path, line_path in traversal_cases:
    try:
        for prefix in ["-r ", "--requirement "]:
            line = prefix + line_path
            result = Parser.resolve_file(base_path, line)
            print(f"  Base: '{base_path}', Line: '{line}' -> '{result}'")
    except Exception as e:
        print(f"  Base: '{base_path}', Line: '{line}' -> EXCEPTION: {e}")

# Bug Hunt 4: Dependency with None values
print("\n4. Testing Dependency with None/empty values...")
try:
    dep = Dependency(name=None, specs=None, line=None)
    print(f"  Created Dependency with None values")
    print(f"    name: {dep.name}, key: {dep.key}, line: {dep.line}")
except Exception as e:
    print(f"  EXCEPTION creating Dependency with None: {e}")

try:
    dep = Dependency(name="", specs=SpecifierSet(), line="")
    print(f"  Created Dependency with empty strings")
    print(f"    name: '{dep.name}', key: '{dep.key}', line: '{dep.line}'")
    print(f"    full_name: '{dep.full_name}'")
except Exception as e:
    print(f"  EXCEPTION creating Dependency with empty: {e}")

# Bug Hunt 5: DependencyFile with unknown extensions
print("\n5. Testing DependencyFile with unknown file extensions...")
unknown_extensions = [
    "file.unknown",
    "file",
    ".hidden",
    "file.123",
    "file.txt.bak",
]

for filename in unknown_extensions:
    try:
        dep_file = DependencyFile(content="", path=filename)
        print(f"  File '{filename}' -> Parser: {dep_file.parser.__class__.__name__}")
    except Exception as e:
        print(f"  File '{filename}' -> EXCEPTION: {type(e).__name__}: {e}")

# Bug Hunt 6: SetupCfgParser section.name bug
print("\n6. Checking SetupCfgParser for potential bug...")
setup_cfg_content = """
[options]
install_requires = 
    package1==1.0.0
    package2>=2.0.0
"""

try:
    from dparse.parser import SetupCfgParser
    dep_file = DependencyFile(content=setup_cfg_content, file_type="setup.cfg")
    # Try to parse - this might reveal the bug in line 416 of parser.py
    dep_file.parse()
    print(f"  SetupCfgParser parsed successfully")
    print(f"  Found {len(dep_file.dependencies)} dependencies")
except AttributeError as e:
    print(f"  ❌ BUG FOUND: SetupCfgParser has AttributeError: {e}")
except Exception as e:
    print(f"  Other exception: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("Bug hunting complete!")