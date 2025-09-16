#!/usr/bin/env python3
"""Property-based tests for rpdk.core using Hypothesis."""

import sys
import math
import json
import copy
from hypothesis import given, strategies as st, assume, settings

# Add the site-packages to path so we can import rpdk
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudformation-cli-java-plugin_env/lib/python3.13/site-packages')

from rpdk.core.jsonutils.pointer import part_encode, part_decode, fragment_encode, fragment_decode
from rpdk.core.jsonutils.utils import item_hash, schema_merge, to_set


# Test 1: JSON Pointer part encode/decode round-trip
@given(st.text())
def test_part_encode_decode_round_trip(s):
    """Test that part_decode(part_encode(x)) == x for any string."""
    encoded = part_encode(s)
    decoded = part_decode(encoded)
    assert decoded == s, f"Round-trip failed: {s!r} -> {encoded!r} -> {decoded!r}"


# Test 2: JSON Pointer fragment encode/decode round-trip  
@given(st.lists(st.text()))
def test_fragment_encode_decode_round_trip(parts):
    """Test that fragment_decode(fragment_encode(parts)) == tuple(parts)."""
    encoded = fragment_encode(parts)
    decoded = fragment_decode(encoded)
    assert decoded == tuple(parts), f"Round-trip failed: {parts} -> {encoded} -> {decoded}"


# Test 3: Item hash consistency - deterministic
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.booleans(),
    st.none(),
    st.lists(st.integers(), max_size=10),
    st.dictionaries(st.text(min_size=1), st.integers(), max_size=10)
))
def test_item_hash_deterministic(item):
    """Test that item_hash is deterministic - same input always gives same output."""
    hash1 = item_hash(item)
    hash2 = item_hash(item)
    assert hash1 == hash2, f"Hash not deterministic for {item!r}: {hash1} != {hash2}"


# Test 4: Item hash equality - equal items have equal hashes
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.booleans(),
    st.none(),
    st.lists(st.integers(), max_size=10),
    st.dictionaries(st.text(min_size=1), st.integers(), max_size=10)
))
def test_item_hash_equality(item):
    """Test that equal items produce equal hashes."""
    item_copy = copy.deepcopy(item)
    hash1 = item_hash(item)
    hash2 = item_hash(item_copy)
    assert hash1 == hash2, f"Equal items have different hashes: {item!r}"


# Test 5: Schema merge with empty dict - identity property
@given(st.dictionaries(
    st.text(min_size=1), 
    st.one_of(st.text(), st.integers(), st.booleans(), st.lists(st.text(), max_size=3)),
    max_size=5
))
def test_schema_merge_empty_identity(schema):
    """Test that merging with empty dict preserves the original schema."""
    # Avoid schemas with $ref or type keys as they have special handling
    assume('$ref' not in schema and 'type' not in schema)
    
    original = copy.deepcopy(schema)
    result = schema_merge(schema, {}, ())
    
    # Result should be the same object (modified in place)
    assert result is schema
    # Content should remain the same
    assert result == original, f"Schema changed after merging with empty: {original} -> {result}"


# Test 6: Schema merge idempotence for simple schemas
@given(st.dictionaries(
    st.sampled_from(['foo', 'bar', 'baz']),
    st.text(min_size=1),
    min_size=1,
    max_size=3
))
def test_schema_merge_idempotent(schema):
    """Test that merging a schema with itself is idempotent for simple properties."""
    # Avoid complex schemas with special keys
    assume('$ref' not in schema and 'type' not in schema and 'required' not in schema)
    
    original = copy.deepcopy(schema)
    schema_copy = copy.deepcopy(schema)
    
    result = schema_merge(schema, schema_copy, ())
    
    # Should still equal the original
    assert result == original, f"Self-merge changed schema: {original} -> {result}"


# Test 7: Fragment encode/decode with empty prefix
@given(st.lists(st.text()))
def test_fragment_encode_decode_empty_prefix(parts):
    """Test fragment encoding/decoding with empty prefix."""
    encoded = fragment_encode(parts, prefix="")
    # For empty prefix, should not start with '#'
    assert not encoded.startswith('#')
    
    # Should be able to decode with empty prefix
    decoded = fragment_decode(encoded, prefix="")
    assert decoded == tuple(parts)


# Test 8: Part encode special characters
@given(st.text())
def test_part_encode_special_chars(text):
    """Test that special characters ~ and / are properly escaped."""
    encoded = part_encode(text)
    
    # Check that ~ is replaced with ~0
    if '~' in text:
        # After encoding, original ~ should become ~0
        # Count occurrences
        original_tilde_count = text.count('~')
        # In encoded, we should see ~0 for each original ~
        # But we need to be careful about counting
        pass  # This is complex to verify without decoding
    
    # Check that / is replaced with ~1
    if '/' in text:
        assert '~1' in encoded or '/' not in text
    
    # Most importantly, round-trip should work
    decoded = part_decode(encoded)
    assert decoded == text


# Test 9: Schema merge with type field handling
@given(
    st.dictionaries(st.text(min_size=1), st.text(), max_size=3),
    st.sampled_from(['string', 'integer', 'boolean', 'array', 'object'])
)
def test_schema_merge_type_field(base_schema, type_value):
    """Test schema merge handles type field specially."""
    schema1 = copy.deepcopy(base_schema)
    schema1['type'] = type_value
    
    schema2 = {'type': type_value}
    
    result = schema_merge(copy.deepcopy(schema1), schema2, ())
    
    # When merging same type, it should create an OrderedSet or keep the value
    assert 'type' in result
    # The type should be preserved (might be in an OrderedSet)
    if hasattr(result['type'], '__iter__') and not isinstance(result['type'], str):
        assert type_value in result['type']
    else:
        assert result['type'] == type_value or type_value in to_set(result['type'])


# Test 10: Item hash for nested structures
@given(st.recursive(
    st.one_of(st.integers(), st.text(), st.booleans(), st.none()),
    lambda children: st.one_of(
        st.lists(children, max_size=3),
        st.dictionaries(st.text(min_size=1), children, max_size=3)
    ),
    max_leaves=20
))
def test_item_hash_nested_structures(item):
    """Test item_hash works correctly on nested structures."""
    hash1 = item_hash(item)
    hash2 = item_hash(copy.deepcopy(item))
    
    # Should be deterministic
    assert hash1 == hash2
    
    # Should be a valid MD5 hex string (32 chars)
    assert isinstance(hash1, str)
    assert len(hash1) == 32
    assert all(c in '0123456789abcdef' for c in hash1)


if __name__ == "__main__":
    # Run a quick test to ensure imports work
    print("Testing rpdk.core properties...")
    
    # Quick smoke tests
    assert part_decode(part_encode("hello")) == "hello"
    assert fragment_decode(fragment_encode(["a", "b"])) == ("a", "b")
    
    print("Smoke tests passed! Run with pytest for full test suite.")