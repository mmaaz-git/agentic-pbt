#!/usr/bin/env python3
"""
Static analysis of dparse to identify potential bugs
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

print("Static Bug Analysis of dparse")
print("=" * 60)

# Import the modules
from dparse.dependencies import Dependency, DependencyFile
from dparse.parser import Parser
from packaging.specifiers import SpecifierSet
import json
from dparse.dependencies import DparseJSONEncoder

# Bug 1: Empty package name handling
print("\n1. POTENTIAL BUG: Empty package name handling")
print("-" * 40)
try:
    dep = Dependency(name="", specs=SpecifierSet(), line="")
    print(f"Empty name creates key: '{dep.key}'")
    print(f"Empty name full_name: '{dep.full_name}'")
    
    # Try to serialize/deserialize
    serialized = dep.serialize()
    json_str = json.dumps(serialized, cls=DparseJSONEncoder)
    deserialized = json.loads(json_str)
    deserialized['specs'] = SpecifierSet(deserialized['specs'])
    restored = Dependency.deserialize(deserialized)
    print(f"Serialization roundtrip successful")
    print("✓ Empty name appears to be handled (but may cause issues downstream)")
except Exception as e:
    print(f"✗ BUG FOUND: Empty name causes: {e}")

# Bug 2: Special characters in dependency key
print("\n2. POTENTIAL BUG: Special characters in key transformation")
print("-" * 40)
test_names = [
    ("Package_Name", "package-name"),  # Expected
    ("PACKAGE", "package"),  # Expected
    ("pkg-name", "pkg-name"),  # Dash should be preserved
    ("pkg--name", "pkg--name"),  # Double dash
    ("_pkg", "-pkg"),  # Starts with underscore -> starts with dash
    ("pkg_", "pkg-"),  # Ends with underscore -> ends with dash
    ("__pkg__", "--pkg--"),  # Multiple underscores -> multiple dashes
]

for name, expected in test_names:
    dep = Dependency(name=name, specs=SpecifierSet(), line=name)
    if dep.key != expected:
        print(f"✗ Unexpected: '{name}' -> '{dep.key}' (expected '{expected}')")
    else:
        print(f"✓ Correct: '{name}' -> '{dep.key}'")

# Bug 3: Index server URL edge cases
print("\n3. POTENTIAL BUG: Index server parsing edge cases")
print("-" * 40)

# Looking at parser.py lines 186-191:
# The code splits by pattern r"[=\s]+" and takes groups[1]
# This could fail with certain inputs

test_cases = [
    "-i",  # No URL
    "-i ",  # Just space
    "--index-url=",  # Empty after =
    "-i  http://example.com",  # Double space
    "--index-url = http://example.com",  # Space around =
]

for line in test_cases:
    try:
        result = Parser.parse_index_server(line)
        print(f"'{line}' -> {repr(result)}")
        if result == "/":
            print("  ⚠️ WARNING: Returns '/' for edge case")
    except IndexError as e:
        print(f"✗ BUG: IndexError on '{line}': {e}")
    except Exception as e:
        print(f"✗ BUG: Exception on '{line}': {e}")

# Bug 4: Hash regex pattern analysis
print("\n4. ANALYZING: Hash regex pattern")
print("-" * 40)
from dparse.regex import HASH_REGEX
import re

print(f"Hash regex pattern: {HASH_REGEX}")
print("This pattern matches: --hash[=| ]\\w+:\\w+")

# Edge cases the regex might not handle correctly:
edge_patterns = [
    "--hash=sha256:abc123",  # Standard - should match
    "--hash sha256:abc123",  # Space separator - should match
    "--hash:sha256:abc123",  # Colon separator - shouldn't match
    "--hash==sha256:abc123",  # Double equals - shouldn't match
    "--hash=SHA256:ABC123",  # Uppercase - should match
    "--hash=sha-256:abc-123",  # Hyphens in algorithm/hash - won't match!
    "--hash=sha256:abc/def",  # Slash in hash - won't match!
    "--hash=sha256:abc+def",  # Plus in hash - won't match!
]

for pattern in edge_patterns:
    matches = re.findall(HASH_REGEX, pattern)
    if matches:
        print(f"✓ Matches: '{pattern}' -> {matches}")
    else:
        print(f"✗ No match: '{pattern}'")

print("\n⚠️ ISSUE: The regex uses \\w+ which only matches [a-zA-Z0-9_]")
print("   Real hashes often contain characters like +, /, =")
print("   Example SHA256 base64: 'Xr8YgfP+MOdL92v/K8dkJY3lj4g7wW7L1X0='")

# Bug 5: Requirements line continuation handling
print("\n5. ANALYZING: Line continuation (backslash) handling")
print("-" * 40)
print("From parser.py lines 266-274:")
print("The code handles multiline requirements with backslashes")
print("Potential issue: The iteration uses self.iter_lines(num + 1)")
print("This could skip lines if multiple continuations exist")

# Bug 6: Dependency file type detection
print("\n6. ANALYZING: File type detection logic")
print("-" * 40)
print("From dependencies.py lines 151-167:")
print("File type detection based on path endings")

test_paths = [
    "requirements.txt",  # Should work
    "requirements.TXT",  # Case sensitive?
    "dev-requirements.txt",  # Should work
    "requirements",  # No extension
    "requirements.txt.bak",  # Backup file
    "../requirements.txt",  # Relative path
]

for path in test_paths:
    try:
        # Can't create actual file, but analyze logic
        if path.endswith((".txt", ".in")):
            print(f"✓ '{path}' -> requirements.txt parser")
        elif path.endswith(".yml"):
            print(f"✓ '{path}' -> conda.yml parser")
        elif path.endswith("Pipfile"):
            print(f"✓ '{path}' -> Pipfile parser")
        else:
            print(f"✗ '{path}' -> Unknown file type")
    except Exception as e:
        print(f"Error: {e}")

# Bug 7: Deserialization type safety
print("\n7. POTENTIAL BUG: Deserialization type safety")
print("-" * 40)
print("The deserialize method doesn't validate input types")

# Try deserializing with wrong types
test_data = {
    "name": 123,  # Should be string
    "specs": ">=1.0",  # Will be converted
    "line": None,  # Should be string
    "extras": "not_a_list",  # Should be list
}

try:
    dep = Dependency.deserialize(test_data)
    print(f"✗ BUG: Accepted invalid types without validation")
    print(f"  name type: {type(dep.name)} = {dep.name}")
    print(f"  line type: {type(dep.line)} = {dep.line}")
    print(f"  extras type: {type(dep.extras)} = {dep.extras}")
except Exception as e:
    print(f"✓ Properly rejected invalid types: {e}")

print("\n" + "=" * 60)
print("SUMMARY OF POTENTIAL BUGS FOUND:")
print("=" * 60)
print("1. Empty package names create empty keys (may cause issues)")
print("2. Leading/trailing underscores create leading/trailing dashes in keys")
print("3. parse_index_server may return '/' for invalid input")
print("4. Hash regex doesn't match valid base64 hashes with +/= characters")
print("5. File type detection is case-sensitive")
print("6. Deserialization accepts invalid types without validation")
print("\nThese issues should be tested with actual execution to confirm.")