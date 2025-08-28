"""
Property-based tests for troposphere.elasticloadbalancing validators
"""

import re
from hypothesis import assume, given, strategies as st, settings
import troposphere.elasticloadbalancing as elb
from troposphere.validators import integer_range, elb_name, network_port


# Test 1: validate_int_to_str round-trip property
@given(st.integers())
def test_validate_int_to_str_from_int(x):
    """Test that integers are converted to strings correctly"""
    result = elb.validate_int_to_str(x)
    assert isinstance(result, str)
    assert result == str(x)
    # Round-trip: converting the result back should give the same string
    result2 = elb.validate_int_to_str(result)
    assert result2 == result


@given(st.text())
def test_validate_int_to_str_from_str(s):
    """Test that string inputs behave correctly"""
    try:
        # If the string represents a valid integer
        int_val = int(s)
        result = elb.validate_int_to_str(s)
        assert isinstance(result, str)
        assert result == str(int_val)
        # Round-trip should be idempotent
        result2 = elb.validate_int_to_str(result)
        assert result2 == result
    except ValueError:
        # String doesn't represent an integer - should raise TypeError
        try:
            elb.validate_int_to_str(s)
            assert False, f"Should have raised TypeError for non-integer string: {repr(s)}"
        except TypeError as e:
            assert "must be either int or str" in str(e)


@given(st.one_of(st.floats(), st.lists(st.integers()), st.dictionaries(st.text(), st.integers())))
def test_validate_int_to_str_invalid_types(x):
    """Test that non-int, non-str types raise TypeError"""
    try:
        elb.validate_int_to_str(x)
        assert False, f"Should have raised TypeError for type {type(x)}"
    except TypeError as e:
        assert "must be either int or str" in str(e)


# Test 2: validate_threshold range enforcement
@given(st.integers())
def test_validate_threshold_range(x):
    """Test that validate_threshold enforces the 2-10 range"""
    if 2 <= x <= 10:
        result = elb.validate_threshold(x)
        assert result == x
    else:
        try:
            elb.validate_threshold(x)
            assert False, f"Should have raised ValueError for threshold {x}"
        except ValueError as e:
            assert "Integer must be between 2 and 10" in str(e)


@given(st.text())
def test_validate_threshold_string_input(s):
    """Test threshold validation with string inputs"""
    try:
        int_val = int(s)
        if 2 <= int_val <= 10:
            result = elb.validate_threshold(s)
            assert result == s
        else:
            try:
                elb.validate_threshold(s)
                assert False, f"Should have raised ValueError for threshold {s}"
            except ValueError as e:
                assert "Integer must be between 2 and 10" in str(e)
    except ValueError:
        # String doesn't represent an integer
        try:
            elb.validate_threshold(s)
            assert False, f"Should have raised ValueError for non-integer string: {repr(s)}"
        except (ValueError, TypeError):
            pass  # Expected


# Test 3: elb_name regex validation
@given(st.text())
def test_elb_name_validation(name):
    """Test that elb_name validates according to its regex pattern"""
    pattern = r"^[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,30}[a-zA-Z0-9]{1})?$"
    
    if re.match(pattern, name):
        # Should accept valid names
        result = elb_name(name)
        assert result == name
    else:
        # Should reject invalid names
        try:
            elb_name(name)
            assert False, f"Should have rejected invalid ELB name: {repr(name)}"
        except ValueError as e:
            assert "is not a valid elb name" in str(e)


@given(st.from_regex(r"^[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,30}[a-zA-Z0-9]{1})?$"))
def test_elb_name_accepts_valid_patterns(name):
    """Test that valid ELB names are always accepted"""
    result = elb_name(name)
    assert result == name


# Test 4: network_port range validation
@given(st.integers())
def test_network_port_range(port):
    """Test that network_port validates port ranges correctly"""
    if -1 <= port <= 65535:
        result = network_port(port)
        assert result == port
    else:
        try:
            network_port(port)
            assert False, f"Should have raised ValueError for port {port}"
        except ValueError as e:
            assert "must been between 0 and 65535" in str(e)


@given(st.text())
def test_network_port_string_input(s):
    """Test network_port with string inputs"""
    try:
        int_val = int(s)
        if -1 <= int_val <= 65535:
            result = network_port(s)
            assert result == s
        else:
            try:
                network_port(s)
                assert False, f"Should have raised ValueError for port {s}"
            except ValueError as e:
                assert "must been between 0 and 65535" in str(e)
    except ValueError:
        # String doesn't represent an integer
        try:
            network_port(s)
            assert False, f"Should have raised error for non-integer string: {repr(s)}"
        except (ValueError, TypeError):
            pass  # Expected


# Test 5: integer_range factory function
@given(st.integers(), st.integers(), st.integers())
def test_integer_range_validator(min_val, max_val, test_val):
    """Test that integer_range creates correct validators"""
    # Ensure min <= max for valid range
    if min_val > max_val:
        min_val, max_val = max_val, min_val
    
    validator = integer_range(min_val, max_val)
    
    if min_val <= test_val <= max_val:
        result = validator(test_val)
        assert result == test_val
    else:
        try:
            validator(test_val)
            assert False, f"Should have raised ValueError for {test_val} not in [{min_val}, {max_val}]"
        except ValueError as e:
            assert f"Integer must be between {min_val} and {max_val}" in str(e)


# Test edge cases for ELB names
@given(st.text(min_size=33, max_size=100))
def test_elb_name_length_limit(long_name):
    """Test that ELB names have a maximum length"""
    try:
        elb_name(long_name)
        # If it passed, check if it actually matches the pattern
        pattern = r"^[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,30}[a-zA-Z0-9]{1})?$"
        assert re.match(pattern, long_name), f"Accepted invalid long name: {repr(long_name)}"
    except ValueError:
        # Expected for most long names
        pass


# Test boundary values for network ports
@given(st.sampled_from([-2, -1, 0, 65535, 65536]))
def test_network_port_boundaries(port):
    """Test network_port at boundary values"""
    if -1 <= port <= 65535:
        result = network_port(port)
        assert result == port
    else:
        try:
            network_port(port)
            assert False, f"Should have raised ValueError for boundary port {port}"
        except ValueError as e:
            assert "must been between 0 and 65535" in str(e)