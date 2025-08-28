import troposphere.emrserverless as emr
from hypothesis import given, strategies as st, assume, settings
import math


# Test integer validator with float inputs - looking for edge cases
@given(f=st.floats(allow_nan=False, allow_infinity=False, min_value=-10**10, max_value=10**10))
def test_integer_validator_with_floats(f):
    """Test integer validator behavior with float inputs"""
    try:
        result = emr.integer(f)
        # If it succeeds, the float should have been exactly representable as int
        assert f == int(f), f"Float {f} was accepted but is not exactly an integer"
        # Result should be the original float
        assert result == f
        assert result is f
    except ValueError as e:
        # Should only fail for non-integer floats
        if f == int(f):
            # This is a bug - integer-valued floats should be accepted
            raise AssertionError(f"integer() rejected integer-valued float {f}") from e


# Test integer validator with float strings
@given(f=st.floats(allow_nan=False, allow_infinity=False, min_value=-1000, max_value=1000))
def test_integer_validator_with_float_strings(f):
    """Test integer validator with string representations of floats"""
    float_str = str(f)
    try:
        result = emr.integer(float_str)
        # If it succeeds, should return the original string
        assert result == float_str
        # The string should be convertible to int (which means it was like "1.0" not "1.5")
        int_val = int(float(float_str))
        assert float(float_str) == int_val
    except ValueError:
        # Should fail for non-integer float strings
        try:
            # Check if this is truly not convertible to int
            int_val = int(float(float_str))
            if float(float_str) == int_val:
                # This might be a bug - "1.0" style strings might not be accepted
                pass  # Not necessarily a bug, depends on design intent
        except (ValueError, TypeError):
            pass  # Expected


# Test with very large integers
@given(n=st.integers(min_value=10**15, max_value=10**18))
def test_integer_validator_large_numbers(n):
    """Test integer validator with very large numbers"""
    result = emr.integer(n)
    assert result is n
    
    # Test with string representation
    str_n = str(n)
    str_result = emr.integer(str_n)
    assert str_result == str_n
    assert int(str_result) == n


# Test ConfigurationObject with nested configurations
@given(
    depth=st.integers(min_value=0, max_value=3),
    props=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.text(min_size=1, max_size=10),
        max_size=3
    )
)
def test_nested_configuration_objects(depth, props):
    """Test ConfigurationObject with nested configurations"""
    def create_config(d):
        config = emr.ConfigurationObject(Classification=f"level_{d}")
        if props:
            config.Properties = props
        if d > 0:
            # Create nested configuration
            nested = create_config(d - 1)
            config.Configurations = [nested]
        return config
    
    original = create_config(depth)
    dict_repr = original.to_dict()
    
    # Check structure
    assert 'Classification' in dict_repr
    assert dict_repr['Classification'] == f"level_{depth}"
    
    if props:
        assert 'Properties' in dict_repr
        assert dict_repr['Properties'] == props
    
    # Try round-trip
    reconstructed = emr.ConfigurationObject.from_dict('test', dict_repr)
    final_dict = reconstructed.to_dict()
    assert dict_repr == final_dict


# Test boolean with numeric strings that look boolean-ish
@given(s=st.text(min_size=1, max_size=10))
def test_boolean_with_arbitrary_strings(s):
    """Test boolean validator with arbitrary strings"""
    try:
        result = emr.boolean(s)
        # Should only succeed for specific strings
        assert s in ["1", "0", "true", "false", "True", "False"]
        assert isinstance(result, bool)
        if s in ["1", "true", "True"]:
            assert result is True
        else:
            assert result is False
    except ValueError:
        # Should fail for non-boolean strings
        assert s not in ["1", "0", "true", "false", "True", "False"]


# Test InitialCapacityConfig
@given(
    worker_count=st.integers(min_value=1, max_value=1000),
    worker_config=st.builds(
        emr.WorkerConfiguration,
        Cpu=st.text(min_size=1, max_size=10),
        Disk=st.text(min_size=1, max_size=10),
        Memory=st.text(min_size=1, max_size=10)
    )
)
def test_initial_capacity_config(worker_count, worker_config):
    """Test InitialCapacityConfig creation and serialization"""
    config = emr.InitialCapacityConfig(
        WorkerCount=worker_count,
        WorkerConfiguration=worker_config
    )
    
    dict_repr = config.to_dict()
    assert dict_repr['WorkerCount'] == worker_count
    assert 'WorkerConfiguration' in dict_repr
    
    # Round-trip
    reconstructed = emr.InitialCapacityConfig.from_dict('test', dict_repr)
    final_dict = reconstructed.to_dict()
    assert dict_repr == final_dict


# Test special float values with integer validator
def test_integer_validator_special_floats():
    """Test integer validator with special float values"""
    # Test with exact integer floats
    for val in [1.0, 2.0, -3.0, 0.0, 100.0]:
        result = emr.integer(val)
        assert result is val
    
    # Test with non-integer floats - should raise ValueError
    for val in [1.5, 2.3, -3.7, 0.1]:
        try:
            emr.integer(val)
            assert False, f"integer() should reject non-integer float {val}"
        except ValueError:
            pass  # Expected


# Test empty string edge case
def test_validators_empty_string():
    """Test validators with empty string"""
    # Boolean with empty string
    try:
        result = emr.boolean("")
        assert False, "boolean('') should raise ValueError"
    except ValueError:
        pass  # Expected
    
    # Integer with empty string
    try:
        result = emr.integer("")
        assert False, "integer('') should raise ValueError"
    except ValueError:
        pass  # Expected


# Test with None values
def test_validators_with_none():
    """Test validators with None input"""
    # Boolean with None
    try:
        result = emr.boolean(None)
        assert False, "boolean(None) should raise ValueError"
    except ValueError:
        pass  # Expected
    
    # Integer with None
    try:
        result = emr.integer(None)
        assert False, "integer(None) should raise ValueError"
    except ValueError:
        pass  # Expected