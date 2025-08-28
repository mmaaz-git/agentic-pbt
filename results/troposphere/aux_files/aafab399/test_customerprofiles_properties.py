#!/usr/bin/env python3
"""Property-based tests for troposphere.customerprofiles module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere.customerprofiles as cp
from troposphere import validators
import pytest


# Test 1: Integer validator property
@given(st.one_of(
    st.integers(),
    st.text(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.none()
))
def test_integer_validator_consistency(value):
    """Test that integer validator accepts int-convertible values and rejects others."""
    try:
        result = validators.integer(value)
        # If it succeeds, the value should be convertible to int
        int_value = int(value)
        # And the result should be the original value (not converted)
        assert result == value
    except ValueError as e:
        # If it fails, int() should also fail or the value is invalid
        try:
            int(value)
            # If int() succeeds but validator failed, that's a bug
            assert False, f"Validator rejected {value} but int() accepts it"
        except (ValueError, TypeError):
            # Both failed, this is expected
            assert "%r is not a valid integer" % value in str(e)


# Test 2: Double validator property  
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text(),
    st.booleans(),
    st.none()
))
def test_double_validator_consistency(value):
    """Test that double validator accepts float-convertible values and rejects others."""
    try:
        result = validators.double(value)
        # If it succeeds, the value should be convertible to float
        float_value = float(value)
        # And the result should be the original value (not converted)
        assert result == value
    except ValueError as e:
        # If it fails, float() should also fail
        try:
            float(value)
            # If float() succeeds but validator failed, that's a bug
            assert False, f"Validator rejected {value} but float() accepts it"
        except (ValueError, TypeError):
            # Both failed, this is expected
            assert "%r is not a valid double" % value in str(e)


# Test 3: Boolean validator mapping property
@settings(max_examples=1000)
@given(st.one_of(
    st.booleans(),
    st.integers(min_value=-100, max_value=100),
    st.text(max_size=20),
    st.none()
))
def test_boolean_validator_mapping(value):
    """Test that boolean validator correctly maps specific values."""
    expected_true = [True, 1, "1", "true", "True"]
    expected_false = [False, 0, "0", "false", "False"]
    
    try:
        result = validators.boolean(value)
        if value in expected_true:
            assert result is True
        elif value in expected_false:
            assert result is False
        else:
            # Should not reach here if validator worked correctly
            assert False, f"Validator accepted {value} but it's not in known mappings"
    except ValueError:
        # Should only raise for values not in the mappings
        assert value not in expected_true and value not in expected_false


# Test 4: Required fields validation in to_dict()
@given(
    st.booleans(),
    st.text(min_size=1, max_size=10).filter(lambda x: x.isalnum()),
    st.integers()
)
def test_required_fields_validation(include_name, name_value, other_value):
    """Test that required fields are validated when to_dict() is called."""
    # AttributeItem has Name as required field
    if include_name:
        item = cp.AttributeItem(Name=name_value)
        # Should succeed
        result = item.to_dict()
        assert result == {'Name': name_value}
    else:
        item = cp.AttributeItem()
        # Should fail on to_dict() because Name is required
        with pytest.raises(ValueError) as exc_info:
            item.to_dict()
        assert "Resource Name required in type" in str(exc_info.value)


# Test 5: ValueRange with integer validation
@given(
    st.one_of(st.integers(), st.text()),
    st.one_of(st.integers(), st.text())
)
def test_valuerange_integer_validation(start, end):
    """Test that ValueRange properly validates integer fields."""
    try:
        # Try to create ValueRange
        vr = cp.ValueRange(Start=start, End=end)
        # If creation succeeds, both should be int-convertible
        int(start)
        int(end)
        # And to_dict should work
        result = vr.to_dict()
        assert 'Start' in result
        assert 'End' in result
    except ValueError as e:
        # At least one should not be int-convertible
        failed_int_conversion = False
        try:
            int(start)
            int(end)
        except (ValueError, TypeError):
            failed_int_conversion = True
        assert failed_int_conversion, f"ValueRange rejected valid integers: {start}, {end}"


# Test 6: Multiple properties can be set before validation
@given(
    st.lists(st.tuples(
        st.sampled_from(['Start', 'End']),
        st.one_of(st.integers(), st.text(), st.none())
    ), min_size=1, max_size=4)
)
def test_deferred_validation(assignments):
    """Test that validation is deferred until to_dict() is called."""
    vr = cp.ValueRange()
    
    # Set properties one by one - should not validate yet
    for prop_name, value in assignments:
        try:
            setattr(vr, prop_name, value)
            # Setting should work for any value initially
        except ValueError as e:
            # Only validator functions should raise during setting
            if "not a valid integer" in str(e):
                # This is expected for non-integer values
                try:
                    int(value)
                    assert False, f"Validator rejected valid integer {value}"
                except (ValueError, TypeError):
                    pass  # Expected
            else:
                raise  # Unexpected error
    
    # Now try to_dict() which should validate everything
    try:
        result = vr.to_dict()
        # Should only succeed if all required fields are present and valid
        assert 'Start' in result
        assert 'End' in result
    except ValueError as e:
        # Should fail if required fields missing or invalid types
        pass


# Test 7: SourceConnectorProperties allows multiple sources
@given(
    st.booleans(),
    st.booleans(), 
    st.booleans()
)
def test_source_connector_multiple_sources(has_s3, has_salesforce, has_zendesk):
    """Test that SourceConnectorProperties allows multiple connector types."""
    props = cp.SourceConnectorProperties()
    
    if has_s3:
        props.S3 = cp.S3SourceProperties(BucketName="test-bucket")
    if has_salesforce:
        props.Salesforce = cp.SalesforceSourceProperties(Object="Account")
    if has_zendesk:
        props.Zendesk = cp.ZendeskSourceProperties(Object="tickets")
    
    # Should always succeed - no validation against multiple sources
    result = props.to_dict()
    
    # Verify all set sources are in result
    if has_s3:
        assert 'S3' in result
        assert result['S3']['BucketName'] == 'test-bucket'
    if has_salesforce:
        assert 'Salesforce' in result
        assert result['Salesforce']['Object'] == 'Account'
    if has_zendesk:
        assert 'Zendesk' in result
        assert result['Zendesk']['Object'] == 'tickets'


# Test 8: Complex nested validation
@given(
    st.integers(min_value=-1000, max_value=1000),
    st.integers(min_value=-1000, max_value=1000),
    st.text(min_size=1, max_size=10),
    st.text(min_size=1, max_size=10)
)
def test_conditions_with_range_validation(start, end, timestamp_format, unit):
    """Test that nested objects validate properly."""
    # Create a Conditions object with a Range containing ValueRange
    try:
        value_range = cp.ValueRange(Start=start, End=end)
        range_obj = cp.Range(
            Unit=unit,
            ValueRange=value_range,
            TimestampFormat=timestamp_format
        )
        conditions = cp.Conditions(Range=range_obj)
        
        # Should succeed and serialize properly
        result = conditions.to_dict()
        assert result['Range']['Unit'] == unit
        assert result['Range']['ValueRange']['Start'] == start
        assert result['Range']['ValueRange']['End'] == end
        if timestamp_format:
            assert result['Range']['TimestampFormat'] == timestamp_format
    except ValueError as e:
        # Should only fail if required fields are missing
        assert "required in type" in str(e)


if __name__ == "__main__":
    # Run with pytest for better output
    pytest.main([__file__, "-v"])