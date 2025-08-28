#!/usr/bin/env python3
"""Property-based tests for requests.status_codes module."""

import string
from hypothesis import given, strategies as st, assume, settings
import requests.status_codes as sc


# Test 1: Case insensitivity property - upper and lower case should give same result
@given(st.sampled_from([name for name in dir(sc.codes) if not name.startswith('_') and name.lower() != name]))
def test_case_insensitivity_consistency(name):
    """Both upper and lower case versions should return the same status code."""
    lower_name = name.lower()
    
    # Skip if lower_name doesn't exist (e.g., for names with special chars)
    if not hasattr(sc.codes, lower_name):
        return
    
    upper_value = getattr(sc.codes, name)
    lower_value = getattr(sc.codes, lower_name)
    
    assert upper_value == lower_value, f"Case mismatch: {name}={upper_value}, {lower_name}={lower_value}"


# Test 2: Attribute vs dict access consistency
@given(st.sampled_from([name for name in dir(sc.codes) if not name.startswith('_')]))
def test_attribute_dict_access_consistency(name):
    """Attribute access and dict access should return the same value."""
    attr_value = getattr(sc.codes, name)
    dict_value = sc.codes[name]
    
    assert attr_value == dict_value, f"Access mismatch for {name}: attr={attr_value}, dict={dict_value}"


# Test 3: All aliases should resolve to same code
def test_all_aliases_consistent():
    """All aliases for a status code should return the same value."""
    # Manually check all aliases from _codes dict
    _codes = {
        200: ("ok", "okay", "all_ok", "all_okay", "all_good", "\\o/", "✓"),
        404: ("not_found", "-o-"),
        418: ("im_a_teapot", "teapot", "i_am_a_teapot"),
        500: ("internal_server_error", "server_error", "/o\\", "✗"),
    }
    
    for code, aliases in _codes.items():
        values = []
        for alias in aliases:
            if hasattr(sc.codes, alias):
                values.append(getattr(sc.codes, alias))
            if alias in sc.codes.__dict__:
                values.append(sc.codes[alias])
        
        assert all(v == code for v in values), f"Alias inconsistency for code {code}: {values}"


# Test 4: LookupDict inheritance behavior - dict methods through __getitem__
@given(st.sampled_from(['items', 'keys', 'values', 'update', 'clear', 'get', 'pop', 'setdefault']))
def test_lookupdict_dict_methods_access(method_name):
    """Dict methods accessed through __getitem__ should not be None if they exist as methods."""
    # Check if method exists as an attribute
    has_method = hasattr(sc.codes, method_name) and callable(getattr(sc.codes, method_name))
    
    # Access through __getitem__
    item_value = sc.codes[method_name]
    
    # If it exists as a callable method, it shouldn't return None through __getitem__
    if has_method:
        # This reveals the bug: dict methods exist but __getitem__ returns None
        assert item_value is not None or not callable(getattr(sc.codes, method_name)), \
            f"Method {method_name} exists but __getitem__ returns None"


# Test 5: Non-existent keys behavior
@given(st.text(alphabet=string.ascii_letters + string.digits + '_', min_size=1, max_size=20))
def test_nonexistent_key_behavior(key):
    """Non-existent keys should behave consistently."""
    # Skip if key actually exists
    if hasattr(sc.codes, key):
        return
    
    # Through __getitem__, non-existent keys return None (not KeyError)
    dict_value = sc.codes[key]
    assert dict_value is None, f"Non-existent key {key} should return None, got {dict_value}"
    
    # Through get method
    get_value = sc.codes.get(key)
    assert get_value is None, f"get({key}) should return None, got {get_value}"
    
    # Both should be consistent
    assert dict_value == get_value


# Test 6: Test that special dict attributes don't leak through
@given(st.sampled_from(['__dict__', '__class__', '__module__', '__doc__']))
def test_special_attributes_not_accessible_via_getitem(attr_name):
    """Special attributes should not be accessible through __getitem__."""
    # These exist as attributes
    assert hasattr(sc.codes, attr_name)
    
    # But should return None through __getitem__ due to the implementation
    item_value = sc.codes[attr_name]
    assert item_value is None, f"Special attribute {attr_name} leaked through __getitem__: {item_value}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])