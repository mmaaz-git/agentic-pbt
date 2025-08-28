"""Edge case property-based tests for storage3.constants module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/storage3_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, HealthCheck
import pytest
import storage3.constants
from storage3.constants import DEFAULT_SEARCH_OPTIONS, DEFAULT_FILE_OPTIONS, DEFAULT_TIMEOUT


# Test for potential integer overflow/underflow
@given(multiplier=st.integers())
@settings(max_examples=1000)
def test_timeout_extreme_values(multiplier):
    """Test DEFAULT_TIMEOUT with extreme integer values."""
    try:
        # Simulate the operation in client.py
        if multiplier != 0:
            modified = DEFAULT_TIMEOUT * multiplier
            result = int(abs(modified))
            
            # Should handle large numbers
            assert isinstance(result, int)
            assert result >= 0
    except OverflowError:
        # Python 3 handles arbitrarily large integers, but httpx might not
        pass


# Test dictionary pollution attacks
@given(
    malicious_keys=st.dictionaries(
        st.sampled_from(["__proto__", "__init__", "__class__", "constructor", "__dict__"]),
        st.text()
    )
)
def test_search_options_prototype_pollution(malicious_keys):
    """Test that merging with potentially malicious keys doesn't break the system."""
    original_dict = dict(DEFAULT_SEARCH_OPTIONS)
    
    merged = {
        **DEFAULT_SEARCH_OPTIONS,
        **malicious_keys
    }
    
    # Original should be unchanged (no mutation)
    assert DEFAULT_SEARCH_OPTIONS == original_dict
    
    # Merged should contain the keys
    for key in malicious_keys:
        assert key in merged


# Test with None values
@given(
    none_keys=st.dictionaries(
        st.sampled_from(["limit", "offset", "sortBy"]),
        st.none()
    )
)
def test_search_options_none_values(none_keys):
    """Test behavior when DEFAULT_SEARCH_OPTIONS values are overridden with None."""
    merged = {
        **DEFAULT_SEARCH_OPTIONS,
        **none_keys
    }
    
    for key in none_keys:
        assert merged[key] is None
        
    # This could break code expecting specific types
    if "limit" in none_keys:
        # Code expects limit to be an integer
        with pytest.raises((TypeError, AttributeError)):
            # This would fail in real usage
            int(merged["limit"])


# Test empty dictionary override
def test_empty_dict_merge():
    """Test that empty dictionary merge preserves defaults."""
    empty = {}
    merged = {**DEFAULT_SEARCH_OPTIONS, **empty}
    assert merged == DEFAULT_SEARCH_OPTIONS
    
    merged2 = {**DEFAULT_FILE_OPTIONS, **empty}
    assert merged2 == DEFAULT_FILE_OPTIONS


# Test recursive dictionary structures
@given(
    depth=st.integers(min_value=1, max_value=5),
    value=st.text()
)
def test_nested_sortby_override(depth, value):
    """Test deeply nested sortBy structures."""
    nested = {"sortBy": {"column": "name", "order": "asc"}}
    for _ in range(depth):
        nested = {"sortBy": nested}
    
    merged = {
        **DEFAULT_SEARCH_OPTIONS,
        **nested
    }
    
    # The last override wins
    assert "sortBy" in merged
    # The structure might be deeply nested now
    current = merged["sortBy"]
    for _ in range(depth):
        if isinstance(current, dict) and "sortBy" in current:
            current = current["sortBy"]


# Test mutation of shared constant
def test_constant_mutation_safety():
    """Test that modifying returned constants doesn't affect originals."""
    # Get a reference
    options = DEFAULT_SEARCH_OPTIONS
    
    # Try to modify it
    if isinstance(options, dict):
        options["limit"] = 999999
        
        # The original should be modified (they're the same object!)
        # This is actually a bug - constants should be immutable
        assert DEFAULT_SEARCH_OPTIONS["limit"] == 999999
        
        # Restore it
        DEFAULT_SEARCH_OPTIONS["limit"] = 100


# Test type coercion edge cases
@given(
    timeout_value=st.one_of(
        st.just("20"),  # String that can be converted
        st.just(20.5),  # Float
        st.just(True),  # Boolean (converts to 1)
        st.just(False), # Boolean (converts to 0)
        st.just([20]),  # List with single element
        st.just(complex(20, 0))  # Complex number
    )
)
def test_timeout_type_coercion(timeout_value):
    """Test how different types are handled when used as timeout."""
    import storage3.constants
    original = storage3.constants.DEFAULT_TIMEOUT
    
    try:
        storage3.constants.DEFAULT_TIMEOUT = timeout_value
        
        # Try the conversion that happens in client.py
        try:
            result = int(abs(timeout_value))
            # Some values can be converted
            assert isinstance(result, int)
        except (TypeError, ValueError):
            # Some values cannot be converted
            pass
            
    finally:
        storage3.constants.DEFAULT_TIMEOUT = original


# Test dictionary key collision
@given(
    user_options=st.fixed_dictionaries({
        "limit": st.integers(),
        "LIMIT": st.integers(),  # Different case
        "lImIt": st.integers(),  # Mixed case
    })
)
def test_case_sensitive_keys(user_options):
    """Test that dictionary keys are case-sensitive."""
    merged = {
        **DEFAULT_SEARCH_OPTIONS,
        **user_options
    }
    
    # All keys should be present (case-sensitive)
    assert "limit" in merged
    assert "LIMIT" in merged
    assert "lImIt" in merged
    
    # Original limit should be overridden
    assert merged["limit"] == user_options["limit"]


# Test special header characters
@given(
    header_value=st.text(
        alphabet=st.characters(whitelist_characters="\n\r\x00") | st.characters(),
        min_size=1
    ).filter(lambda x: "\n" in x or "\r" in x or "\x00" in x)
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_file_options_header_injection(header_value):
    """Test that special characters in headers could cause issues."""
    
    user_headers = {"x-custom": header_value}
    merged = {
        **DEFAULT_FILE_OPTIONS,
        **user_headers
    }
    
    # Headers with newlines could cause header injection
    assert merged["x-custom"] == header_value
    # This could be a security issue if not properly sanitized