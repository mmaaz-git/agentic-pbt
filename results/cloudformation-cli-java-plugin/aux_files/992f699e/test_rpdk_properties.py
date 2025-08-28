#!/usr/bin/env python3
"""Property-based tests for rpdk.core.jsonutils using Hypothesis."""

import sys
import math
from hypothesis import given, assume, strategies as st, settings
import json

# Add the rpdk path to sys.path
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudformation-cli-java-plugin_env/lib/python3.13/site-packages')

from rpdk.core.jsonutils.pointer import (
    part_encode, part_decode,
    fragment_encode, fragment_decode
)
from rpdk.core.jsonutils.utils import item_hash


# Test 1: Round-trip property for part_encode/part_decode
@given(st.text())
def test_part_encode_decode_round_trip(s):
    """Test that part_decode(part_encode(s)) == s for any string."""
    encoded = part_encode(s)
    decoded = part_decode(encoded)
    assert decoded == s, f"Round-trip failed: {s!r} -> {encoded!r} -> {decoded!r}"


# Test 2: Round-trip property for fragment_encode/fragment_decode
@given(st.lists(st.text()))
def test_fragment_encode_decode_round_trip(parts):
    """Test that fragment_decode(fragment_encode(parts)) == parts."""
    encoded = fragment_encode(parts)
    decoded = fragment_decode(encoded, output=list)
    assert decoded == parts, f"Round-trip failed: {parts!r} -> {encoded!r} -> {decoded!r}"


# Test 3: fragment_encode with empty list should produce just the prefix
@given(st.sampled_from(["#", "", "foo"]))
def test_fragment_encode_empty_list(prefix):
    """Test that encoding an empty list produces just the prefix."""
    result = fragment_encode([], prefix=prefix)
    assert result == prefix, f"Expected {prefix!r}, got {result!r}"


# Test 4: fragment_decode should handle the prefix correctly
@given(st.lists(st.text()), st.text(min_size=1))
def test_fragment_decode_with_custom_prefix(parts, prefix):
    """Test that fragment_decode correctly handles custom prefixes."""
    # Avoid '/' in prefix as it would confuse the decoder
    assume('/' not in prefix)
    encoded = fragment_encode(parts, prefix=prefix)
    decoded = fragment_decode(encoded, prefix=prefix, output=list)
    assert decoded == parts, f"Round-trip with prefix {prefix!r} failed"


# Test 5: Test item_hash determinism
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.booleans(),
    st.none()
))
def test_item_hash_determinism_scalars(item):
    """Test that item_hash is deterministic for scalar values."""
    hash1 = item_hash(item)
    hash2 = item_hash(item)
    assert hash1 == hash2, f"Hash not deterministic for {item!r}: {hash1} != {hash2}"


# Test 6: Test item_hash determinism for simple dicts
@given(st.dictionaries(
    st.text(min_size=1),
    st.one_of(st.integers(), st.text(), st.booleans(), st.none()),
    max_size=5
))
def test_item_hash_determinism_dicts(item):
    """Test that item_hash is deterministic for dictionaries."""
    hash1 = item_hash(item)
    hash2 = item_hash(item)
    assert hash1 == hash2, f"Hash not deterministic for dict: {hash1} != {hash2}"


# Test 7: Test item_hash determinism for lists
@given(st.lists(
    st.one_of(st.integers(), st.text(), st.booleans()),
    max_size=10
))
def test_item_hash_determinism_lists(item):
    """Test that item_hash is deterministic for lists."""
    hash1 = item_hash(item)
    hash2 = item_hash(item)
    assert hash1 == hash2, f"Hash not deterministic for list: {hash1} != {hash2}"


# Test 8: part_encode should handle integers (as shown in docstring)
@given(st.integers())
def test_part_encode_integers(n):
    """Test that part_encode handles integers correctly."""
    encoded = part_encode(n)
    decoded = part_decode(encoded)
    assert decoded == str(n), f"Integer encoding failed: {n} -> {encoded} -> {decoded}"


# Test 9: Special characters in part encoding
def test_part_encode_special_chars():
    """Test the specific examples from the docstring."""
    # From the docstring examples
    assert part_encode("~foo") == "~0foo"
    assert part_encode("foo~") == "foo~0"
    assert part_encode("/foo") == "~1foo"
    assert part_encode("foo/") == "foo~1"
    assert part_encode("f/o~o") == "f~1o~0o"
    assert part_encode("~0") == "~00"
    assert part_encode("~1") == "~01"
    assert part_encode(0) == "0"
    
    # And their decoding
    assert part_decode("~0foo") == "~foo"
    assert part_decode("foo~0") == "foo~"
    assert part_decode("~1foo") == "/foo"
    assert part_decode("foo~1") == "foo/"
    assert part_decode("f~1o~0o") == "f/o~o"
    assert part_decode("~00") == "~0"
    assert part_decode("~01") == "~1"
    assert part_decode("0") == "0"


# Test 10: fragment_encode/decode specific examples from docstring
def test_fragment_encode_decode_examples():
    """Test specific examples from the docstring."""
    assert fragment_encode([]) == "#"
    assert fragment_encode([], prefix="") == ""
    assert fragment_encode(["foo", "bar"]) == "#/foo/bar"
    assert fragment_encode([0, " ", "~"]) == "#/0/%20/~0"
    
    assert fragment_decode("#") == ()
    assert fragment_decode("#/foo/bar") == ("foo", "bar")
    assert fragment_decode("#/0/%20/~0") == ("0", " ", "~")


# Test 11: Complex nested structure for item_hash
@given(st.recursive(
    st.one_of(
        st.integers(),
        st.text(max_size=10),
        st.booleans(),
        st.none()
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=3),
        st.dictionaries(st.text(min_size=1, max_size=5), children, max_size=3)
    ),
    max_leaves=20
))
def test_item_hash_complex_structures(item):
    """Test that item_hash is deterministic for complex nested structures."""
    # Skip if the structure is too large to JSON encode
    try:
        json.dumps(item)
    except (RecursionError, OverflowError):
        assume(False)
    
    hash1 = item_hash(item)
    hash2 = item_hash(item)
    assert hash1 == hash2, f"Hash not deterministic for complex structure"


if __name__ == "__main__":
    # Run the tests
    import pytest
    pytest.main([__file__, "-v"])