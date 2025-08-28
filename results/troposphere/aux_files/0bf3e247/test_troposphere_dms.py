"""Property-based tests for troposphere.dms module"""

import sys
import math
from hypothesis import given, strategies as st, assume, settings

# Add the venv site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.dms as dms
from troposphere.validators import network_port, integer, boolean, double
from troposphere.validators.dms import validate_network_port

# Test 1: Network port validator - tests the claimed property from the error message
@given(st.integers())
def test_network_port_validator_range(port):
    """Test that network_port validator accepts ports in the documented range.
    
    The error message at line 131 of validators/__init__.py says:
    'network port %r must been between 0 and 65535'
    But the actual check is: int(i) < -1 or int(i) > 65535
    
    This tests whether the implementation matches the error message.
    """
    if -1 <= port <= 65535:
        # Should succeed for valid ports
        result = network_port(port)
        assert result == port
    else:
        # Should fail for invalid ports
        try:
            network_port(port)
            assert False, f"network_port should have rejected {port}"
        except ValueError as e:
            # Check if error message matches what's claimed
            assert "must been between 0 and 65535" in str(e)


# Test 2: Test DMS-specific validate_network_port wrapper
@given(st.integers())
def test_validate_network_port_matches_base(port):
    """Test that DMS validate_network_port behaves identically to base network_port."""
    # Both should either succeed together or fail together
    base_exception = None
    dms_exception = None
    
    try:
        base_result = network_port(port)
    except Exception as e:
        base_exception = e
    
    try:
        dms_result = validate_network_port(port)
    except Exception as e:
        dms_exception = e
    
    # They should behave identically
    if base_exception is None:
        assert dms_exception is None
        assert base_result == dms_result
    else:
        assert dms_exception is not None
        assert type(base_exception) == type(dms_exception)
        assert str(base_exception) == str(dms_exception)


# Test 3: Boolean validator property - test documented conversions
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]),
    st.integers(),
    st.text()
))
def test_boolean_validator_conversions(value):
    """Test that boolean validator correctly converts documented values."""
    try:
        result = boolean(value)
        # If it succeeds, check it returns the right boolean
        if value in [True, 1, "1", "true", "True"]:
            assert result is True
        elif value in [False, 0, "0", "false", "False"]:
            assert result is False
        else:
            # Should not succeed for other values
            assert False, f"boolean should have rejected {value!r}"
    except ValueError:
        # Should only fail for non-documented values
        assert value not in [True, 1, "1", "true", "True", False, 0, "0", "false", "False"]


# Test 4: Integer validator property
@given(st.one_of(
    st.integers(),
    st.text(),
    st.floats(),
    st.none(),
    st.lists(st.integers())
))
def test_integer_validator(value):
    """Test that integer validator accepts valid integers and rejects invalid ones."""
    try:
        result = integer(value)
        # If it succeeds, verify the value can be converted to int
        int(value)
        assert result == value
    except ValueError as e:
        # Should contain the error message format
        if not (isinstance(value, (list, type(None))) or (isinstance(value, float) and math.isnan(value))):
            assert "is not a valid integer" in str(e)
    except TypeError:
        # Some types may raise TypeError instead
        pass


# Test 5: Double validator property
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text(),
    st.none(),
    st.lists(st.floats())
))
def test_double_validator(value):
    """Test that double validator accepts valid floats and rejects invalid ones."""
    try:
        result = double(value)
        # If it succeeds, verify the value can be converted to float
        float(value)
        assert result == value
    except ValueError as e:
        # Should contain the error message format
        if not isinstance(value, (list, type(None))):
            assert "is not a valid double" in str(e)
    except TypeError:
        # Some types may raise TypeError instead
        pass


# Test 6: MongoDbSettings port validation
@given(st.integers())
def test_mongodb_settings_port_validation(port):
    """Test that MongoDbSettings properly validates port numbers using validate_network_port."""
    settings = dms.MongoDbSettings()
    
    if -1 <= port <= 65535:
        # Should succeed for valid ports
        settings.Port = port
        assert settings.Port == port
    else:
        # Should fail for invalid ports
        try:
            settings.Port = port
            # The validation happens in BaseAWSObject.__setattr__
            # We need to trigger to_dict() to see validation  
            settings.to_dict()
            assert False, f"MongoDbSettings should have rejected port {port}"
        except (ValueError, AttributeError):
            pass  # Expected for invalid ports


# Test 7: Test integer range edge cases
@given(st.sampled_from([-2, -1, 0, 1, 65534, 65535, 65536]))
def test_network_port_edge_cases(port):
    """Test network_port validator at boundary values."""
    if port == -2 or port == 65536:
        # Should reject
        try:
            network_port(port)
            assert False, f"Should reject port {port}"
        except ValueError as e:
            assert "must been between 0 and 65535" in str(e)
    else:
        # Should accept -1, 0, 1, 65534, 65535
        result = network_port(port)
        assert result == port


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])