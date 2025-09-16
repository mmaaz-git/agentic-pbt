"""Property-based tests for pyramid.paster and related modules."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import assume, given, strategies as st, settings
import pytest
from pyramid.scripts.common import parse_vars


# Strategy for valid variable names (keys)
var_name = st.text(
    alphabet=st.characters(blacklist_categories=['Cc', 'Cs'], blacklist_characters='=\x00'),
    min_size=1,
    max_size=50
).filter(lambda x: x and not x.isspace())

# Strategy for variable values (can contain '=' signs)
var_value = st.text(
    alphabet=st.characters(blacklist_categories=['Cc', 'Cs'], blacklist_characters='\x00'),
    max_size=100
)


@given(st.dictionaries(var_name, var_value, min_size=1, max_size=10))
def test_parse_vars_round_trip(original_dict):
    """Test that parse_vars correctly parses and we can reconstruct the input."""
    # Create input list in the format parse_vars expects
    input_list = [f"{k}={v}" for k, v in original_dict.items()]
    
    # Parse it
    parsed = parse_vars(input_list)
    
    # Check that we get the same dictionary back
    assert parsed == original_dict


@given(var_name, var_value)
def test_parse_vars_single_equals_split(name, value):
    """Test that parse_vars splits on first '=' only, preserving '=' in values."""
    # This tests the documented behavior: split('=', 1)
    input_str = f"{name}={value}"
    result = parse_vars([input_str])
    
    assert result == {name: value}
    assert name in result
    assert result[name] == value


@given(st.text(min_size=1).filter(lambda x: '=' not in x))
def test_parse_vars_no_equals_raises_error(text):
    """Test that parse_vars raises ValueError for strings without '='."""
    with pytest.raises(ValueError) as exc_info:
        parse_vars([text])
    
    assert 'invalid' in str(exc_info.value).lower()
    assert 'no "="' in str(exc_info.value)


@given(var_value)
def test_parse_vars_empty_key(value):
    """Test parsing with empty key (edge case)."""
    input_str = f"={value}"
    result = parse_vars([input_str])
    
    # Empty key should still work according to the implementation
    assert result == {"": value}


@given(var_name)
def test_parse_vars_empty_value(name):
    """Test parsing with empty value."""
    input_str = f"{name}="
    result = parse_vars([input_str])
    
    assert result == {name: ""}


@given(st.lists(st.tuples(var_name, var_value), min_size=1, max_size=10))
def test_parse_vars_multiple_assignments(assignments):
    """Test parsing multiple variable assignments."""
    # Filter out duplicate keys to ensure predictable results
    seen_keys = set()
    unique_assignments = []
    for name, value in assignments:
        if name not in seen_keys:
            seen_keys.add(name)
            unique_assignments.append((name, value))
    
    input_list = [f"{k}={v}" for k, v in unique_assignments]
    result = parse_vars(input_list)
    
    assert len(result) == len(unique_assignments)
    for name, value in unique_assignments:
        assert result[name] == value


@given(var_name, st.lists(var_value, min_size=2, max_size=5))
def test_parse_vars_multiple_equals_in_value(name, value_parts):
    """Test that multiple '=' signs in the value are preserved."""
    # Join value parts with '=' to create a value with multiple '=' signs
    value = "=".join(value_parts)
    input_str = f"{name}={value}"
    
    result = parse_vars([input_str])
    
    assert result == {name: value}
    assert result[name].count('=') == len(value_parts) - 1


@given(st.lists(st.tuples(var_name, var_value), min_size=2, max_size=5))
def test_parse_vars_duplicate_keys_last_wins(assignments):
    """Test behavior with duplicate keys - last assignment should win."""
    assume(len(assignments) >= 2)
    
    # Create assignments with at least one duplicate key
    key = assignments[0][0]
    input_list = []
    expected_value = None
    
    for i, (name, value) in enumerate(assignments):
        if i == 0 or i == len(assignments) - 1:
            # Use the same key for first and last
            input_list.append(f"{key}={value}")
            expected_value = value
        else:
            input_list.append(f"{name}={value}")
    
    result = parse_vars(input_list)
    
    # The last assignment for the key should win
    assert result[key] == expected_value


@given(st.lists(
    st.one_of(
        st.tuples(st.just(True), var_name, var_value),  # Valid
        st.tuples(st.just(False), st.text(min_size=1).filter(lambda x: '=' not in x))  # Invalid
    ),
    min_size=1,
    max_size=10
))
def test_parse_vars_mixed_valid_invalid(items):
    """Test that parse_vars fails fast on first invalid item."""
    input_list = []
    has_invalid = False
    
    for item in items:
        if item[0]:  # Valid
            input_list.append(f"{item[1]}={item[2]}")
        else:  # Invalid
            input_list.append(item[1])
            has_invalid = True
            break  # Stop at first invalid
    
    if has_invalid:
        with pytest.raises(ValueError):
            parse_vars(input_list)
    else:
        result = parse_vars(input_list)
        assert isinstance(result, dict)