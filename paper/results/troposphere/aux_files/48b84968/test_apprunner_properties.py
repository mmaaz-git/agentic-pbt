#!/usr/bin/env python3
"""Property-based tests for troposphere.apprunner module"""

import sys
import json
from hypothesis import given, strategies as st, assume, settings
import pytest

# Add the troposphere env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.apprunner as apprunner
from troposphere import validators


# Test 1: Title validation property - titles must be alphanumeric
@given(st.text())
def test_title_validation_property(title):
    """Test that resource titles only accept alphanumeric characters"""
    # The regex in the code is: ^[a-zA-Z0-9]+$
    # So empty strings and non-alphanumeric should fail
    
    try:
        resource = apprunner.Service(title)
        # If it succeeded, title should be alphanumeric and non-empty
        assert title.isalnum() and len(title) > 0
    except ValueError as e:
        # If it failed, title should be non-alphanumeric or empty
        assert not (title.isalnum() and len(title) > 0)
        assert 'not alphanumeric' in str(e)


# Test 2: Required property validation
@given(st.text(min_size=1).filter(str.isalnum))
def test_required_property_validation(title):
    """Test that required properties are enforced during validation"""
    # Service has SourceConfiguration as required
    service = apprunner.Service(title)
    
    # Should raise error when validating without required property
    with pytest.raises(ValueError, match="Resource SourceConfiguration required"):
        service.to_dict()


# Test 3: Boolean validator property
@given(st.one_of(
    st.sampled_from([True, False, 1, 0, "true", "false", "True", "False", "1", "0"]),
    st.text(), st.integers(), st.floats()
))
def test_boolean_validator(value):
    """Test the boolean validator accepts correct values and rejects others"""
    valid_true = [True, 1, "1", "true", "True"]
    valid_false = [False, 0, "0", "false", "False"]
    
    if value in valid_true:
        assert validators.boolean(value) is True
    elif value in valid_false:
        assert validators.boolean(value) is False
    else:
        with pytest.raises(ValueError):
            validators.boolean(value)


# Test 4: Integer validator property
@given(st.one_of(
    st.integers(),
    st.text(),
    st.floats(),
    st.none(),
    st.lists(st.integers())
))
def test_integer_validator(value):
    """Test the integer validator accepts valid integers and rejects invalid ones"""
    try:
        result = validators.integer(value)
        # If it succeeded, value should be convertible to int
        int(value)
        assert result == value
    except (ValueError, TypeError):
        # If it failed, value should not be convertible to int
        with pytest.raises(ValueError, match="is not a valid integer"):
            validators.integer(value)


# Test 5: Round-trip property for simple resources
@given(
    title=st.text(min_size=1).filter(str.isalnum),
    name=st.text(min_size=1).filter(str.isalnum),
    max_concurrency=st.integers(min_value=1, max_value=200),
    max_size=st.integers(min_value=1, max_value=100),
    min_size=st.integers(min_value=1, max_value=100)
)
def test_autoscaling_roundtrip(title, name, max_concurrency, max_size, min_size):
    """Test that to_dict and from_dict are inverse operations"""
    # Ensure min_size <= max_size (reasonable constraint)
    assume(min_size <= max_size)
    
    # Create an AutoScalingConfiguration
    config = apprunner.AutoScalingConfiguration(
        title,
        AutoScalingConfigurationName=name,
        MaxConcurrency=max_concurrency,
        MaxSize=max_size,
        MinSize=min_size
    )
    
    # Convert to dict
    config_dict = config.to_dict()
    
    # Create from dict
    config2 = apprunner.AutoScalingConfiguration.from_dict(
        title, 
        config_dict['Properties']
    )
    
    # They should be equal
    assert config.to_dict() == config2.to_dict()
    assert config.title == config2.title


# Test 6: Property type enforcement for nested properties
@given(
    title=st.text(min_size=1).filter(str.isalnum),
    vendor=st.one_of(st.text(), st.integers(), st.none(), st.lists(st.text()))
)
def test_trace_configuration_type_enforcement(title, vendor):
    """Test that TraceConfiguration enforces string type for Vendor"""
    config = apprunner.ObservabilityConfiguration(title)
    
    if isinstance(vendor, str):
        # Should work with strings
        trace = apprunner.TraceConfiguration(Vendor=vendor)
        config.TraceConfiguration = trace
        assert config.TraceConfiguration.Vendor == vendor
    else:
        # Should fail with non-strings in validation
        with pytest.raises((TypeError, AttributeError)):
            trace = apprunner.TraceConfiguration(Vendor=vendor)


# Test 7: Network port validation in HealthCheckConfiguration
@given(
    healthy=st.integers(),
    unhealthy=st.integers(),
    interval=st.integers(),
    timeout=st.integers()
)
def test_health_check_integer_properties(healthy, unhealthy, interval, timeout):
    """Test that HealthCheckConfiguration correctly validates integer properties"""
    health_check = apprunner.HealthCheckConfiguration()
    
    # All these should accept integers
    health_check.HealthyThreshold = healthy
    health_check.UnhealthyThreshold = unhealthy
    health_check.Interval = interval
    health_check.Timeout = timeout
    
    # They should be stored as-is
    assert health_check.HealthyThreshold == healthy
    assert health_check.UnhealthyThreshold == unhealthy
    assert health_check.Interval == interval
    assert health_check.Timeout == timeout


# Test 8: IngressConfiguration boolean property
@given(
    value=st.one_of(
        st.sampled_from([True, False, 1, 0, "true", "false", "True", "False"]),
        st.text(), st.integers().filter(lambda x: x not in [0, 1])
    )
)
def test_ingress_configuration_boolean(value):
    """Test that IngressConfiguration.IsPubliclyAccessible uses boolean validator"""
    valid_values = [True, False, 1, 0, "true", "false", "True", "False"]
    
    if value in valid_values:
        config = apprunner.IngressConfiguration(IsPubliclyAccessible=value)
        # Should be converted to boolean
        assert isinstance(config.IsPubliclyAccessible, bool)
    else:
        with pytest.raises((ValueError, TypeError)):
            apprunner.IngressConfiguration(IsPubliclyAccessible=value)


# Test 9: KeyValuePair list property
@given(
    pairs=st.lists(
        st.fixed_dictionaries({
            'Name': st.text(min_size=1),
            'Value': st.text()
        }),
        max_size=10
    )
)
def test_keyvaluepair_list_property(pairs):
    """Test that RuntimeEnvironmentVariables accepts lists of KeyValuePair"""
    config = apprunner.ImageConfiguration()
    
    # Convert dicts to KeyValuePair objects
    kv_pairs = [apprunner.KeyValuePair(**p) for p in pairs]
    
    config.RuntimeEnvironmentVariables = kv_pairs
    
    # Should be stored correctly
    assert len(config.RuntimeEnvironmentVariables) == len(pairs)
    for i, kv in enumerate(config.RuntimeEnvironmentVariables):
        assert kv.Name == pairs[i]['Name']
        assert kv.Value == pairs[i]['Value']


if __name__ == "__main__":
    # Run with increased examples for better coverage
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))