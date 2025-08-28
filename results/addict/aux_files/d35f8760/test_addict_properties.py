"""Property-based tests for addict.Dict using Hypothesis"""
import sys
import os
import pickle
import copy
sys.path.insert(0, '/root/hypothesis-llm/envs/addict_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import hypothesis
from addict import Dict


# Strategy for generating nested dictionaries
def dict_strategy(max_depth=3):
    """Generate nested dictionaries with various types of values"""
    if max_depth <= 0:
        return st.dictionaries(
            st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'),
            st.one_of(
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.text(max_size=20),
                st.booleans(),
                st.none(),
                st.lists(st.integers(), max_size=5)
            )
        )
    
    return st.dictionaries(
        st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'),
        st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(max_size=20),
            st.booleans(),
            st.none(),
            st.lists(st.integers(), max_size=5),
            st.deferred(lambda: dict_strategy(max_depth - 1))
        ),
        max_size=5
    )


@given(dict_strategy())
def test_round_trip_to_dict(d):
    """Test that Dict(d).to_dict() == d for plain dictionaries"""
    addict_dict = Dict(d)
    result = addict_dict.to_dict()
    assert result == d, f"Round-trip failed: {result} != {d}"


@given(dict_strategy())
def test_attribute_access_equivalence(d):
    """Test that d.key == d['key'] for all valid keys"""
    assume(len(d) > 0)
    # Filter out keys that would conflict with dict methods
    valid_keys = [k for k in d.keys() if not hasattr(dict, k) and k.isidentifier()]
    assume(len(valid_keys) > 0)
    
    addict_dict = Dict(d)
    for key in valid_keys:
        attr_value = getattr(addict_dict, key)
        item_value = addict_dict[key]
        assert attr_value == item_value, f"Attribute access mismatch for key '{key}'"


@given(dict_strategy())
def test_deepcopy_independence(d):
    """Test that deepcopy creates truly independent objects"""
    original = Dict(d)
    copied = original.deepcopy()
    
    # Verify they start equal
    assert original.to_dict() == copied.to_dict()
    
    # Modify the copy and ensure original is unchanged
    if len(copied) > 0:
        first_key = list(copied.keys())[0]
        copied[first_key] = "modified_value"
        assert original[first_key] != "modified_value" or d[first_key] == "modified_value"


@given(dict_strategy(), dict_strategy())
def test_update_merge_behavior(d1, d2):
    """Test that update correctly merges dictionaries"""
    addict_dict = Dict(d1)
    addict_dict.update(d2)
    
    # Check that all keys from d2 are in the result
    for key in d2:
        assert key in addict_dict
        
        # For non-dict values, should be directly replaced
        if not isinstance(d1.get(key), dict) or not isinstance(d2[key], dict):
            assert addict_dict[key] == d2[key] or (isinstance(addict_dict[key], Dict) and addict_dict[key].to_dict() == d2[key])


@given(dict_strategy())
def test_freeze_prevents_new_keys(d):
    """Test that frozen Dict objects reject new keys"""
    addict_dict = Dict(d)
    addict_dict.freeze()
    
    # Try to add a new key that doesn't exist
    new_key = "new_test_key_xyz"
    while new_key in d:
        new_key += "_"
    
    try:
        addict_dict[new_key] = "should_fail"
        assert False, "Should have raised KeyError for frozen dict"
    except KeyError:
        pass  # Expected behavior


@given(dict_strategy())
def test_freeze_allows_existing_key_modification(d):
    """Test that frozen Dict objects allow modifying existing keys"""
    assume(len(d) > 0)
    addict_dict = Dict(d)
    addict_dict.freeze()
    
    # Modify an existing key
    first_key = list(d.keys())[0]
    addict_dict[first_key] = "modified_value"
    assert addict_dict[first_key] == "modified_value"


@given(dict_strategy())
def test_pickle_round_trip(d):
    """Test that Dict objects survive pickling and unpickling"""
    original = Dict(d)
    pickled = pickle.dumps(original)
    unpickled = pickle.loads(pickled)
    
    assert unpickled.to_dict() == original.to_dict()
    assert type(unpickled) == type(original)


@given(dict_strategy(), dict_strategy())
def test_or_operator_merge(d1, d2):
    """Test that the | operator correctly merges dictionaries"""
    dict1 = Dict(d1)
    dict2 = Dict(d2)
    
    result = dict1 | dict2
    
    # All keys from both dicts should be present
    for key in d1:
        assert key in result
    for key in d2:
        assert key in result
        # Keys from d2 should override keys from d1
        if isinstance(result[key], Dict):
            assert result[key].to_dict() == d2[key]
        else:
            assert result[key] == d2[key]


@given(st.dictionaries(
    st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'),
    st.integers()
))
def test_auto_vivification(d):
    """Test that accessing non-existent keys creates new Dict objects"""
    addict_dict = Dict(d)
    
    # Access a non-existent nested path
    new_key = "nonexistent_key_abc"
    while new_key in d:
        new_key += "_"
    
    # This should create a new Dict object
    nested = addict_dict[new_key]
    assert isinstance(nested, Dict)
    assert len(nested) == 0
    
    # We should be able to set values on it
    nested["sub_key"] = "value"
    assert addict_dict[new_key]["sub_key"] == "value"


@given(st.lists(st.integers()))
def test_constructor_with_empty_args(empty_args):
    """Test that Dict constructor handles empty arguments correctly"""
    # Constructor should skip empty arguments
    args = [None, {}, None, {}] + empty_args
    d = Dict(*[a for a in args if not a])
    assert len(d) == 0


@given(dict_strategy())
def test_missing_key_behavior_when_frozen(d):
    """Test __missing__ raises KeyError when frozen"""
    addict_dict = Dict(d)
    addict_dict.freeze()
    
    new_key = "missing_key_test"
    while new_key in d:
        new_key += "_"
    
    try:
        _ = addict_dict[new_key]
        assert False, "Should have raised KeyError for missing key when frozen"
    except KeyError:
        pass  # Expected


@given(st.dictionaries(
    st.text(min_size=1, max_size=5, alphabet='abc'),
    st.lists(st.dictionaries(st.text(min_size=1, max_size=5), st.integers()))
))
def test_hook_converts_lists_of_dicts(d):
    """Test that _hook recursively converts lists containing dicts"""
    addict_dict = Dict(d)
    
    for key, value in addict_dict.items():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    assert isinstance(item, Dict), "Dict in list should be converted to Dict type"


if __name__ == "__main__":
    # Run a quick smoke test
    print("Running property-based tests for addict.Dict...")
    test_round_trip_to_dict()
    test_attribute_access_equivalence()
    test_deepcopy_independence()
    test_update_merge_behavior()
    test_freeze_prevents_new_keys()
    test_freeze_allows_existing_key_modification()
    test_pickle_round_trip()
    test_or_operator_merge()
    test_auto_vivification()
    test_constructor_with_empty_args()
    test_missing_key_behavior_when_frozen()
    test_hook_converts_lists_of_dicts()
    print("All smoke tests passed!")