"""Property-based tests for lml_loader module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/worker_/14')

import math
from hypothesis import assume, given, settings, strategies as st
from hypothesis import example
import lml_loader
from lml_loader import DataLoader, process_config, validate_email, parse_version, compare_versions


# Strategy for JSON-serializable data
json_primitive = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-1e10, max_value=1e10),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text()
)

json_data = st.recursive(
    json_primitive,
    lambda children: st.one_of(
        st.lists(children),
        st.dictionaries(st.text(), children)
    ),
    max_leaves=100
)

# Test 1: JSON round-trip property
@given(json_data)
def test_json_round_trip(data):
    """Test that load_json(save_json(x)) = x"""
    loader = DataLoader()
    json_str = loader.save_json(data)
    loaded = loader.load_json(json_str)
    assert loaded == data


# Test 2: Split/join round-trip with non-empty delimiter
@given(
    st.lists(st.text(alphabet=st.characters(blacklist_characters=',', min_codepoint=32), min_size=1)),
    st.text(alphabet=st.characters(blacklist_characters='\n\r\t ', min_codepoint=32), min_size=1, max_size=3)
)
def test_split_join_round_trip(items, delimiter):
    """Test that split(join(items, delim), delim) = items when delimiter is non-empty"""
    loader = DataLoader()
    
    # Ensure items don't contain the delimiter
    assume(all(delimiter not in item for item in items))
    
    joined = loader.join_with_delimiter(items, delimiter)
    split = loader.split_by_delimiter(joined, delimiter)
    
    # After stripping whitespace, should match
    assert split == items


# Test 3: Chunk/flatten round-trip
@given(
    st.lists(st.integers()),
    st.integers(min_value=1, max_value=100)
)
def test_chunk_flatten_round_trip(items, chunk_size):
    """Test that flatten(chunk(items, n)) = items"""
    loader = DataLoader()
    chunked = loader.chunk_list(items, chunk_size)
    flattened = loader.flatten_list(chunked)
    assert flattened == items


# Test 4: Remove duplicates preserves unique elements and order
@given(st.lists(st.integers()))
def test_remove_duplicates_preserves_elements(items):
    """Test that remove_duplicates preserves all unique elements"""
    loader = DataLoader()
    deduped = loader.remove_duplicates(items)
    
    # Should have same unique elements
    assert set(deduped) == set(items)
    
    # Should not have more items than original
    assert len(deduped) <= len(items)
    
    # Should be idempotent
    assert loader.remove_duplicates(deduped) == deduped


@given(st.lists(st.integers()))
def test_remove_duplicates_preserves_order(items):
    """Test that remove_duplicates preserves the order of first occurrences"""
    loader = DataLoader()
    deduped = loader.remove_duplicates(items)
    
    # Track first occurrence indices in original
    first_occurrence = {}
    for i, item in enumerate(items):
        if item not in first_occurrence:
            first_occurrence[item] = i
    
    # Verify order is preserved
    for i in range(len(deduped) - 1):
        idx1 = first_occurrence[deduped[i]]
        idx2 = first_occurrence[deduped[i + 1]]
        assert idx1 < idx2, f"Order not preserved: {deduped[i]} (at {idx1}) should come before {deduped[i+1]} (at {idx2})"


# Test 5: Set/get nested value consistency
@given(
    st.dictionaries(st.text(min_size=1), st.integers()),
    st.text(alphabet=st.characters(blacklist_characters='.', min_codepoint=65), min_size=1),
    st.integers()
)
def test_nested_value_simple(data, key, value):
    """Test set and get nested value for simple paths"""
    loader = DataLoader()
    
    # Set a value at a simple path
    updated = loader.set_nested_value(data, key, value)
    retrieved = loader.get_nested_value(updated, key)
    
    assert retrieved == value


@given(
    st.text(alphabet=st.characters(blacklist_characters='.', min_codepoint=65), min_size=1),
    st.text(alphabet=st.characters(blacklist_characters='.', min_codepoint=65), min_size=1),
    st.integers(),
    st.integers()
)
def test_nested_value_deep_path(key1, key2, value1, value2):
    """Test set and get nested value for deeper paths"""
    loader = DataLoader()
    
    # Start with empty dict
    data = {}
    
    # Set nested values
    path = f"{key1}.{key2}"
    updated = loader.set_nested_value(data, path, value1)
    retrieved = loader.get_nested_value(updated, path)
    assert retrieved == value1
    
    # Verify structure
    assert key1 in updated
    assert isinstance(updated[key1], dict)
    assert key2 in updated[key1]


# Test 6: Version comparison properties
@given(
    st.lists(st.integers(min_value=0, max_value=999), min_size=1, max_size=4),
    st.lists(st.integers(min_value=0, max_value=999), min_size=1, max_size=4),
    st.lists(st.integers(min_value=0, max_value=999), min_size=1, max_size=4)
)
def test_version_comparison_transitivity(v1_parts, v2_parts, v3_parts):
    """Test transitivity of version comparison"""
    v1 = '.'.join(map(str, v1_parts))
    v2 = '.'.join(map(str, v2_parts))
    v3 = '.'.join(map(str, v3_parts))
    
    cmp12 = compare_versions(v1, v2)
    cmp23 = compare_versions(v2, v3)
    cmp13 = compare_versions(v1, v3)
    
    # If v1 < v2 and v2 < v3, then v1 < v3
    if cmp12 == -1 and cmp23 == -1:
        assert cmp13 == -1
    
    # If v1 > v2 and v2 > v3, then v1 > v3
    if cmp12 == 1 and cmp23 == 1:
        assert cmp13 == 1
    
    # If v1 = v2 and v2 = v3, then v1 = v3
    if cmp12 == 0 and cmp23 == 0:
        assert cmp13 == 0


@given(st.lists(st.integers(min_value=0, max_value=999), min_size=1, max_size=4))
def test_version_comparison_reflexivity(v_parts):
    """Test that compare_versions(v, v) = 0"""
    v = '.'.join(map(str, v_parts))
    assert compare_versions(v, v) == 0


# Test 7: Filter by key invariants
@given(
    st.lists(st.dictionaries(st.text(), st.integers())),
    st.text(),
    st.integers()
)
def test_filter_by_key_size_invariant(data, key, value):
    """Test that filtering reduces or maintains list size"""
    loader = DataLoader()
    filtered = loader.filter_by_key(data, key, value)
    
    assert len(filtered) <= len(data)
    
    # All filtered items should match the criterion
    for item in filtered:
        assert item.get(key) == value
    
    # All filtered items should be from original data
    for item in filtered:
        assert item in data


# Test 8: Merge dicts property
@given(
    st.dictionaries(st.text(), st.integers()),
    st.dictionaries(st.text(), st.integers())
)
def test_merge_dicts_overwrite(d1, d2):
    """Test that merge_dicts properly overwrites d1 with d2 values"""
    loader = DataLoader()
    merged = loader.merge_dicts(d1, d2)
    
    # All keys from both dicts should be present
    assert set(merged.keys()) == set(d1.keys()) | set(d2.keys())
    
    # Values from d2 should overwrite d1
    for key in d2:
        assert merged[key] == d2[key]
    
    # Values only in d1 should be preserved
    for key in d1:
        if key not in d2:
            assert merged[key] == d1[key]


# Test 9: Process config with defaults
@given(st.dictionaries(st.text(), st.one_of(st.integers(), st.booleans(), st.text())))
def test_process_config_defaults(config):
    """Test that process_config properly applies defaults"""
    result = process_config(config)
    
    # Default values should be present if not in config
    if 'timeout' not in config:
        assert result['timeout'] == 30
    if 'retries' not in config:
        assert result['retries'] == 3
    if 'debug' not in config:
        assert result['debug'] == False
    
    # Config values should override defaults
    for key, value in config.items():
        assert result[key] == value


# Test 10: Encode/decode bytes round-trip
@given(st.text())
def test_encode_decode_round_trip(text):
    """Test that encode_decode_bytes is identity function"""
    loader = DataLoader()
    result = loader.encode_decode_bytes(text)
    assert result == text


# Test 11: Empty delimiter edge case
@given(st.text())
def test_split_empty_delimiter(text):
    """Test split_by_delimiter with empty delimiter returns [text]"""
    loader = DataLoader()
    result = loader.split_by_delimiter(text, '')
    assert result == [text]


# Test 12: Chunk list properties
@given(
    st.lists(st.integers(), min_size=1),
    st.integers(min_value=1, max_value=100)
)
def test_chunk_list_sizes(items, chunk_size):
    """Test that chunk sizes are correct"""
    loader = DataLoader()
    chunks = loader.chunk_list(items, chunk_size)
    
    if not items:
        assert chunks == []
    else:
        # All chunks except possibly the last should be of chunk_size
        for i, chunk in enumerate(chunks[:-1]):
            assert len(chunk) == chunk_size, f"Chunk {i} has size {len(chunk)}, expected {chunk_size}"
        
        # Last chunk should be <= chunk_size
        if chunks:
            assert len(chunks[-1]) <= chunk_size
            assert len(chunks[-1]) > 0
        
        # Total elements should be preserved
        total = sum(len(chunk) for chunk in chunks)
        assert total == len(items)