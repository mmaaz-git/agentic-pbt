import math
import string
from hypothesis import given, strategies as st, assume, settings
import pytest
from requests.structures import CaseInsensitiveDict, LookupDict


# Strategies for valid string keys
valid_keys = st.text(min_size=1, alphabet=string.printable).filter(lambda x: x.strip())
valid_values = st.one_of(
    st.text(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.none(),
    st.lists(st.text()),
)

# CaseInsensitiveDict tests

@given(st.dictionaries(valid_keys, valid_values))
def test_caseinsensitive_dict_case_insensitivity(data):
    """Test that CaseInsensitiveDict retrieves values regardless of key case."""
    cid = CaseInsensitiveDict(data)
    
    for key, value in data.items():
        # Test various case combinations
        assert cid[key.lower()] == value
        assert cid[key.upper()] == value
        if key:  # Only test if key is non-empty
            assert cid[key.swapcase()] == value
            # Test mixed case
            mixed_key = ''.join(c.upper() if i % 2 else c.lower() 
                              for i, c in enumerate(key))
            assert cid[mixed_key] == value


@given(st.dictionaries(valid_keys, valid_values))
def test_caseinsensitive_dict_copy_equality(data):
    """Test that copying a CaseInsensitiveDict preserves equality."""
    cid = CaseInsensitiveDict(data)
    cid_copy = cid.copy()
    
    assert cid == cid_copy
    assert list(cid.keys()) == list(cid_copy.keys())
    assert list(cid.values()) == list(cid_copy.values())


@given(st.dictionaries(valid_keys, valid_values))
def test_caseinsensitive_dict_len_invariant(data):
    """Test that len() matches the number of unique lowercase keys."""
    cid = CaseInsensitiveDict()
    
    # Track unique lowercase keys
    unique_lower_keys = set()
    
    for key, value in data.items():
        cid[key] = value
        unique_lower_keys.add(key.lower())
    
    assert len(cid) == len(unique_lower_keys)
    assert len(list(cid)) == len(cid)
    assert len(list(cid.keys())) == len(cid)
    assert len(list(cid.values())) == len(cid)
    assert len(list(cid.items())) == len(cid)


@given(st.dictionaries(valid_keys, valid_values))
def test_caseinsensitive_dict_update_preserves_last_case(data):
    """Test that the last set key case is preserved in iteration."""
    cid = CaseInsensitiveDict()
    
    # Track the last case for each lowercase key
    last_case = {}
    
    for key, value in data.items():
        cid[key] = value
        last_case[key.lower()] = key
    
    # Check that iteration uses the last set case
    for actual_key in cid.keys():
        assert actual_key == last_case[actual_key.lower()]


@given(st.dictionaries(valid_keys, valid_values, min_size=1))
def test_caseinsensitive_dict_pop_behavior(data):
    """Test that pop works with case-insensitive keys."""
    cid = CaseInsensitiveDict(data)
    
    # Pick a random key to pop
    key = list(data.keys())[0]
    expected_value = data[key]
    
    # Pop with different cases should work
    value = cid.pop(key.upper())
    assert value == expected_value
    
    # Key should be gone regardless of case
    with pytest.raises(KeyError):
        _ = cid[key]
    with pytest.raises(KeyError):
        _ = cid[key.lower()]
    with pytest.raises(KeyError):
        _ = cid[key.upper()]


@given(st.dictionaries(valid_keys, valid_values))
def test_caseinsensitive_dict_setdefault(data):
    """Test setdefault with case-insensitive keys."""
    cid = CaseInsensitiveDict(data)
    
    for key, value in data.items():
        # setdefault with existing key (different case) should return existing value
        result = cid.setdefault(key.upper(), "different_value")
        assert result == value
        assert cid[key.lower()] == value  # Original value unchanged


# LookupDict tests

@given(valid_keys, valid_values)
def test_lookupdict_getitem_vs_dict_storage(key, value):
    """Test that LookupDict's __getitem__ uses __dict__ not parent dict."""
    ld = LookupDict(name="test")
    
    # Set via dict's __setitem__
    dict.__setitem__(ld, key, value)
    
    # __getitem__ should NOT find it (because it looks in __dict__)
    result = ld[key]
    assert result is None  # Returns None instead of the value!
    
    # But dict.get should find it
    assert ld.get(key) is None  # Also uses __dict__!
    
    # Regular dict access should work
    assert dict.__getitem__(ld, key) == value


@given(valid_keys, valid_values)
def test_lookupdict_attribute_vs_item_access(key, value):
    """Test the mismatch between attribute and item access."""
    ld = LookupDict(name="test")
    
    # Set as attribute
    if key.isidentifier() and not key.startswith('_'):
        setattr(ld, key, value)
        
        # Should be accessible via __getitem__
        assert ld[key] == value
        
        # But NOT via dict methods
        assert key not in ld  # This uses dict's __contains__
        assert len(ld) == 0  # Dict is empty!
        
        # This shows the dict storage is separate from __dict__
        dict.__setitem__(ld, key, "different")
        assert ld[key] == value  # Still returns attribute value
        assert dict.__getitem__(ld, key) == "different"


@given(valid_keys)
def test_lookupdict_get_method_uses_dict_not_parent(key):
    """Test that get() method also uses __dict__ instead of parent dict."""
    ld = LookupDict(name="test")
    
    # Add to parent dict
    dict.__setitem__(ld, key, "value_in_dict")
    
    # get() returns None because it checks __dict__
    assert ld.get(key) is None
    assert ld.get(key, "default") == "default"
    
    # But if we set via attribute
    if key.isidentifier() and not key.startswith('_'):
        setattr(ld, key, "value_in_dict_attr")
        assert ld.get(key) == "value_in_dict_attr"


@given(st.dictionaries(valid_keys, valid_values, min_size=1))
def test_lookupdict_iteration_ignores_attributes(data):
    """Test that iteration only sees dict items, not attributes."""
    ld = LookupDict(name="test")
    
    # Set some attributes
    attrs_set = {}
    dict_set = {}
    for i, (key, value) in enumerate(data.items()):
        if i < len(data) // 2 and key.isidentifier() and not key.startswith('_'):
            setattr(ld, key, value)
            attrs_set[key] = value
        else:
            dict.__setitem__(ld, key, value)
            dict_set[key] = value
    
    # Iteration only sees dict items
    dict_items = {k for k in ld}
    
    # Check that dict iteration matches what we put in dict
    assert dict_items == set(dict_set.keys())
    
    # Check that attributes are accessible via __getitem__ but not in iteration
    for key, value in attrs_set.items():
        if key not in dict_set:  # Only if not overridden in dict
            assert ld[key] == value  # Accessible via __getitem__
            assert key not in dict_items  # But not in iteration