#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

from dparse.dependencies import Dependency
from packaging.specifiers import SpecifierSet

# Test 1: Simple key property test
print("Testing Dependency.key property...")

test_cases = [
    ("Package_Name", "package-name"),
    ("MY_PACKAGE", "my-package"),
    ("test_pkg_123", "test-pkg-123"),
    ("SimplePackage", "simplepackage"),
    ("under_score_pkg", "under-score-pkg")
]

for name, expected_key in test_cases:
    dep = Dependency(name=name, specs=SpecifierSet(), line=name)
    actual_key = dep.key
    if actual_key != expected_key:
        print(f"FAILURE: {name} -> {actual_key} != {expected_key}")
    else:
        print(f"  ✓ {name} -> {actual_key}")

# Test 2: Full name with extras
print("\nTesting Dependency.full_name property...")

test_cases_extras = [
    ("mypackage", [], "mypackage"),
    ("mypackage", ["dev"], "mypackage[dev]"),
    ("mypackage", ["test", "dev"], "mypackage[test,dev]"),
]

for name, extras, expected in test_cases_extras:
    dep = Dependency(name=name, specs=SpecifierSet(), line=name, extras=extras)
    actual = dep.full_name
    if actual != expected:
        print(f"FAILURE: {name} with extras {extras} -> {actual} != {expected}")
    else:
        print(f"  ✓ {name} with extras {extras} -> {actual}")

# Test 3: Serialize/deserialize
print("\nTesting serialize/deserialize...")

import json
from dparse.dependencies import DparseJSONEncoder

original = Dependency(
    name="TestPackage",
    specs=SpecifierSet(">=1.0.0"),
    line="TestPackage>=1.0.0",
    extras=["dev", "test"]
)

serialized = original.serialize()
serialized_json = json.dumps(serialized, cls=DparseJSONEncoder)
deserialized_dict = json.loads(serialized_json)

if isinstance(deserialized_dict['specs'], str):
    deserialized_dict['specs'] = SpecifierSet(deserialized_dict['specs'])

restored = Dependency.deserialize(deserialized_dict)

print(f"  Original name: {original.name}")
print(f"  Restored name: {restored.name}")
print(f"  Original specs: {original.specs}")
print(f"  Restored specs: {restored.specs}")
print(f"  Original extras: {original.extras}")
print(f"  Restored extras: {restored.extras}")

if restored.name == original.name and str(restored.specs) == str(original.specs):
    print("  ✓ Serialize/deserialize successful")
else:
    print("  ✗ Serialize/deserialize failed")

# Test 4: Parser methods
print("\nTesting Parser.parse_index_server...")

from dparse.parser import Parser

test_urls = [
    ("-i http://example.com", "http://example.com/"),
    ("-i http://example.com/", "http://example.com/"),
    ("--index-url=https://pypi.org/simple", "https://pypi.org/simple/"),
    ("--index-url=https://pypi.org/simple/", "https://pypi.org/simple/"),
]

for line, expected in test_urls:
    result = Parser.parse_index_server(line)
    if result == expected:
        print(f"  ✓ {line} -> {result}")
    else:
        print(f"  ✗ {line} -> {result} != {expected}")

# Test 5: Hash parsing
print("\nTesting Parser.parse_hashes...")

test_lines = [
    ("package==1.0 --hash=sha256:abc123", ["--hash=sha256:abc123"]),
    ("package --hash sha512:def456 --hash md5:789", ["--hash sha512:def456", "--hash md5:789"]),
    ("simple-package", [])
]

for line, expected_hashes in test_lines:
    cleaned, hashes = Parser.parse_hashes(line)
    if set(hashes) == set(expected_hashes):
        print(f"  ✓ Found {len(hashes)} hashes in: {line[:50]}...")
    else:
        print(f"  ✗ Expected {expected_hashes}, got {hashes}")

print("\n" + "=" * 60)
print("Manual tests completed. Review output for any failures.")