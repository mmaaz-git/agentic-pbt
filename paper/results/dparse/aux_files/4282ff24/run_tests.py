#!/usr/bin/env /root/hypothesis-llm/envs/dparse_env/bin/python3

import sys
import traceback

sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, Verbosity
from hypothesis.strategies import text, lists, sets, dictionaries, one_of, none, sampled_from, integers, booleans
import json
import re
from packaging.specifiers import SpecifierSet
from dparse.dependencies import Dependency, DependencyFile, DparseJSONEncoder
from dparse.parser import Parser
from dparse import filetypes


# Strategy for generating valid package names
package_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"),
    min_size=1,
    max_size=50
).filter(lambda x: x and not x[0].isdigit() and not x.startswith("-"))

# Strategy for generating valid specifier sets
specifier_strategy = st.one_of(
    st.just(SpecifierSet()),
    st.sampled_from([
        SpecifierSet(">=1.0.0"),
        SpecifierSet("==2.3.4"),
        SpecifierSet("<3.0"),
        SpecifierSet("~=1.2.0"),
        SpecifierSet("!=1.5"),
        SpecifierSet(">=1.0,<2.0")
    ])
)

# Strategy for generating extras
extras_strategy = st.lists(
    st.text(alphabet=st.characters(whitelist_categories=("Ll",), whitelist_characters="_-"), min_size=1, max_size=20),
    min_size=0,
    max_size=5
)

print("Running property-based tests for dparse...")
print("=" * 60)

test_results = []

# Test 1: Dependency.key property
print("\n1. Testing Dependency.key property...")
@given(package_name_strategy)
@settings(max_examples=100, verbosity=Verbosity.verbose)
def test_dependency_key_property(name):
    dep = Dependency(
        name=name,
        specs=SpecifierSet(),
        line=name
    )
    expected_key = name.lower().replace("_", "-")
    assert dep.key == expected_key, f"Failed: {name} -> {dep.key} != {expected_key}"

try:
    test_dependency_key_property()
    print("✓ Dependency.key property test passed")
    test_results.append(("Dependency.key property", "PASS"))
except Exception as e:
    print(f"✗ Dependency.key property test failed: {e}")
    test_results.append(("Dependency.key property", f"FAIL: {e}"))
    traceback.print_exc()

# Test 2: Dependency.full_name property
print("\n2. Testing Dependency.full_name property...")
@given(package_name_strategy, extras_strategy)
@settings(max_examples=100, verbosity=Verbosity.verbose)
def test_dependency_full_name_property(name, extras):
    dep = Dependency(
        name=name,
        specs=SpecifierSet(),
        line=name,
        extras=extras
    )
    
    if extras:
        expected = f"{name}[{','.join(extras)}]"
    else:
        expected = name
    
    assert dep.full_name == expected, f"Failed: {name}, {extras} -> {dep.full_name} != {expected}"

try:
    test_dependency_full_name_property()
    print("✓ Dependency.full_name property test passed")
    test_results.append(("Dependency.full_name property", "PASS"))
except Exception as e:
    print(f"✗ Dependency.full_name property test failed: {e}")
    test_results.append(("Dependency.full_name property", f"FAIL: {e}"))
    traceback.print_exc()

# Test 3: Dependency serialize/deserialize roundtrip
print("\n3. Testing Dependency serialize/deserialize roundtrip...")
@given(
    package_name_strategy,
    specifier_strategy,
    st.text(min_size=0, max_size=50),  # line
    st.text(min_size=0, max_size=20),  # source  
    extras_strategy,
    st.lists(st.text(min_size=0, max_size=50), min_size=0, max_size=3),  # hashes
)
@settings(max_examples=50, verbosity=Verbosity.verbose)
def test_dependency_serialize_deserialize_simple(name, specs, line, source, extras, hashes):
    original = Dependency(
        name=name,
        specs=specs,
        line=line,
        source=source,
        extras=extras,
        hashes=tuple(hashes)
    )
    
    serialized = original.serialize()
    serialized_json = json.dumps(serialized, cls=DparseJSONEncoder)
    deserialized_dict = json.loads(serialized_json)
    
    if isinstance(deserialized_dict['specs'], str):
        deserialized_dict['specs'] = SpecifierSet(deserialized_dict['specs'])
    
    restored = Dependency.deserialize(deserialized_dict)
    
    assert restored.name == original.name
    assert restored.key == original.key
    assert str(restored.specs) == str(original.specs)
    assert restored.line == original.line
    assert restored.source == original.source
    assert restored.extras == original.extras

try:
    test_dependency_serialize_deserialize_simple()
    print("✓ Dependency serialize/deserialize roundtrip test passed")
    test_results.append(("Dependency serialize/deserialize", "PASS"))
except Exception as e:
    print(f"✗ Dependency serialize/deserialize test failed: {e}")
    test_results.append(("Dependency serialize/deserialize", f"FAIL: {e}"))
    traceback.print_exc()

# Test 4: parse_index_server normalization
print("\n4. Testing parse_index_server URL normalization...")
@given(st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=".-/:"), 
              min_size=1, max_size=50))
@settings(max_examples=50, verbosity=Verbosity.verbose)
def test_parse_index_server_normalization(url):
    # Skip URLs with spaces
    if " " in url.strip() or not url.strip():
        return
    
    url = url.strip()
    line = f"-i {url}"
    result = Parser.parse_index_server(line)
    
    if result is not None:
        assert result.endswith("/"), f"Result doesn't end with /: {result}"
        if url.endswith("/"):
            assert result == url
        else:
            assert result == url + "/"

try:
    test_parse_index_server_normalization()
    print("✓ parse_index_server normalization test passed")
    test_results.append(("parse_index_server normalization", "PASS"))
except Exception as e:
    print(f"✗ parse_index_server normalization test failed: {e}")
    test_results.append(("parse_index_server normalization", f"FAIL: {e}"))
    traceback.print_exc()

# Test 5: Hash regex pattern
print("\n5. Testing hash regex pattern...")
@given(st.text(min_size=0, max_size=50))
@settings(max_examples=50, verbosity=Verbosity.verbose)
def test_hash_regex_basic(text):
    from dparse.regex import HASH_REGEX
    
    # Test that valid patterns are found
    test_pattern = "--hash=sha256:abc123"
    test_text = text + test_pattern
    matches = re.findall(HASH_REGEX, test_text)
    assert test_pattern in matches, f"Valid pattern not found in: {test_text}"

try:
    test_hash_regex_basic()
    print("✓ Hash regex pattern test passed")
    test_results.append(("Hash regex pattern", "PASS"))
except Exception as e:
    print(f"✗ Hash regex pattern test failed: {e}")
    test_results.append(("Hash regex pattern", f"FAIL: {e}"))
    traceback.print_exc()

# Summary
print("\n" + "=" * 60)
print("TEST SUMMARY:")
print("=" * 60)
for test_name, result in test_results:
    status = "✓" if result == "PASS" else "✗"
    print(f"{status} {test_name}: {result}")

passed = sum(1 for _, r in test_results if r == "PASS")
total = len(test_results)
print(f"\nTotal: {passed}/{total} tests passed")

if passed == total:
    print("\n✅ All property-based tests passed!")
else:
    print("\n⚠️ Some tests failed. Review the output above for details.")