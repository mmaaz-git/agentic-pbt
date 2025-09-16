#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/addict_env/lib/python3.13/site-packages')

import copy
import pytest
from hypothesis import given, assume, strategies as st, settings
from addict import Dict


# Strategy for valid dictionary keys (strings and integers primarily)
dict_keys = st.one_of(
    st.text(min_size=1, max_size=100).filter(lambda s: s.isidentifier()),  # Valid Python identifiers
    st.integers(),
)

# Strategy for simple values
simple_values = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(max_size=100),
)

# Recursive strategy for nested dictionaries
@st.composite
def nested_dicts(draw, max_depth=3):
    if max_depth <= 0:
        return draw(simple_values)
    
    return draw(st.dictionaries(
        dict_keys,
        st.one_of(
            simple_values,
            st.deferred(lambda: nested_dicts(max_depth=max_depth-1))
        ),
        min_size=0,
        max_size=5
    ))


class TestDictProperties:
    
    @given(nested_dicts())
    def test_attribute_access_equals_key_access(self, data):
        """Property: For valid identifier keys, d.key should equal d['key']"""
        d = Dict(data)
        
        for key in d.keys():
            if isinstance(key, str) and key.isidentifier() and not key.startswith('_'):
                # Attribute access should equal key access
                assert getattr(d, key) == d[key]
    
    @given(nested_dicts())
    def test_to_dict_round_trip(self, data):
        """Property: Dict(d.to_dict()) should preserve all data"""
        d1 = Dict(data)
        regular = d1.to_dict()
        d2 = Dict(regular)
        
        # The data should be preserved
        assert d1 == d2
        assert d1.to_dict() == d2.to_dict()
        
        # to_dict should return regular dicts
        assert type(regular) == dict
        for key, val in regular.items():
            if isinstance(val, dict):
                assert type(val) == dict
    
    @given(nested_dicts(), dict_keys)
    def test_frozen_dict_rejects_new_keys(self, data, new_key):
        """Property: Frozen dicts should raise KeyError for new keys"""
        d = Dict(data)
        assume(new_key not in d)  # Only test with keys that don't exist
        
        d.freeze()
        
        # Should raise KeyError when trying to add new key
        with pytest.raises(KeyError):
            d[new_key] = "new_value"
        
        # Should also raise for attribute access
        if isinstance(new_key, str) and new_key.isidentifier():
            with pytest.raises(KeyError):
                setattr(d, new_key, "new_value")
        
        # Existing keys should still be modifiable
        if len(d) > 0:
            existing_key = list(d.keys())[0]
            d[existing_key] = "modified"  # Should not raise
    
    @given(nested_dicts())
    def test_deep_copy_independence(self, data):
        """Property: Changes to deepcopy should not affect original"""
        d1 = Dict(data)
        d2 = d1.deepcopy()
        
        # They should initially be equal
        assert d1 == d2
        
        # Modify the copy
        d2['new_key'] = 'new_value'
        
        # Original should be unchanged
        assert 'new_key' not in d1
        assert d1 != d2
        
        # Modify nested values in copy
        if len(d2) > 0:
            key = list(d2.keys())[0]
            if isinstance(d2[key], Dict):
                d2[key]['nested_new'] = 'nested_value'
                assert 'nested_new' not in d1.get(key, {})
    
    @given(nested_dicts(), nested_dicts())
    def test_update_preserves_nested_structure(self, data1, data2):
        """Property: update() should merge nested dicts, not replace them"""
        d1 = Dict(data1)
        d2 = Dict(data2)
        
        # Create a deep copy to compare later
        original_d1 = d1.deepcopy()
        
        # Perform update
        d1.update(d2)
        
        # For any key that was a dict in both, it should be merged
        for key in original_d1.keys():
            if key in d2:
                if isinstance(original_d1[key], dict) and isinstance(d2[key], dict):
                    # Should have keys from both
                    for nested_key in original_d1[key]:
                        if nested_key not in d2[key]:
                            assert nested_key in d1[key]
    
    @given(st.lists(st.tuples(dict_keys, simple_values), max_size=10))
    def test_init_from_tuple_list(self, tuple_list):
        """Property: Dict should correctly initialize from list of tuples"""
        # Filter out duplicate keys to avoid ambiguity
        seen_keys = set()
        filtered_list = []
        for k, v in tuple_list:
            if k not in seen_keys:
                filtered_list.append((k, v))
                seen_keys.add(k)
        
        d = Dict(filtered_list)
        
        # All tuples should be in the dict
        for key, val in filtered_list:
            assert key in d
            assert d[key] == val
    
    @given(nested_dicts(), nested_dicts())
    def test_dict_union_operator(self, data1, data2):
        """Property: Dict union (|) should combine dicts correctly"""
        d1 = Dict(data1)
        d2 = Dict(data2)
        
        # Test | operator
        d3 = d1 | d2
        
        # d3 should have all keys from both
        for key in d1:
            if key not in d2:
                assert d3[key] == d1[key]
        
        for key in d2:
            assert d3[key] == d2[key]  # d2 values should override d1
        
        # Original dicts should be unchanged
        assert d1 == Dict(data1)
        assert d2 == Dict(data2)
    
    @given(dict_keys, simple_values)
    def test_setdefault_behavior(self, key, default_value):
        """Property: setdefault should return existing value or set and return default"""
        d = Dict()
        
        # First setdefault should return the default and set it
        result1 = d.setdefault(key, default_value)
        assert result1 == default_value
        assert d[key] == default_value
        
        # Second setdefault should return existing value
        other_value = "different" if default_value != "different" else "another"
        result2 = d.setdefault(key, other_value)
        assert result2 == default_value  # Should return original, not new default
        assert d[key] == default_value  # Should not change
    
    @given(nested_dicts())
    def test_empty_dict_addition(self, data):
        """Property: Empty Dict + other should return other (per __add__ implementation)"""
        d1 = Dict()  # Empty
        d2 = Dict(data)
        
        # According to the code, empty dict + other returns other
        result = d1 + d2
        assert result == d2
        
        # Non-empty dict + other should raise TypeError
        if len(d2) > 0:
            with pytest.raises(TypeError):
                result = d2 + d1
    
    @given(st.dictionaries(dict_keys, simple_values, min_size=1))
    def test_recursive_freeze_unfreeze(self, data):
        """Property: freeze() should recursively freeze nested Dicts"""
        # Create nested structure
        d = Dict({'level1': Dict({'level2': Dict(data)})})
        
        # Freeze the top level
        d.freeze()
        
        # All levels should be frozen
        with pytest.raises(KeyError):
            d['new_key'] = 'value'
        
        with pytest.raises(KeyError):
            d.level1['new_key'] = 'value'
            
        with pytest.raises(KeyError):
            d.level1.level2['new_key'] = 'value'
        
        # Unfreeze
        d.unfreeze()
        
        # All levels should be unfrozen
        d['new_key'] = 'value'
        d.level1['new_key'] = 'value'
        d.level1.level2['new_key'] = 'value'
        
        assert d['new_key'] == 'value'
        assert d.level1['new_key'] == 'value'
        assert d.level1.level2['new_key'] == 'value'


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v"])