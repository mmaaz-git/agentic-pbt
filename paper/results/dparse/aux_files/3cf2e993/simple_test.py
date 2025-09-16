#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

import re
from dparse.parser import Parser
from dparse.regex import HASH_REGEX

# Test 1: parse_index_server should ensure trailing slash
print("Test 1: parse_index_server trailing slash invariant")
test_cases = [
    ("--index-url http://example.com", "http://example.com/"),
    ("--index-url http://example.com/", "http://example.com/"),
    ("-i https://pypi.org/simple", "https://pypi.org/simple/"),
    ("-i https://pypi.org/simple/", "https://pypi.org/simple/"),
]

for line, expected in test_cases:
    result = Parser.parse_index_server(line)
    print(f"  Input: {line}")
    print(f"  Expected: {expected}")
    print(f"  Got: {result}")
    if result != expected:
        print(f"  ❌ FAILED!")
    else:
        print(f"  ✓ Passed")
    print()

# Test 2: parse_hashes should extract and remove hashes
print("Test 2: parse_hashes extraction")
test_line = "package==1.0.0 --hash=sha256:abc123def456 --hash=md5:789xyz"
cleaned, hashes = Parser.parse_hashes(test_line)
print(f"  Input: {test_line}")
print(f"  Cleaned: {cleaned}")
print(f"  Hashes: {hashes}")
print(f"  Expected cleaned: 'package==1.0.0'")
print(f"  Expected 2 hashes extracted")
if cleaned.strip() != "package==1.0.0":
    print(f"  ❌ FAILED: Cleaned line incorrect")
elif len(hashes) != 2:
    print(f"  ❌ FAILED: Expected 2 hashes, got {len(hashes)}")
else:
    print(f"  ✓ Passed")
print()

# Test 3: Check HASH_REGEX pattern
print("Test 3: HASH_REGEX pattern test")
valid_hashes = [
    "--hash=sha256:abc123",
    "--hash sha256:def456",
    "--hash=md5:xyz789"
]
invalid_hashes = [
    "--hash:sha256:abc",  # Missing = or space
    "hash=sha256:abc",    # Missing --
    "--hash=sha256-abc",  # Wrong separator
]

print("  Valid hashes:")
for h in valid_hashes:
    match = re.search(HASH_REGEX, h)
    if match:
        print(f"    {h} ✓ Matched")
    else:
        print(f"    {h} ❌ FAILED to match")

print("  Invalid hashes (should not match):")
for h in invalid_hashes:
    match = re.search(HASH_REGEX, h)
    if not match:
        print(f"    {h} ✓ Correctly not matched")
    else:
        print(f"    {h} ❌ FAILED: Should not match")

print()

# Test 4: resolve_file should handle comments
print("Test 4: resolve_file comment handling")
from dparse.parser import Parser
result = Parser.resolve_file("/base/path", "-r requirements.txt # this is a comment")
print(f"  Input: '-r requirements.txt # this is a comment'")
print(f"  Result: {result}")
if "#" in result:
    print(f"  ❌ FAILED: Comment not stripped")
else:
    print(f"  ✓ Passed: Comment stripped")

print()

# Test 5: Dependency key normalization
print("Test 5: Dependency key normalization")
from dparse.dependencies import Dependency
from packaging.specifiers import SpecifierSet

test_names = [
    ("My_Package", "my-package"),
    ("UPPERCASE", "uppercase"),
    ("under_score_name", "under-score-name"),
    ("Mixed_Case_Name", "mixed-case-name"),
]

for name, expected_key in test_names:
    dep = Dependency(name=name, specs=SpecifierSet(), line=name)
    print(f"  Name: {name}")
    print(f"  Expected key: {expected_key}")
    print(f"  Got key: {dep.key}")
    if dep.key != expected_key:
        print(f"  ❌ FAILED!")
    else:
        print(f"  ✓ Passed")
    print()