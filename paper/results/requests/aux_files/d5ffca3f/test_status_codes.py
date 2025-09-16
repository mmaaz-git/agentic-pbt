"""Property-based tests for requests.status_codes module."""
import string
from hypothesis import given, strategies as st, assume
import requests.status_codes


def test_lookupdict_getitem_get_consistency():
    """Property: codes[key] should equal codes.get(key) for any key."""
    codes = requests.status_codes.codes
    
    @given(st.text())
    def check_consistency(key):
        assert codes[key] == codes.get(key)
    
    check_consistency()


def test_lookupdict_none_default():
    """Property: Non-existent keys should return None, not raise KeyError."""
    codes = requests.status_codes.codes
    
    @given(st.text(min_size=1))
    def check_none_default(key):
        # Filter out keys that actually exist
        assume(not hasattr(codes, key))
        
        # Should not raise KeyError
        result = codes[key]
        assert result is None
        
        # get() should also return None
        assert codes.get(key) is None
    
    check_none_default()


def test_lookupdict_get_with_default():
    """Property: get(key, default) should return default for non-existent keys."""
    codes = requests.status_codes.codes
    
    @given(st.text(min_size=1), st.integers())
    def check_get_default(key, default_value):
        # Filter out keys that actually exist
        assume(not hasattr(codes, key))
        
        assert codes.get(key, default_value) == default_value
    
    check_get_default()


def test_case_consistency():
    """Property: For alphabetic status code names, uppercase and lowercase versions should have same value."""
    codes = requests.status_codes.codes
    
    # Get all alphabetic attributes
    alphabetic_attrs = [
        attr for attr in dir(codes) 
        if not attr.startswith('_') and attr.isalpha() and attr.islower()
    ]
    
    for attr in alphabetic_attrs:
        lower_value = getattr(codes, attr, None)
        upper_value = getattr(codes, attr.upper(), None)
        
        if lower_value is not None and upper_value is not None:
            assert lower_value == upper_value, f"Mismatch for {attr}: {lower_value} != {upper_value}"


def test_dict_vs_attribute_access():
    """Property: codes[key] should equal getattr(codes, key, None) for existing keys."""
    codes = requests.status_codes.codes
    
    # Test all existing attributes
    for attr in dir(codes):
        if not attr.startswith('_'):
            dict_access = codes[attr]
            attr_access = getattr(codes, attr, None)
            assert dict_access == attr_access, f"Mismatch for {attr}: {dict_access} != {attr_access}"


def test_lookupdict_with_numeric_strings():
    """Property: LookupDict should handle numeric strings consistently."""
    codes = requests.status_codes.codes
    
    @given(st.integers(100, 999))
    def check_numeric_strings(num):
        str_num = str(num)
        
        # Both should return None or same value
        result1 = codes[str_num]
        result2 = codes.get(str_num)
        assert result1 == result2
        
        # If it exists as attribute, dict access should match
        if hasattr(codes, str_num):
            assert result1 == getattr(codes, str_num)
    
    check_numeric_strings()


def test_lookupdict_special_characters():
    """Property: LookupDict should handle special character keys consistently."""
    codes = requests.status_codes.codes
    
    @given(st.text(alphabet=string.punctuation, min_size=1, max_size=10))
    def check_special_chars(key):
        # Should not raise exception
        result = codes[key]
        assert result == codes.get(key)
        
        # If exists as attribute, should match
        if hasattr(codes, key):
            assert result == getattr(codes, key, None)
    
    check_special_chars()


def test_lookupdict_empty_string():
    """Property: Empty string key should be handled consistently."""
    codes = requests.status_codes.codes
    
    assert codes[""] == codes.get("")
    if hasattr(codes, ""):
        assert codes[""] == getattr(codes, "", None)


def test_valid_http_status_codes():
    """Property: All status code values should be valid HTTP status codes (100-599)."""
    codes = requests.status_codes.codes
    
    for attr in dir(codes):
        if not attr.startswith('_'):
            value = getattr(codes, attr, None)
            if value is not None and isinstance(value, int):
                assert 100 <= value <= 599, f"Invalid status code for {attr}: {value}"


def test_lookupdict_initialization():
    """Property: New LookupDict instances should behave consistently."""
    
    @given(st.text())
    def check_new_instance(name):
        ld = requests.status_codes.LookupDict(name)
        
        # Should have the name set
        assert ld.name == name
        
        # Should be empty dict
        assert len(ld) == 0
        assert list(ld.keys()) == []
        assert list(ld.items()) == []
        
        # Should return None for any key
        assert ld["anything"] is None
        assert ld.get("anything") is None
        
        # Test setting attributes
        ld.test_attr = 42
        assert ld["test_attr"] == 42
        assert ld.get("test_attr") == 42
        assert ld.test_attr == 42
    
    check_new_instance()


if __name__ == "__main__":
    # Run the tests
    test_lookupdict_getitem_get_consistency()
    test_lookupdict_none_default()
    test_lookupdict_get_with_default()
    test_case_consistency()
    test_dict_vs_attribute_access()
    test_lookupdict_with_numeric_strings()
    test_lookupdict_special_characters()
    test_lookupdict_empty_string()
    test_valid_http_status_codes()
    test_lookupdict_initialization()
    print("All tests passed!")