import troposphere.emrserverless as emr
from hypothesis import given, strategies as st, assume
import hypothesis.strategies as st
import math


# Test 1: Round-trip property for AWSProperty classes
@given(
    enabled=st.booleans(),
    idle_timeout=st.integers(min_value=1, max_value=10000)
)
def test_autostop_configuration_round_trip(enabled, idle_timeout):
    """Test that AutoStopConfiguration survives to_dict/from_dict round-trip"""
    original = emr.AutoStopConfiguration(
        Enabled=enabled,
        IdleTimeoutMinutes=idle_timeout
    )
    
    dict_repr = original.to_dict()
    reconstructed = emr.AutoStopConfiguration.from_dict('test', dict_repr)
    final_dict = reconstructed.to_dict()
    
    assert dict_repr == final_dict
    assert dict_repr['Enabled'] == enabled
    assert dict_repr['IdleTimeoutMinutes'] == idle_timeout


# Test 2: Boolean validator edge cases
@given(x=st.one_of(
    st.booleans(),
    st.integers(min_value=-10, max_value=10),
    st.text(min_size=0, max_size=20),
    st.floats(allow_nan=False, allow_infinity=False),
    st.none()
))
def test_boolean_validator(x):
    """Test the boolean validator function with various inputs"""
    try:
        result = emr.boolean(x)
        # If it succeeds, result should be a boolean
        assert isinstance(result, bool)
        
        # Check that known true values return True
        if x in [True, 1, "1", "true", "True"]:
            assert result is True
        # Check that known false values return False  
        elif x in [False, 0, "0", "false", "False"]:
            assert result is False
            
    except ValueError:
        # Should only raise ValueError for invalid inputs
        assert x not in [True, False, 1, 0, "1", "0", "true", "True", "false", "False"]


# Test 3: Integer validator type preservation
@given(x=st.one_of(
    st.integers(),
    st.text(min_size=1).filter(lambda s: s.strip().lstrip('-').isdigit()),
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda f: f == int(f))
))
def test_integer_validator_preserves_input(x):
    """Test that integer validator returns the original value unchanged"""
    try:
        result = emr.integer(x)
        # The function should return the exact same object
        assert result is x
        # And it should be convertible to int without error
        int(result)
    except ValueError:
        # Should only fail if x cannot be converted to int
        try:
            int(x)
            # If int(x) works, the validator should not have raised
            assert False, f"integer() raised ValueError for valid input {x}"
        except (ValueError, TypeError):
            # Expected - x cannot be converted to int
            pass


# Test 4: AutoStartConfiguration round-trip
@given(enabled=st.booleans())
def test_autostart_configuration_round_trip(enabled):
    """Test AutoStartConfiguration to_dict/from_dict round-trip"""
    original = emr.AutoStartConfiguration(Enabled=enabled)
    dict_repr = original.to_dict()
    reconstructed = emr.AutoStartConfiguration.from_dict('test', dict_repr)
    final_dict = reconstructed.to_dict()
    
    assert dict_repr == final_dict
    assert dict_repr['Enabled'] == enabled


# Test 5: ConfigurationObject round-trip with various property combinations
@given(
    classification=st.text(min_size=1, max_size=100),
    configurations=st.none(),  # Can be list of ConfigurationObject
    properties=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=0, max_size=200),
        max_size=10
    )
)
def test_configuration_object_round_trip(classification, configurations, properties):
    """Test ConfigurationObject serialization round-trip"""
    kwargs = {'Classification': classification}
    if properties:
        kwargs['Properties'] = properties
        
    original = emr.ConfigurationObject(**kwargs)
    dict_repr = original.to_dict()
    reconstructed = emr.ConfigurationObject.from_dict('test', dict_repr)
    final_dict = reconstructed.to_dict()
    
    assert dict_repr == final_dict
    assert dict_repr.get('Classification') == classification
    if properties:
        assert dict_repr.get('Properties') == properties


# Test 6: MaximumAllowedResources validation
@given(
    cpu=st.text(min_size=1, max_size=20),
    disk=st.text(min_size=1, max_size=20),
    memory=st.text(min_size=1, max_size=20)
)
def test_maximum_allowed_resources(cpu, disk, memory):
    """Test MaximumAllowedResources creation and serialization"""
    resource = emr.MaximumAllowedResources(
        Cpu=cpu,
        Disk=disk,
        Memory=memory
    )
    
    dict_repr = resource.to_dict()
    assert dict_repr['Cpu'] == cpu
    assert dict_repr['Disk'] == disk
    assert dict_repr['Memory'] == memory
    
    # Round-trip test
    reconstructed = emr.MaximumAllowedResources.from_dict('test', dict_repr)
    final_dict = reconstructed.to_dict()
    assert dict_repr == final_dict


# Test 7: Integer validator with string numbers
@given(n=st.integers(min_value=-10**10, max_value=10**10))
def test_integer_validator_string_numbers(n):
    """Test integer validator with string representations of numbers"""
    string_n = str(n)
    result = emr.integer(string_n)
    # Should return the original string unchanged
    assert result == string_n
    assert isinstance(result, str)
    # But should be convertible to the same integer
    assert int(result) == n


# Test 8: Boolean validator idempotence
@given(x=st.one_of(
    st.just(True), st.just(False),
    st.just(1), st.just(0),
    st.just("true"), st.just("false"),
    st.just("True"), st.just("False"),
    st.just("1"), st.just("0")
))
def test_boolean_validator_idempotent(x):
    """Test that boolean validator is idempotent for valid inputs"""
    result1 = emr.boolean(x)
    # Applying boolean to a boolean result should be idempotent
    result2 = emr.boolean(result1)
    assert result1 == result2
    assert isinstance(result1, bool)
    assert isinstance(result2, bool)