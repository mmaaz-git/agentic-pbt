"""Property-based tests for storage3.constants module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/storage3_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume
import pytest
from storage3.constants import DEFAULT_SEARCH_OPTIONS, DEFAULT_FILE_OPTIONS, DEFAULT_TIMEOUT
from storage3._sync.client import SyncStorageClient
from storage3._async.client import AsyncStorageClient


# Test 1: DEFAULT_TIMEOUT numeric properties
@given(negative_multiplier=st.integers(min_value=-1000, max_value=-1))
def test_default_timeout_abs_int_invariant(negative_multiplier):
    """Test that DEFAULT_TIMEOUT behaves correctly with abs() and int() as used in client code."""
    # Simulate what happens in client.py line 56
    modified_timeout = DEFAULT_TIMEOUT * negative_multiplier
    result = int(abs(modified_timeout))
    
    # The result should always be positive and an integer
    assert isinstance(result, int)
    assert result >= 0
    
    # The abs should handle the negative case properly
    assert result == abs(modified_timeout)


# Test 2: Dictionary merge safety for DEFAULT_SEARCH_OPTIONS
@given(user_options=st.dictionaries(
    st.text(min_size=1),
    st.one_of(
        st.integers(),
        st.text(),
        st.dictionaries(st.text(), st.text())
    )
))
def test_default_search_options_merge_safety(user_options):
    """Test that DEFAULT_SEARCH_OPTIONS can be safely merged with user options."""
    # Simulate what happens in file_api.py line 398
    try:
        merged = {
            **DEFAULT_SEARCH_OPTIONS,
            **user_options,
        }
        
        # The merge should succeed without errors
        assert isinstance(merged, dict)
        
        # User options should override defaults
        for key in user_options:
            assert merged[key] == user_options[key]
            
        # Default keys should exist unless overridden
        for key in DEFAULT_SEARCH_OPTIONS:
            assert key in merged
            
    except Exception as e:
        # Dictionary merge should not raise exceptions
        pytest.fail(f"Dictionary merge failed: {e}")


# Test 3: DEFAULT_FILE_OPTIONS header validity
@given(user_headers=st.dictionaries(
    st.text(min_size=1, alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters=":")),
    st.text(min_size=1)
))
def test_default_file_options_header_merge(user_headers):
    """Test that DEFAULT_FILE_OPTIONS can be safely merged as HTTP headers."""
    # Simulate what happens in file_api.py line 127
    try:
        base_headers = {"User-Agent": "test"}
        headers = {
            **base_headers,
            **DEFAULT_FILE_OPTIONS,
            **user_headers,
        }
        
        # Headers should be a valid dictionary
        assert isinstance(headers, dict)
        
        # All values should be strings (HTTP header requirement)
        for key, value in headers.items():
            assert isinstance(key, str)
            assert isinstance(value, str) or isinstance(value, (int, float))
            
    except Exception as e:
        pytest.fail(f"Header merge failed: {e}")


# Test 4: DEFAULT_SEARCH_OPTIONS structure preservation
@given(override_limit=st.integers(min_value=1, max_value=1000))
def test_search_options_structure_preservation(override_limit):
    """Test that DEFAULT_SEARCH_OPTIONS maintains expected structure after modification."""
    # Create modified options as done in the codebase
    extra_options = {"limit": override_limit}
    body = {
        **DEFAULT_SEARCH_OPTIONS,
        **extra_options,
        "prefix": "test_path"
    }
    
    # Essential fields should be present
    assert "limit" in body
    assert "offset" in body
    assert "sortBy" in body
    assert "prefix" in body
    
    # Types should be preserved or coerced correctly
    assert isinstance(body["limit"], int)
    assert isinstance(body["offset"], int)
    assert isinstance(body["sortBy"], dict)
    
    # User override should take precedence
    assert body["limit"] == override_limit
    
    # sortBy should have expected structure
    if "sortBy" in DEFAULT_SEARCH_OPTIONS:
        assert "column" in body["sortBy"]
        assert "order" in body["sortBy"]


# Test 5: Mutation test - modifying DEFAULT_TIMEOUT
@given(new_timeout=st.one_of(
    st.floats(min_value=0.1, max_value=1000, allow_nan=False, allow_infinity=False),
    st.integers(min_value=1, max_value=1000),
    st.text(),
    st.none()
))
def test_timeout_mutation_handling(new_timeout):
    """Test how the code handles when DEFAULT_TIMEOUT is mutated to different types."""
    import storage3.constants
    
    # Save original
    original_timeout = storage3.constants.DEFAULT_TIMEOUT
    
    try:
        # Mutate the constant
        storage3.constants.DEFAULT_TIMEOUT = new_timeout
        
        # Test what happens when client code tries to use it
        # This simulates line 56 in client.py
        if new_timeout is not None:
            try:
                result = int(abs(new_timeout))
                # If this succeeds, it should produce a valid timeout
                assert isinstance(result, int)
                assert result >= 0
            except (TypeError, ValueError) as e:
                # Non-numeric values should fail predictably
                assert not isinstance(new_timeout, (int, float))
                
    finally:
        # Restore original
        storage3.constants.DEFAULT_TIMEOUT = original_timeout


# Test 6: Round-trip property for search options
@given(
    limit=st.integers(min_value=1, max_value=10000),
    offset=st.integers(min_value=0, max_value=10000),
    column=st.sampled_from(["name", "created_at", "updated_at", "size"]),
    order=st.sampled_from(["asc", "desc"])
)
def test_search_options_round_trip(limit, offset, column, order):
    """Test that search options maintain their values through merge operations."""
    custom_options = {
        "limit": limit,
        "offset": offset,
        "sortBy": {
            "column": column,
            "order": order
        }
    }
    
    # Merge with defaults (as done in file_api)
    merged = {
        **DEFAULT_SEARCH_OPTIONS,
        **custom_options
    }
    
    # Values should be preserved
    assert merged["limit"] == limit
    assert merged["offset"] == offset
    assert merged["sortBy"]["column"] == column
    assert merged["sortBy"]["order"] == order
    
    # Double merge should be idempotent
    double_merged = {
        **DEFAULT_SEARCH_OPTIONS,
        **merged
    }
    assert double_merged == merged