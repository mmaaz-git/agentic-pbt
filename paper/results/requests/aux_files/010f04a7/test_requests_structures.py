"""Property-based tests for requests.structures module."""

import math
from hypothesis import assume, given, strategies as st, settings
import pytest
from requests.structures import CaseInsensitiveDict, LookupDict


# Strategy for generating valid string keys
string_keys = st.text(min_size=1, alphabet=st.characters(blacklist_categories=("Cc", "Cs")))
# Values can be any json-serializable data
json_values = st.recursive(
    st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False, allow_infinity=False) | st.text(),
    lambda children: st.lists(children) | st.dictionaries(st.text(), children),
    max_leaves=5
)


class TestCaseInsensitiveDict:
    """Test properties of CaseInsensitiveDict."""
    
    @given(string_keys, json_values)
    def test_case_insensitive_retrieval(self, key, value):
        """Keys should be retrievable regardless of case."""
        cid = CaseInsensitiveDict()
        cid[key] = value
        
        # Should be able to retrieve with any case variation
        assert cid[key.lower()] == value
        assert cid[key.upper()] == value
        assert cid[key.title()] == value
        
        # Contains should also be case-insensitive
        assert key.lower() in cid
        assert key.upper() in cid
        assert key.title() in cid
    
    @given(st.dictionaries(string_keys, json_values, min_size=1))
    def test_round_trip_key_preservation(self, data):
        """Original key case should be preserved when iterating."""
        cid = CaseInsensitiveDict(data)
        
        # The keys returned should match the original case of last set
        keys_list = list(cid.keys())
        
        # After setting with specific case, that case should be preserved
        for key, value in data.items():
            cid[key] = value
            assert key in list(cid.keys())
    
    @given(st.dictionaries(string_keys, json_values))
    def test_equality_case_insensitive(self, data):
        """Two dicts with same keys (different case) and values should be equal."""
        cid1 = CaseInsensitiveDict(data)
        cid2 = CaseInsensitiveDict()
        
        # Add same data but with different case keys
        for key, value in data.items():
            cid2[key.upper()] = value
        
        # Should be equal despite different case
        assert cid1 == cid2
    
    @given(st.dictionaries(string_keys, json_values))
    def test_copy_preserves_structure(self, data):
        """Copy should create an equivalent dict."""
        cid = CaseInsensitiveDict(data)
        cid_copy = cid.copy()
        
        # Should be equal
        assert cid == cid_copy
        
        # Should be separate objects
        assert cid is not cid_copy
        assert cid._store is not cid_copy._store
        
        # Modifying copy shouldn't affect original
        if data:
            key = list(data.keys())[0]
            cid_copy[key] = "modified"
            assert cid[key] != "modified" or data[key] == "modified"
    
    @given(st.dictionaries(string_keys, json_values))
    def test_lower_items_all_lowercase(self, data):
        """lower_items() should return all keys in lowercase."""
        cid = CaseInsensitiveDict(data)
        
        for key, value in cid.lower_items():
            assert key == key.lower()
            # Value should be retrievable with this key
            assert cid[key] == value
    
    @given(st.dictionaries(string_keys, json_values, min_size=1))
    def test_len_consistency(self, data):
        """Length should be consistent with number of unique lowercase keys."""
        cid = CaseInsensitiveDict()
        
        # Count unique lowercase keys
        unique_lower_keys = set()
        for key, value in data.items():
            cid[key] = value
            unique_lower_keys.add(key.lower())
        
        assert len(cid) == len(unique_lower_keys)
    
    @given(st.dictionaries(string_keys, json_values, min_size=1))
    def test_delitem_consistency(self, data):
        """Deleting items should work case-insensitively."""
        cid = CaseInsensitiveDict(data)
        
        for key in list(data.keys()):
            # Should be able to delete with any case
            del cid[key.upper()]
            
            # Should no longer be present with any case
            assert key not in cid
            assert key.lower() not in cid
            assert key.upper() not in cid
    
    @given(string_keys, json_values, json_values)
    def test_setdefault_case_insensitive(self, key, value1, value2):
        """setdefault should work case-insensitively."""
        cid = CaseInsensitiveDict()
        
        # First setdefault should set the value
        result1 = cid.setdefault(key, value1)
        assert result1 == value1
        assert cid[key] == value1
        
        # Second setdefault with different case should return existing value
        result2 = cid.setdefault(key.upper(), value2)
        assert result2 == value1  # Should return existing value, not value2
        assert cid[key] == value1  # Value shouldn't change
    
    @given(st.dictionaries(string_keys, json_values, min_size=1))
    def test_pop_case_insensitive(self, data):
        """pop should work case-insensitively."""
        cid = CaseInsensitiveDict(data)
        key = list(data.keys())[0]
        expected_value = data[key]
        
        # Should be able to pop with different case
        popped = cid.pop(key.upper())
        assert popped == expected_value
        
        # Key should be gone with any case
        assert key not in cid
        assert key.lower() not in cid
        assert key.upper() not in cid
    
    @given(st.dictionaries(string_keys, json_values))
    def test_update_case_handling(self, data):
        """update() should handle case-insensitive keys properly."""
        cid = CaseInsensitiveDict()
        
        # Add initial data
        cid.update(data)
        
        # Update with same keys but different case
        update_data = {k.upper(): v for k, v in data.items()}
        cid.update(update_data)
        
        # Should have same number of keys (case-insensitive)
        unique_lower_keys = {k.lower() for k in data.keys()}
        assert len(cid) == len(unique_lower_keys)
        
        # All values should be accessible
        for key, value in data.items():
            assert cid[key] == value


class TestLookupDict:
    """Test properties of LookupDict."""
    
    @given(string_keys, json_values)
    def test_attribute_vs_dict_inconsistency(self, key, value):
        """LookupDict has a bug: it stores in __dict__ but inherits from dict."""
        ld = LookupDict(name="test")
        
        # Setting via setattr
        setattr(ld, key, value)
        
        # Should be retrievable via __getitem__ according to implementation
        result = ld[key]
        assert result == value
        
        # But it's NOT in the dict itself!
        assert key not in dict.keys(ld)
        assert len(ld) == 0  # The dict is empty!
        
        # This is a design bug - it inherits from dict but doesn't use dict storage
    
    @given(string_keys, json_values)
    def test_get_vs_getitem_consistency(self, key, value):
        """get() and __getitem__ should behave consistently."""
        ld = LookupDict(name="test")
        
        # Set a value
        setattr(ld, key, value)
        
        # Both should return the same value
        assert ld[key] == ld.get(key)
        assert ld.get(key) == value
    
    @given(string_keys)
    def test_missing_key_returns_none(self, key):
        """Missing keys should return None instead of raising KeyError."""
        ld = LookupDict(name="test")
        
        # Should return None for missing keys
        assert ld[key] is None
        assert ld.get(key) is None
        assert ld.get(key, "default") == "default"
    
    @given(string_keys, json_values)
    def test_dict_methods_dont_work(self, key, value):
        """Dict methods don't work properly with LookupDict's storage."""
        ld = LookupDict(name="test")
        
        # Set via attribute
        setattr(ld, key, value)
        
        # Dict methods won't see it
        assert list(ld.keys()) == []
        assert list(ld.values()) == []
        assert list(ld.items()) == []
        assert len(ld) == 0
        
        # But it's accessible via __getitem__
        assert ld[key] == value
    
    @given(st.dictionaries(string_keys, json_values, min_size=1))
    def test_standard_dict_operations_broken(self, data):
        """Standard dict operations are broken in LookupDict."""
        ld = LookupDict(name="test")
        
        # Try to use it as a normal dict
        for key, value in data.items():
            ld[key] = value  # This uses dict.__setitem__
        
        # These should work for a normal dict
        assert len(ld) == len(data)
        
        # But __getitem__ is overridden to look in __dict__
        for key in data:
            # This will return None because __getitem__ looks in __dict__, not the dict storage!
            assert ld[key] is None  # This is wrong behavior!
        
        # The values are in the dict storage but not accessible via __getitem__
        for key, value in dict.items(ld):
            assert ld[key] != value  # __getitem__ returns None or different value!