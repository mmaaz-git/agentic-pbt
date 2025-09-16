#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume, example
from dparse.dependencies import Dependency, DependencyFile
from dparse.parser import Parser
from dparse import filetypes, parse
from packaging.specifiers import SpecifierSet
import json
import traceback
import re

# First, let me verify the package works with basic examples
print("Verifying basic functionality...")
print("=" * 60)

# Test 1: Basic parsing of requirements.txt
req_content = """
# This is a comment
Django==3.2.0
requests>=2.25.0
numpy  # inline comment
pandas[excel]>=1.2.0
-i https://pypi.org/simple/
"""

try:
    result = parse(req_content, file_type=filetypes.requirements_txt)
    print(f"✓ Parsed requirements.txt: {len(result.dependencies)} dependencies")
    for dep in result.dependencies:
        print(f"  - {dep.name}: {dep.specs}")
except Exception as e:
    print(f"✗ Failed to parse requirements.txt: {e}")
    traceback.print_exc()

# Test 2: Basic Pipfile parsing  
pipfile_content = """
[packages]
django = "==3.2.0"
requests = "*"
numpy = ">=1.20"

[dev-packages]
pytest = ">=6.0"
"""

try:
    result = parse(pipfile_content, file_type=filetypes.pipfile)
    print(f"\n✓ Parsed Pipfile: {len(result.dependencies)} dependencies")
    for dep in result.dependencies:
        print(f"  - {dep.name}: {dep.specs} (sections: {dep.sections})")
except Exception as e:
    print(f"\n✗ Failed to parse Pipfile: {e}")
    traceback.print_exc()

# Now property-based testing with Hypothesis
print("\n\nProperty-based bug hunting...")
print("=" * 60)

# Strategy for generating package names that might break parsing
tricky_names = st.one_of(
    st.just(""),  # Empty name
    st.text(alphabet=st.characters(whitelist_categories=("Cc", "Cf", "Cs")), min_size=1, max_size=10),  # Control chars
    st.text(alphabet="@#$%^&*()[]{}|\\/<>?;:'\"", min_size=1, max_size=20),  # Special chars
    st.text(min_size=500, max_size=1000),  # Very long names
    st.sampled_from([".", "..", "...", "-", "--", "---"]),  # Edge case names
)

# Bug Hunt: Dependency creation with edge case names
print("\n1. Testing Dependency with edge case names...")
@given(tricky_names)
@settings(max_examples=50, deadline=None)
def test_dependency_edge_cases(name):
    """Test if Dependency handles edge case names without crashing"""
    try:
        dep = Dependency(
            name=name,
            specs=SpecifierSet(),
            line=name
        )
        # Check that key transformation is consistent
        key = dep.key
        assert isinstance(key, str), f"Key is not a string: {type(key)}"
        
        # Key should be lowercase
        if name:
            assert key == name.lower().replace("_", "-"), f"Key transformation incorrect for {repr(name)}"
            
        # Test serialization doesn't crash
        serialized = dep.serialize()
        json.dumps(serialized, cls=DparseJSONEncoder)
        
    except Exception as e:
        print(f"  ✗ FOUND BUG: Name {repr(name)} caused {type(e).__name__}: {e}")
        return False
    return True

try:
    test_dependency_edge_cases()
    print("  ✓ No crashes with edge case names")
except Exception as e:
    print(f"  ✗ Property test failed: {e}")

# Bug Hunt: Parser.parse_index_server with malformed input
print("\n2. Testing parse_index_server with edge cases...")
@given(st.text(min_size=0, max_size=100))
@settings(max_examples=50, deadline=None)
def test_parse_index_server_robustness(text):
    """Test if parse_index_server handles arbitrary input safely"""
    lines = [
        f"-i {text}",
        f"--index-url {text}",
        f"--index-url={text}",
        text  # Raw text
    ]
    
    for line in lines:
        try:
            result = Parser.parse_index_server(line)
            # If result is not None, it should end with /
            if result is not None:
                assert isinstance(result, str), f"Result is not string: {type(result)}"
                if not result.endswith("/"):
                    print(f"  ✗ FOUND BUG: Result doesn't end with /: {repr(result)} from {repr(line)}")
                    return False
        except Exception as e:
            print(f"  ✗ FOUND BUG: parse_index_server crashed on {repr(line)}: {e}")
            return False
    return True

try:
    test_parse_index_server_robustness()
    print("  ✓ parse_index_server handles edge cases")
except Exception as e:
    print(f"  ✗ Property test failed: {e}")

# Bug Hunt: Hash parsing with malformed patterns
print("\n3. Testing hash parsing with edge cases...")
@given(st.text(min_size=0, max_size=200))
@settings(max_examples=50, deadline=None)
def test_hash_parsing_robustness(text):
    """Test if parse_hashes handles arbitrary input safely"""
    try:
        cleaned, hashes = Parser.parse_hashes(text)
        
        # Cleaned should not contain extracted hashes
        for hash_val in hashes:
            if hash_val in cleaned:
                print(f"  ✗ FOUND BUG: Hash {repr(hash_val)} still in cleaned: {repr(cleaned)}")
                return False
                
        # All hashes should match the regex pattern
        from dparse.regex import HASH_REGEX
        for hash_val in hashes:
            if not re.match(HASH_REGEX, hash_val):
                print(f"  ✗ FOUND BUG: Invalid hash extracted: {repr(hash_val)}")
                return False
                
    except Exception as e:
        print(f"  ✗ FOUND BUG: parse_hashes crashed on {repr(text[:50])}: {e}")
        return False
    return True

try:
    test_hash_parsing_robustness()
    print("  ✓ Hash parsing handles edge cases")
except Exception as e:
    print(f"  ✗ Property test failed: {e}")

# Bug Hunt: Requirements parsing with malformed content
print("\n4. Testing requirements.txt parsing with edge cases...")
@given(st.text(min_size=0, max_size=500))
@settings(max_examples=30, deadline=None)
def test_requirements_parsing_robustness(content):
    """Test if requirements parsing handles arbitrary content safely"""
    try:
        result = parse(content, file_type=filetypes.requirements_txt)
        
        # Should always return a DependencyFile
        assert isinstance(result, DependencyFile), f"Wrong return type: {type(result)}"
        
        # Dependencies should be a list
        assert isinstance(result.dependencies, list), f"Dependencies not a list: {type(result.dependencies)}"
        
        # Each dependency should be valid
        for dep in result.dependencies:
            assert isinstance(dep.name, str), f"Dependency name not string: {type(dep.name)}"
            assert dep.name, "Empty dependency name"
            
    except Exception as e:
        # Some exceptions might be expected for truly malformed content
        if "MalformedDependencyFileError" not in str(type(e)):
            print(f"  ✗ FOUND BUG: Unexpected error: {type(e).__name__}: {e}")
            print(f"     Content: {repr(content[:100])}")
            return False
    return True

try:
    test_requirements_parsing_robustness()
    print("  ✓ Requirements parsing handles edge cases")
except Exception as e:
    print(f"  ✗ Property test failed: {e}")

# Bug Hunt: JSON encoding edge cases
print("\n5. Testing JSON encoding with edge cases...")
@given(
    st.dictionaries(
        st.text(min_size=0, max_size=50),
        st.one_of(
            st.none(),
            st.text(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.lists(st.text(), max_size=5),
            st.sets(st.text(), max_size=5)
        ),
        max_size=10
    )
)
@settings(max_examples=30, deadline=None)
def test_json_encoder_robustness(meta_dict):
    """Test if DparseJSONEncoder handles various data types"""
    try:
        dep = Dependency(
            name="test",
            specs=SpecifierSet(),
            line="test",
            meta=meta_dict
        )
        
        serialized = dep.serialize()
        json_str = json.dumps(serialized, cls=DparseJSONEncoder)
        
        # Should be valid JSON
        deserialized = json.loads(json_str)
        assert isinstance(deserialized, dict), f"Deserialized not a dict: {type(deserialized)}"
        
    except Exception as e:
        print(f"  ✗ FOUND BUG: JSON encoding failed: {e}")
        print(f"     Meta dict: {meta_dict}")
        return False
    return True

try:
    test_json_encoder_robustness()
    print("  ✓ JSON encoder handles edge cases")
except Exception as e:
    print(f"  ✗ Property test failed: {e}")

print("\n" + "=" * 60)
print("Property-based bug hunting complete.")