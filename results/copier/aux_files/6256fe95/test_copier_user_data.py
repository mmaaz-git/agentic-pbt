"""Property-based tests for copier._user_data module."""

import json
from datetime import datetime
from typing import Any

import yaml
from hypothesis import assume, given, strategies as st
from hypothesis import settings

# Import the module under test
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')
from copier._user_data import (
    AnswersMap,
    Question,
    parse_yaml_string,
    parse_yaml_list,
    load_answersfile_data,
    CAST_STR_TO_NATIVE,
)
from copier._types import MISSING
from jinja2.sandbox import SandboxedEnvironment


# Property 1: YAML round-trip for parse_yaml_string
@given(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-1e10, max_value=1e10),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
        st.text(min_size=0, max_size=1000),
        st.lists(st.text(max_size=100), max_size=10),
        st.dictionaries(st.text(min_size=1, max_size=20), st.text(max_size=100), max_size=10)
    )
)
@settings(max_examples=1000)
def test_parse_yaml_string_round_trip(value):
    """Test that parsing YAML after dumping preserves the value."""
    # First dump to YAML string
    yaml_str = yaml.safe_dump(value)
    # Then parse it back
    parsed = parse_yaml_string(yaml_str)
    # Should get back the same value
    if isinstance(value, float):
        # Handle float precision issues
        assert abs(parsed - value) < 1e-9 or parsed == value
    else:
        assert parsed == value


# Property 2: parse_yaml_list always returns a list
@given(st.text(min_size=1))
def test_parse_yaml_list_returns_list_or_raises(yaml_str):
    """Test that parse_yaml_list either returns a list or raises ValueError."""
    try:
        result = parse_yaml_list(yaml_str)
        assert isinstance(result, list)
    except (ValueError, yaml.error.YAMLError):
        # Expected for non-list YAML strings
        pass


# Property 3: parse_yaml_list preserves raw strings for valid lists
@given(st.lists(st.one_of(
    st.integers(min_value=-1000, max_value=1000),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=0, max_size=100),
    st.booleans()
), min_size=1, max_size=10))
def test_parse_yaml_list_preserves_items(items):
    """Test that parse_yaml_list preserves the raw string representation of items."""
    # Create a YAML list string
    yaml_str = yaml.safe_dump(items, default_flow_style=False)
    
    # Parse it as a raw list
    parsed_list = parse_yaml_list(yaml_str)
    
    # The number of items should match
    assert len(parsed_list) == len(items)
    
    # Each parsed item, when parsed as YAML again, should match the original
    for parsed_raw, original in zip(parsed_list, items):
        reparsed = yaml.safe_load(parsed_raw)
        if isinstance(original, float):
            assert abs(reparsed - original) < 1e-9 or reparsed == original
        else:
            assert reparsed == original


# Property 4: AnswersMap.combined contains all individual maps
@given(
    user=st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), max_size=5),
    init=st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), max_size=5),
    metadata=st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), max_size=5),
    last=st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), max_size=5),
    user_defaults=st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), max_size=5),
)
def test_answers_map_combined_contains_all(user, init, metadata, last, user_defaults):
    """Test that AnswersMap.combined contains values from all source maps with correct priority."""
    # Create an AnswersMap
    answers = AnswersMap(
        user=user,
        init=init,
        metadata=metadata,
        last=last,
        user_defaults=user_defaults
    )
    
    combined = answers.combined
    
    # Check that all keys from all maps are in combined
    all_keys = set()
    all_keys.update(user.keys(), init.keys(), metadata.keys(), last.keys(), user_defaults.keys())
    # Add special keys
    all_keys.update(["_external_data", "now", "make_secret"])
    
    for key in all_keys:
        assert key in combined
    
    # Check priority: user > init > metadata > last > user_defaults
    for key in user:
        assert combined[key] == user[key]
    
    for key in init:
        if key not in user:
            assert combined[key] == init[key]
    
    for key in metadata:
        if key not in user and key not in init:
            assert combined[key] == metadata[key]
    
    for key in last:
        if key not in user and key not in init and key not in metadata:
            assert combined[key] == last[key]
    
    for key in user_defaults:
        if key not in user and key not in init and key not in metadata and key not in last:
            assert combined[key] == user_defaults[key]


# Property 5: Type casting consistency
@given(
    st.sampled_from(["bool", "float", "int", "str"])
)
def test_cast_str_to_native_idempotent(type_name):
    """Test that casting functions are consistent."""
    cast_fn = CAST_STR_TO_NATIVE[type_name]
    
    # Generate appropriate test values
    if type_name == "bool":
        test_values = ["true", "false", "True", "False", "yes", "no", "1", "0"]
    elif type_name == "float":
        test_values = ["1.5", "-2.7", "0.0", "1e10", "-1e-5"]
    elif type_name == "int":
        test_values = ["1", "-5", "0", "1000000"]
    else:  # str
        test_values = ["hello", "world", "123", ""]
    
    for val_str in test_values:
        try:
            # Cast once
            result1 = cast_fn(val_str)
            # Cast the string again (should be idempotent for string input)
            result2 = cast_fn(val_str)
            assert result1 == result2
        except (ValueError, TypeError):
            # Some values might not be valid for the type
            pass


# Property 6: Question type validation
@given(
    var_name=st.text(min_size=1, max_size=20).filter(lambda x: x not in ["now", "make_secret"]),
    q_type=st.sampled_from(["str", "int", "float", "bool"])
)
def test_question_type_casting_preserves_type(var_name, q_type):
    """Test that Question correctly casts answers according to type."""
    # Create a minimal Question
    question = Question(
        var_name=var_name,
        answers=AnswersMap(),
        context={},
        jinja_env=SandboxedEnvironment(),
        type=q_type
    )
    
    # Generate appropriate test values
    if q_type == "bool":
        test_answer = "true"
        expected_type = bool
    elif q_type == "int":
        test_answer = "42"
        expected_type = int
    elif q_type == "float":
        test_answer = "3.14"
        expected_type = float
    else:  # str
        test_answer = "test string"
        expected_type = str
    
    # Cast the answer
    casted = question.cast_answer(test_answer)
    assert isinstance(casted, expected_type)


# Property 7: JSON/YAML type casting round-trip
@given(
    data=st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-1e6, max_value=1e6),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(max_size=100),
        st.lists(st.integers(), max_size=10),
        st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), max_size=5)
    )
)
def test_json_yaml_cast_round_trip(data):
    """Test that JSON and YAML casting are inverse operations."""
    # Test JSON round-trip
    json_str = json.dumps(data)
    json_cast_fn = CAST_STR_TO_NATIVE["json"]
    json_parsed = json_cast_fn(json_str)
    assert json_parsed == data
    
    # Test YAML round-trip
    yaml_str = yaml.safe_dump(data)
    yaml_cast_fn = CAST_STR_TO_NATIVE["yaml"]
    yaml_parsed = yaml_cast_fn(yaml_str)
    if isinstance(data, float):
        assert abs(yaml_parsed - data) < 1e-9 or yaml_parsed == data
    else:
        assert yaml_parsed == data