#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import text
from dparse.dependencies import Dependency, DependencyFile
from dparse.parser import Parser
from dparse import filetypes
from packaging.specifiers import SpecifierSet
import json
from dparse.dependencies import DparseJSONEncoder
import traceback

# Focus on testing specific edge cases and properties

# Bug Hunt 1: Test if empty package names are handled
print("Bug Hunt 1: Empty or invalid package names...")
try:
    dep = Dependency(name="", specs=SpecifierSet(), line="")
    print(f"  Created dependency with empty name: key='{dep.key}'")
    if dep.key == "":
        print("  ⚠️ Empty package name creates empty key")
except Exception as e:
    print(f"  ✗ Exception with empty name: {e}")

# Bug Hunt 2: Test special characters in package names
print("\nBug Hunt 2: Special characters in package names...")
special_names = ["pkg@123", "pkg#test", "pkg!ver", "pkg$money", "pkg%percent", 
                 "pkg&and", "pkg*star", "pkg+plus", "pkg=equal", "pkg?question",
                 "pkg[bracket]", "pkg{brace}", "pkg|pipe", "pkg\\backslash", 
                 "pkg/slash", "pkg:colon", "pkg;semicolon", "pkg<less", "pkg>greater"]

for name in special_names:
    try:
        dep = Dependency(name=name, specs=SpecifierSet(), line=name)
        print(f"  {name} -> key='{dep.key}'")
    except Exception as e:
        print(f"  ✗ Exception with {name}: {e}")

# Bug Hunt 3: Unicode in package names
print("\nBug Hunt 3: Unicode in package names...")
unicode_names = ["пакет", "包裹", "📦package", "café-lib", "naïve-pkg"]
for name in unicode_names:
    try:
        dep = Dependency(name=name, specs=SpecifierSet(), line=name)
        print(f"  {name} -> key='{dep.key}'")
    except Exception as e:
        print(f"  ✗ Exception with {name}: {e}")

# Bug Hunt 4: Extremely long package names
print("\nBug Hunt 4: Extremely long package names...")
long_name = "a" * 1000
try:
    dep = Dependency(name=long_name, specs=SpecifierSet(), line=long_name)
    print(f"  Created dependency with 1000-char name, key length: {len(dep.key)}")
except Exception as e:
    print(f"  ✗ Exception with long name: {e}")

# Bug Hunt 5: Test serialize/deserialize with edge cases
print("\nBug Hunt 5: Serialize/deserialize edge cases...")

# Test with None values
try:
    dep = Dependency(
        name="test",
        specs=SpecifierSet(),
        line="test",
        meta=None,
        extras=None,
        line_numbers=None,
        index_server=None,
        hashes=None,
        dependency_type=None,
        sections=None
    )
    serialized = dep.serialize()
    json_str = json.dumps(serialized, cls=DparseJSONEncoder)
    deserialized_dict = json.loads(json_str)
    if isinstance(deserialized_dict['specs'], str):
        deserialized_dict['specs'] = SpecifierSet(deserialized_dict['specs'])
    restored = Dependency.deserialize(deserialized_dict)
    print(f"  ✓ None values handled correctly")
except Exception as e:
    print(f"  ✗ Failed with None values: {e}")
    traceback.print_exc()

# Bug Hunt 6: Hash regex edge cases
print("\nBug Hunt 6: Hash regex pattern edge cases...")
from dparse.regex import HASH_REGEX
import re

test_patterns = [
    "--hash=:nocontent",  # Missing algorithm
    "--hash=sha256:",     # Missing hash value
    "--hash==sha256:abc", # Double equals
    "--hash  sha256:abc", # Multiple spaces
    "--hashsha256:abc",   # No separator
    "-- hash sha256:abc", # Space in --hash
]

for pattern in test_patterns:
    matches = re.findall(HASH_REGEX, pattern)
    if matches:
        print(f"  Pattern '{pattern}' matched: {matches}")

# Bug Hunt 7: Parser.parse_index_server edge cases
print("\nBug Hunt 7: Index server parsing edge cases...")

edge_cases = [
    "",                  # Empty string
    "-i",                # Just the flag
    "-i ",               # Flag with space
    "--index-url=",      # Empty URL
    "-i //",             # Protocol-relative URL
    "-i file:///path",   # File URL
    "-i ftp://server",   # FTP URL
]

for line in edge_cases:
    try:
        result = Parser.parse_index_server(line)
        print(f"  '{line}' -> {result}")
    except Exception as e:
        print(f"  '{line}' raised: {type(e).__name__}: {e}")

# Bug Hunt 8: DependencyFile with malformed content
print("\nBug Hunt 8: DependencyFile with malformed content...")

# Test with invalid JSON for Pipfile.lock
try:
    dep_file = DependencyFile(
        content='{"invalid json',
        file_type=filetypes.pipfile_lock
    )
    dep_file.parse()
    print(f"  Parsed invalid JSON without error")
except Exception as e:
    print(f"  ✓ Invalid JSON raised: {type(e).__name__}")

# Test with invalid TOML for Pipfile
try:
    dep_file = DependencyFile(
        content='[packages\ninvalid toml',
        file_type=filetypes.pipfile
    )
    dep_file.parse()
    print(f"  Parsed invalid TOML without error")
except Exception as e:
    print(f"  ✓ Invalid TOML handled: {type(e).__name__}")

# Bug Hunt 9: Extras with special characters
print("\nBug Hunt 9: Extras with special characters...")

special_extras = [
    ["test-dev"],
    ["test.dev"],
    ["test@dev"],
    ["test/dev"],
    [""],  # Empty extra
    ["a" * 100],  # Long extra
]

for extras in special_extras:
    try:
        dep = Dependency(name="pkg", specs=SpecifierSet(), line="pkg", extras=extras)
        full_name = dep.full_name
        print(f"  Extras {extras} -> {full_name}")
    except Exception as e:
        print(f"  ✗ Extras {extras} raised: {e}")

# Bug Hunt 10: File path resolution edge cases
print("\nBug Hunt 10: File path resolution...")

test_paths = [
    ("/base/path/req.txt", "-r ../other/req.txt"),
    ("/base/req.txt", "-r ./sub/req.txt"),
    ("/base/req.txt", "-r req2.txt"),
    ("/base/req.txt", "--requirement ../../../req.txt"),
]

for base_path, line in test_paths:
    try:
        result = Parser.resolve_file(base_path, line)
        print(f"  {base_path} + {line} -> {result}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")

print("\n" + "=" * 60)
print("Bug hunt complete. Review output for potential issues.")