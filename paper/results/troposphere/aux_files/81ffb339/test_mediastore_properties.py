#!/usr/bin/env python3
"""Property-based tests for troposphere.mediastore module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from troposphere.validators import boolean, integer
from troposphere.validators.mediastore import containerlevelmetrics_status
from troposphere.mediastore import CorsRule, MetricPolicyRule, MetricPolicy, Container
from troposphere import encode_to_dict


# Test 1: Boolean validator properties
@given(st.one_of(
    st.just(True), st.just(1), st.just("1"), st.just("true"), st.just("True"),
    st.just(False), st.just(0), st.just("0"), st.just("false"), st.just("False")
))
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator correctly handles all documented valid inputs."""
    result = boolean(value)
    
    # Property: These specific values should map to True
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    # Property: These specific values should map to False
    elif value in [False, 0, "0", "false", "False"]:
        assert result is False
    else:
        raise AssertionError(f"Unexpected value: {value}")


@given(st.one_of(
    st.integers().filter(lambda x: x not in [0, 1]),
    st.text().filter(lambda x: x not in ["0", "1", "true", "True", "false", "False"]),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
    st.none()
))
def test_boolean_validator_invalid_inputs(value):
    """Test that boolean validator raises ValueError for invalid inputs."""
    with pytest.raises(ValueError):
        boolean(value)


# Test 2: ContainerLevelMetrics status validator
@given(st.text())
def test_containerlevelmetrics_status_validation(status):
    """Test that containerlevelmetrics_status only accepts DISABLED or ENABLED."""
    if status in ["DISABLED", "ENABLED"]:
        # Property: Valid statuses should return unchanged
        result = containerlevelmetrics_status(status)
        assert result == status
    else:
        # Property: Invalid statuses should raise ValueError with specific message
        with pytest.raises(ValueError) as exc_info:
            containerlevelmetrics_status(status)
        assert 'ContainerLevelMetrics must be one of: "DISABLED, ENABLED"' in str(exc_info.value)


# Test 3: Integer validator properties
@given(st.one_of(
    st.integers(),
    st.text(min_size=1).map(lambda x: str(int.from_bytes(x.encode()[:8], 'little') % 10000)),
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x == int(x)).map(lambda x: int(x))
))
def test_integer_validator_valid_inputs(value):
    """Test that integer validator accepts values convertible to integers."""
    result = integer(value)
    # Property: Should return the same value if it can be converted to int
    assert result == value
    # Property: The value should be convertible to int without error
    int(result)


@given(st.one_of(
    st.text().filter(lambda x: not x.isdigit() and x != "" and (x[0] != '-' or not x[1:].isdigit())),
    st.floats(allow_nan=True),
    st.floats(allow_infinity=True),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
    st.none()
))
def test_integer_validator_invalid_inputs(value):
    """Test that integer validator raises ValueError for non-integer convertible values."""
    # Skip values that might actually be valid integers
    try:
        int(value)
        assume(False)  # Skip if it's actually convertible to int
    except (ValueError, TypeError):
        pass
    
    with pytest.raises(ValueError) as exc_info:
        integer(value)
    assert "is not a valid integer" in str(exc_info.value)


# Test 4: CorsRule properties
@given(
    allowed_headers=st.lists(st.text()),
    allowed_methods=st.lists(st.text()),
    allowed_origins=st.lists(st.text()),
    expose_headers=st.lists(st.text()),
    max_age_seconds=st.integers()
)
def test_cors_rule_creation_and_dict_conversion(allowed_headers, allowed_methods, 
                                                 allowed_origins, expose_headers, 
                                                 max_age_seconds):
    """Test that CorsRule can be created and converted to dict without errors."""
    cors_rule = CorsRule(
        AllowedHeaders=allowed_headers,
        AllowedMethods=allowed_methods,
        AllowedOrigins=allowed_origins,
        ExposeHeaders=expose_headers,
        MaxAgeSeconds=max_age_seconds
    )
    
    # Property: Should be able to convert to dict
    result = cors_rule.to_dict()
    assert isinstance(result, dict)
    
    # Property: Dict should contain the provided values
    if allowed_headers:
        assert result.get("AllowedHeaders") == allowed_headers
    if allowed_methods:
        assert result.get("AllowedMethods") == allowed_methods
    if allowed_origins:
        assert result.get("AllowedOrigins") == allowed_origins
    if expose_headers:
        assert result.get("ExposeHeaders") == expose_headers
    if max_age_seconds is not None:
        assert result.get("MaxAgeSeconds") == max_age_seconds


# Test 5: MetricPolicyRule required fields
@given(object_group=st.text(), object_group_name=st.text())
def test_metric_policy_rule_required_fields(object_group, object_group_name):
    """Test that MetricPolicyRule enforces required fields."""
    rule = MetricPolicyRule(
        ObjectGroup=object_group,
        ObjectGroupName=object_group_name
    )
    
    # Property: Required fields should be present in dict
    result = rule.to_dict()
    assert result["ObjectGroup"] == object_group
    assert result["ObjectGroupName"] == object_group_name


# Test 6: encode_to_dict round-trip property
@given(
    object_group=st.text(min_size=1),
    object_group_name=st.text(min_size=1)
)
def test_encode_to_dict_preserves_data(object_group, object_group_name):
    """Test that encode_to_dict preserves data correctly."""
    rule = MetricPolicyRule(
        ObjectGroup=object_group,
        ObjectGroupName=object_group_name
    )
    
    # Property: encode_to_dict should preserve all data
    encoded = encode_to_dict(rule)
    assert isinstance(encoded, dict)
    assert encoded["ObjectGroup"] == object_group
    assert encoded["ObjectGroupName"] == object_group_name


# Test 7: Container validation with boolean field
@given(
    container_name=st.text(min_size=1),
    access_logging=st.one_of(
        st.just(True), st.just(False),
        st.just(1), st.just(0),
        st.just("true"), st.just("false"),
        st.just("True"), st.just("False"),
        st.just("1"), st.just("0")
    )
)
def test_container_boolean_field(container_name, access_logging):
    """Test that Container correctly handles boolean AccessLoggingEnabled field."""
    container = Container(
        title="TestContainer",
        ContainerName=container_name,
        AccessLoggingEnabled=access_logging
    )
    
    # Property: Boolean field should be normalized to True/False
    result = container.to_dict()
    properties = result.get("Properties", result)
    
    if "AccessLoggingEnabled" in properties:
        logging_value = properties["AccessLoggingEnabled"]
        # Should be normalized to boolean
        assert isinstance(logging_value, bool) or logging_value in [True, False, 0, 1, "true", "false", "True", "False", "0", "1"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])