#!/usr/bin/env python3
"""Additional tests to find more edge case bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/worker_/14')

from hypothesis import given, strategies as st
from lml_loader import DataLoader

# Test for unhashable items in remove_duplicates
@given(st.lists(st.one_of(
    st.lists(st.integers()),  # Lists are unhashable
    st.dictionaries(st.text(), st.integers())  # Dicts are unhashable
)))
def test_remove_duplicates_unhashable(items):
    """Test remove_duplicates with unhashable items"""
    loader = DataLoader()
    try:
        deduped = loader.remove_duplicates(items)
        # If it works, verify the invariants
        assert len(deduped) <= len(items)
    except TypeError as e:
        # This will fail for unhashable items
        print(f"Bug found: remove_duplicates fails for unhashable items: {e}")
        raise


# Test set_nested_value with existing nested dicts
@given(
    st.text(alphabet=st.characters(blacklist_characters='.', min_codepoint=65), min_size=1),
    st.text(alphabet=st.characters(blacklist_characters='.', min_codepoint=65), min_size=1),
    st.integers()
)
def test_set_nested_value_overwrites_non_dict(key1, key2, value):
    """Test that set_nested_value fails when trying to overwrite non-dict values"""
    loader = DataLoader()
    
    # Create a dict where key1 points to a non-dict value
    data = {key1: "not a dict"}
    
    # Try to set a nested value through key1
    path = f"{key1}.{key2}"
    try:
        updated = loader.set_nested_value(data, path, value)
        # Check if it properly handled the case
        assert isinstance(updated[key1], dict)
        assert updated[key1][key2] == value
    except (TypeError, AttributeError) as e:
        print(f"Bug found: set_nested_value doesn't handle non-dict values in path: {e}")
        raise


# Test edge case with whitespace in split_by_delimiter  
@given(st.text(alphabet=' \t\n', min_size=1))
def test_split_whitespace_only(text):
    """Test split_by_delimiter with whitespace-only text"""
    loader = DataLoader()
    result = loader.split_by_delimiter(text, ',')
    # After stripping, whitespace-only should become empty string
    assert result == ['']  # or should it be []?


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])