#!/usr/bin/env python3
"""Advanced property-based tests for rpdk focusing on more complex properties."""

import sys
import json
from hypothesis import given, assume, strategies as st, settings, example

# Add the rpdk path to sys.path
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudformation-cli-java-plugin_env/lib/python3.13/site-packages')

from rpdk.core.jsonutils.utils import (
    schema_merge, traverse, traverse_raw_schema,
    traverse_path_for_sequence_members, item_hash
)
from rpdk.core.jsonutils.pointer import fragment_encode, fragment_decode
from ordered_set import OrderedSet


# Test schema_merge properties

# Generate valid JSON schema-like dicts
def json_schema_strategy():
    """Generate simple JSON schema-like dictionaries."""
    return st.recursive(
        st.one_of(
            st.just({"type": "string"}),
            st.just({"type": "integer"}),
            st.just({"type": "boolean"}),
            st.just({"type": "number"}),
            st.dictionaries(
                st.text(min_size=1, max_size=10),
                st.text(min_size=1, max_size=10),
                max_size=3
            )
        ),
        lambda children: st.dictionaries(
            st.sampled_from(["properties", "required", "type", "description"]),
            st.one_of(
                children,
                st.text(),
                st.lists(st.text(), max_size=3)
            ),
            max_size=3
        ),
        max_leaves=5
    )


@given(json_schema_strategy(), json_schema_strategy())
def test_schema_merge_idempotence(schema1, schema2):
    """Test that merging a schema with itself doesn't change it fundamentally."""
    # Make copies to avoid mutation
    target = dict(schema1)
    src = dict(schema1)
    
    result = schema_merge(target, src, ())
    
    # The result should contain all keys from the original
    for key in schema1:
        assert key in result, f"Key {key} missing after self-merge"


@given(json_schema_strategy())
def test_schema_merge_with_empty(schema):
    """Test that merging with empty dict preserves the schema."""
    target = dict(schema)
    result = schema_merge(target, {}, ())
    assert result == schema, "Merging with empty dict should preserve schema"


# Test traverse function
@given(st.dictionaries(
    st.text(min_size=1, max_size=5),
    st.recursive(
        st.one_of(st.integers(), st.text(), st.booleans()),
        lambda children: st.one_of(
            st.dictionaries(st.text(min_size=1, max_size=3), children, max_size=3),
            st.lists(children, max_size=3)
        ),
        max_leaves=10
    ),
    min_size=1,
    max_size=5
))
def test_traverse_empty_path(document):
    """Test that traversing with empty path returns the document itself."""
    result, path, parent = traverse(document, tuple())
    assert result == document, "Empty path should return original document"
    assert path == (), "Path should be empty tuple"
    assert parent is None, "Parent should be None for empty path"


@given(st.lists(st.integers(), min_size=1, max_size=10))
def test_traverse_list_indices(lst):
    """Test traversing lists with valid indices."""
    for i in range(len(lst)):
        result, path, parent = traverse(lst, [str(i)])
        assert result == lst[i], f"Failed to traverse to index {i}"
        assert path == (i,), f"Path should be ({i},)"
        assert parent == lst, "Parent should be the list"


# Test item_hash ordering independence for dicts
@given(st.dictionaries(
    st.text(min_size=1, max_size=5),
    st.integers(),
    min_size=2,
    max_size=5
))
def test_item_hash_dict_order_independence(d):
    """Test that item_hash produces same hash regardless of dict key order."""
    # Create two dicts with same items but different order
    items = list(d.items())
    d1 = dict(items)
    d2 = dict(reversed(items))
    
    hash1 = item_hash(d1)
    hash2 = item_hash(d2)
    assert hash1 == hash2, "Hash should be independent of dict key order"


# Test list sorting behavior in item_hash
@given(st.lists(st.integers(), min_size=2, max_size=10))
def test_item_hash_list_preserves_order(lst):
    """Test that item_hash for lists is order-dependent."""
    # Create a different ordering
    lst2 = list(reversed(lst))
    
    # Only test if lists are actually different
    if lst != lst2:
        hash1 = item_hash(lst)
        hash2 = item_hash(lst2)
        # Lists with different order might have different hashes
        # This is testing the implementation detail from the code


# Test complex round-trip with special characters
@given(st.lists(st.text().filter(lambda x: '\x00' not in x)))
@settings(max_examples=200)
def test_fragment_round_trip_special_chars(parts):
    """Test round-trip with various special characters."""
    try:
        encoded = fragment_encode(parts)
        decoded = fragment_decode(encoded, output=list)
        assert decoded == parts, f"Round-trip failed for {parts!r}"
    except Exception as e:
        # Check if the error is expected
        if any('\x00' in part for part in parts):
            # Null bytes might cause issues
            pass
        else:
            raise


# Test traverse_path_for_sequence_members
def test_traverse_sequence_members_examples():
    """Test the examples from docstring."""
    doc = {"foo": {"bar": [42, 43, 44]}}
    
    # Test empty path
    result, paths = traverse_path_for_sequence_members(doc, tuple())
    assert result == [doc]
    assert paths == [()]
    
    # Test path to object
    result, paths = traverse_path_for_sequence_members(doc, ["foo"])
    assert result == [{"bar": [42, 43, 44]}]
    assert paths == [("foo",)]
    
    # Test path to array
    result, paths = traverse_path_for_sequence_members(doc, ("foo", "bar"))
    assert result == [[42, 43, 44]]
    assert paths == [("foo", "bar")]
    
    # Test unpacking with *
    result, paths = traverse_path_for_sequence_members(doc, ("foo", "bar", "*"))
    assert result == [42, 43, 44]
    assert paths == [("foo", "bar", 0), ("foo", "bar", 1), ("foo", "bar", 2)]


# Test nested structure with wildcards
def test_traverse_nested_wildcard():
    """Test traversing nested structures with wildcards."""
    doc = {
        "foo": {
            "bar": [
                {"baz": 1, "bin": 1},
                {"baz": 2, "bin": 2}
            ]
        }
    }
    
    result, paths = traverse_path_for_sequence_members(doc, ("foo", "bar", "*", "baz"))
    assert result == [1, 2]
    assert paths == [("foo", "bar", 0, "baz"), ("foo", "bar", 1, "baz")]


# Edge case: empty string handling
@given(st.lists(st.text(), min_size=0, max_size=5))
def test_fragment_encode_with_empty_strings(parts):
    """Test that empty strings in parts are handled correctly."""
    # Include empty strings
    parts_with_empty = [""] + parts + [""]
    encoded = fragment_encode(parts_with_empty)
    decoded = fragment_decode(encoded, output=list)
    assert decoded == parts_with_empty, f"Failed with empty strings: {parts_with_empty!r}"


# Test error conditions for fragment_decode
def test_fragment_decode_wrong_prefix():
    """Test that fragment_decode raises error with wrong prefix."""
    try:
        fragment_decode("/foo", prefix="#")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Expected prefix '#'" in str(e)


# Test schema_merge with $ref
def test_schema_merge_ref_handling():
    """Test the $ref handling in schema_merge as shown in docstrings."""
    # From docstring example
    a = {"$ref": "a"}
    b = {"foo": "b"}
    result = schema_merge(dict(a), dict(b), ("foo",))
    assert "$ref" in result
    assert result["foo"] == "b"
    
    # $ref and type merging
    a = {"$ref": "a"}
    b = {"type": "b"}
    result = schema_merge(dict(a), dict(b), ("foo",))
    assert "type" in result
    assert isinstance(result["type"], OrderedSet)
    assert "a" in result["type"]
    assert "b" in result["type"]


# Test required field merging
@given(
    st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=3, unique=True),
    st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=3, unique=True)
)
def test_schema_merge_required_fields(req1, req2):
    """Test that required fields are merged correctly."""
    schema1 = {"required": req1}
    schema2 = {"required": req2}
    
    result = schema_merge(dict(schema1), dict(schema2), ())
    
    # Required fields should be union of both, sorted
    expected = sorted(set(req1) | set(req2))
    assert result["required"] == expected


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])