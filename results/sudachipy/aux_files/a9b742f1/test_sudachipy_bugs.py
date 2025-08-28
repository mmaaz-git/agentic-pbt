#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, HealthCheck, example
import sudachipy
from sudachipy import config
import json

# Test 1: _filter_nulls mutates the input dictionary - this is a potential bug!
@given(st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.one_of(st.none(), st.text(), st.integers()),
    min_size=1, max_size=5
))
@example({"a": None, "b": "value"})
def test_filter_nulls_mutates_input_bug(data):
    """_filter_nulls should not mutate its input, but it does!"""
    original = data.copy()
    original_keys = set(original.keys())
    
    # Call the function
    filtered = config._filter_nulls(data)
    
    # Check if input was mutated
    if any(v is None for v in original.values()):
        # Bug: The function mutates the input dict!
        assert data != original, "Input dictionary was mutated"
        assert filtered is data, "Returns the same object, not a copy"
        
        # The None values are removed from the original dict
        assert None not in data.values()
        
        # Keys with None values are deleted
        for key in original_keys:
            if original[key] is None:
                assert key not in data

# Test 2: Special characters in JSON with better strategy
@given(
    system=st.one_of(
        st.just('"quoted"'),
        st.just('back\\slash'),
        st.just('new\nline'),
        st.just('tab\ttab'),
        st.just('\r\nwindows'),
        st.text(min_size=1).map(lambda x: x + '"' + x),
        st.text(min_size=1).map(lambda x: '\\' + x)
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_config_json_special_chars_fixed(system):
    cfg = config.Config(system=system)
    json_str = cfg.as_jsons()
    
    # Should properly escape special characters
    parsed = json.loads(json_str)
    assert parsed.get("system") == system
    
    # Round-trip should preserve the value
    re_serialized = json.dumps(parsed)
    re_parsed = json.loads(re_serialized)
    assert re_parsed.get("system") == system

# Test 3: Demonstrate the mutation bug with a simple example
def test_filter_nulls_mutation_demo():
    """Demonstrate that _filter_nulls mutates its input"""
    # Create a dict with None values
    test_dict = {"keep": "value", "remove": None, "another": 42}
    original = test_dict.copy()
    
    # Call _filter_nulls
    result = config._filter_nulls(test_dict)
    
    # Show the mutation
    print(f"Original dict (copy): {original}")
    print(f"Dict after _filter_nulls: {test_dict}")
    print(f"Result: {result}")
    print(f"Result is same object as input: {result is test_dict}")
    
    # The input dict was mutated!
    assert test_dict != original
    assert "remove" not in test_dict
    assert result is test_dict

# Test 4: Config with None values gets mutated during as_jsons
@given(
    st.dictionaries(
        st.sampled_from(["system", "user", "connectionCostPlugin"]),
        st.one_of(st.none(), st.text()),
        min_size=1
    )
)
def test_config_dict_mutation_through_as_jsons(config_dict):
    """Test if creating Config and calling as_jsons mutates the input dict"""
    # Skip if user is not a list
    if "user" in config_dict and config_dict["user"] is not None:
        if not isinstance(config_dict["user"], list):
            config_dict["user"] = [config_dict["user"]]
    
    # Create a Config object
    cfg = config.Config(**config_dict)
    
    # Check the original values
    original_values = {}
    for key in config_dict:
        original_values[key] = getattr(cfg, key)
    
    # Call as_jsons - this internally calls _filter_nulls
    json_str = cfg.as_jsons()
    
    # The Config object fields should not change
    for key in config_dict:
        assert getattr(cfg, key) == original_values[key]