"""
Property-based tests for troposphere.vpclattice module
Testing validation functions and class behaviors
"""

import json
from hypothesis import given, strategies as st, assume, settings
import troposphere.vpclattice as vpc
import troposphere


# Test 1: Integer validator should properly validate and convert integers
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.booleans()
))
def test_integer_validator_type_consistency(value):
    """
    The integer validator function should either:
    1. Accept and convert the value to an integer
    2. Reject invalid values with an exception
    
    It should NOT accept strings that look like numbers without converting them.
    """
    int_func = vpc.HealthCheckConfig.props['Port'][0]
    
    try:
        result = int_func(value)
        # If it accepts the value, check what type it returns
        if isinstance(value, str) and value.isdigit():
            # Bug: integer validator accepts string numbers but doesn't convert them
            assert isinstance(result, int), f"integer validator returned {type(result).__name__} for string '{value}', expected int"
        elif isinstance(value, float):
            # Bug: integer validator accepts floats without converting
            assert isinstance(result, int), f"integer validator returned {type(result).__name__} for float {value}, expected int"
    except ValueError:
        # It's okay to raise ValueError for invalid inputs
        pass


# Test 2: Properties with integer validators should store integers
@given(
    port=st.one_of(
        st.integers(min_value=1, max_value=65535),
        st.text(alphabet="0123456789", min_size=1, max_size=5),
        st.floats(min_value=1.0, max_value=65535.0, allow_nan=False)
    ),
    interval=st.one_of(
        st.integers(min_value=5, max_value=300),
        st.text(alphabet="0123456789", min_size=1, max_size=3)
    )
)
def test_healthcheck_integer_properties(port, interval):
    """
    When creating a HealthCheckConfig with integer properties,
    the stored values should be actual integers, not strings or floats.
    """
    try:
        hc = vpc.HealthCheckConfig(
            'test',
            Port=port,
            HealthCheckIntervalSeconds=interval
        )
        
        # Check that properties are stored as integers
        if 'Port' in hc.properties:
            stored_port = hc.properties['Port']
            # If we passed a string number, it should be converted to int
            if isinstance(port, str) and port.isdigit():
                assert isinstance(stored_port, int), f"Port stored as {type(stored_port).__name__}, expected int for input '{port}'"
            # If we passed a float, it should be converted to int
            elif isinstance(port, float):
                assert isinstance(stored_port, int), f"Port stored as {type(stored_port).__name__}, expected int for input {port}"
                
        if 'HealthCheckIntervalSeconds' in hc.properties:
            stored_interval = hc.properties['HealthCheckIntervalSeconds']
            if isinstance(interval, str) and interval.isdigit():
                assert isinstance(stored_interval, int), f"Interval stored as {type(stored_interval).__name__}, expected int for input '{interval}'"
    except (ValueError, TypeError):
        # It's okay if invalid values are rejected
        pass


# Test 3: Required fields should be enforced during to_dict
@given(
    type_value=st.sampled_from(['IP', 'LAMBDA', 'INSTANCE', 'ALB']),
    name=st.text(min_size=1, max_size=20)
)
def test_target_group_required_fields(type_value, name):
    """
    TargetGroup has 'Type' as a required field.
    Creating without it and calling to_dict should raise an error.
    """
    # First test: with required field
    tg_valid = vpc.TargetGroup(
        'TestTG',
        Type=type_value,
        Name=name
    )
    # This should work fine
    dict_result = tg_valid.to_dict()
    assert 'Type' in dict_result['Properties']
    
    # Second test: without required field  
    tg_invalid = vpc.TargetGroup(
        'TestTG2',
        Name=name
        # Missing required Type field
    )
    # to_dict should validate and raise an error for missing required field
    try:
        invalid_dict = tg_invalid.to_dict()
        # If it doesn't raise, check if validation is happening
        assert 'Type' in invalid_dict['Properties'], "Required field 'Type' missing but no error raised"
    except (ValueError, KeyError, AttributeError) as e:
        # Expected - required field validation should fail
        pass


# Test 4: JSON serialization round-trip should preserve types
@given(
    enabled=st.booleans(),
    port=st.integers(min_value=1, max_value=65535),
    interval=st.integers(min_value=5, max_value=300)
)
def test_json_serialization_type_preservation(enabled, port, interval):
    """
    When serializing to JSON and back, integer properties should remain integers,
    not become strings.
    """
    hc = vpc.HealthCheckConfig(
        'test',
        Enabled=enabled,
        Port=port,
        HealthCheckIntervalSeconds=interval
    )
    
    # Convert to dict then to JSON
    hc_dict = hc.to_dict()
    json_str = json.dumps(hc_dict)
    
    # Parse back from JSON
    parsed = json.loads(json_str)
    
    # Check that integer values are still integers
    if 'Port' in parsed.get('Properties', {}):
        assert isinstance(parsed['Properties']['Port'], int), f"Port became {type(parsed['Properties']['Port']).__name__} after JSON round-trip"
    
    if 'HealthCheckIntervalSeconds' in parsed.get('Properties', {}):
        assert isinstance(parsed['Properties']['HealthCheckIntervalSeconds'], int), f"Interval became {type(parsed['Properties']['HealthCheckIntervalSeconds']).__name__} after JSON round-trip"


# Test 5: HeaderMatch required fields validation
@given(
    name=st.text(min_size=1, max_size=50),
    case_sensitive=st.booleans()
)
def test_header_match_required_fields(name, case_sensitive):
    """
    HeaderMatch has 'Match' and 'Name' as required fields.
    Creating without them should fail validation.
    """
    # Valid HeaderMatchType
    match_type = vpc.HeaderMatchType(
        Exact='test-value'
    )
    
    # Test with all required fields - should work
    try:
        hm_valid = vpc.HeaderMatch(
            'TestMatch',
            Name=name,
            Match=match_type,
            CaseSensitive=case_sensitive
        )
        dict_result = hm_valid.to_dict()
        assert 'Name' in dict_result['Properties']
        assert 'Match' in dict_result['Properties']
    except Exception as e:
        # Should not fail with valid inputs
        assert False, f"Valid HeaderMatch creation failed: {e}"
    
    # Test without required Match field - should fail
    try:
        hm_invalid = vpc.HeaderMatch(
            'TestMatch2',
            Name=name,
            CaseSensitive=case_sensitive
            # Missing required Match field
        )
        invalid_dict = hm_invalid.to_dict()
        # If no exception, validation is not working properly
        assert False, "HeaderMatch without required 'Match' field did not raise error"
    except (ValueError, TypeError, AttributeError):
        # Expected - validation should fail
        pass