"""Property-based tests for troposphere.guardduty module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from troposphere import validators
from troposphere.guardduty import (
    Detector, Filter, IPSet, TagItem, Condition, FindingCriteria,
    CFNFeatureConfiguration, CFNKubernetesAuditLogsConfiguration
)


# Test 1: Title validation property
@given(st.text(min_size=1, max_size=100))
def test_title_validation_property(title):
    """Title must be alphanumeric - matches regex ^[a-zA-Z0-9]+$"""
    try:
        detector = Detector(title, Enable=True)
        # If it succeeded, the title should be alphanumeric
        assert title.isalnum(), f"Non-alphanumeric title {title!r} was accepted but shouldn't be"
    except ValueError as e:
        # If it failed, the title should NOT be alphanumeric
        assert not title.isalnum(), f"Alphanumeric title {title!r} was rejected but shouldn't be"
        assert 'not alphanumeric' in str(e)


# Test 2: Boolean validator property
@given(st.one_of(
    st.booleans(),
    st.integers(),
    st.text(),
    st.none(),
    st.floats(),
    st.lists(st.integers())
))
def test_boolean_validator_property(value):
    """Boolean validator should accept specific truthy/falsy values"""
    truthy_values = [True, 1, "1", "true", "True"]
    falsy_values = [False, 0, "0", "false", "False"]
    
    try:
        result = validators.boolean(value)
        # If it succeeded, value should be in truthy or falsy lists
        if value in truthy_values:
            assert result is True, f"Value {value!r} should return True"
        elif value in falsy_values:
            assert result is False, f"Value {value!r} should return False"
        else:
            # This shouldn't happen - validator should have raised
            assert False, f"Value {value!r} was accepted but shouldn't be"
    except ValueError:
        # If it failed, value should NOT be in truthy or falsy lists
        assert value not in truthy_values + falsy_values, \
            f"Valid boolean value {value!r} was rejected"


# Test 3: Integer validator property
@given(st.one_of(
    st.integers(),
    st.floats(),
    st.text(),
    st.none(),
    st.booleans(),
    st.lists(st.integers())
))
def test_integer_validator_property(value):
    """Integer validator should accept values convertible to int"""
    try:
        result = validators.integer(value)
        # If it succeeded, int(value) should work
        int_value = int(value)
        # Result should be the original value (not converted)
        assert result == value
    except ValueError as e:
        # If validator raised, int() should also fail or be inappropriate
        assert 'not a valid integer' in str(e)
        try:
            int(value)
            # If int() worked but validator failed, that's a bug
            # unless it's a boolean (which int() accepts but validator might not)
            if not isinstance(value, bool):
                assert False, f"Value {value!r} can be int() but validator rejected it"
        except (ValueError, TypeError):
            pass  # Expected - value can't be converted to int


# Test 4: Required field validation
@given(st.booleans())
def test_required_field_validation(include_required):
    """Objects with required fields should enforce them during validation"""
    # Filter has required fields: DetectorId, FindingCriteria, Name
    kwargs = {}
    if include_required:
        kwargs = {
            'DetectorId': 'test-detector',
            'FindingCriteria': FindingCriteria(Criterion={}),
            'Name': 'TestFilter'
        }
    
    filter_obj = Filter('MyFilter', **kwargs)
    
    try:
        # Validation happens in to_dict()
        filter_obj.to_dict()
        # If it succeeded, we should have included required fields
        assert include_required, "Object missing required fields passed validation"
    except ValueError as e:
        # If it failed, we should NOT have included required fields
        assert not include_required, "Object with all required fields failed validation"
        assert 'required in type' in str(e)


# Test 5: Serialization round-trip for simple objects
@given(
    st.text(alphabet=st.characters(whitelist_categories=['L', 'N']), min_size=1, max_size=50),
    st.booleans()
)
def test_detector_serialization_roundtrip(title, enable_value):
    """to_dict and from_dict should be inverses for valid objects"""
    assume(title.isalnum())  # Only valid titles
    
    # Create detector with minimal required fields
    detector1 = Detector(title, Enable=enable_value)
    
    # Convert to dict
    dict_repr = detector1.to_dict()
    
    # The dict should have the expected structure
    assert 'Type' in dict_repr
    assert dict_repr['Type'] == 'AWS::GuardDuty::Detector'
    assert 'Properties' in dict_repr
    assert 'Enable' in dict_repr['Properties']
    
    # Create new detector from dict (using Properties only)
    detector2 = Detector.from_dict(title, dict_repr['Properties'])
    
    # They should be equal
    assert detector1.title == detector2.title
    assert detector1.Enable == detector2.Enable
    assert detector1.to_dict() == detector2.to_dict()


# Test 6: TagItem property validation
@given(st.text(), st.text())
def test_tagitem_key_value_required(key, value):
    """TagItem requires both Key and Value properties"""
    # Try with both properties
    try:
        tag = TagItem(Key=key, Value=value)
        tag_dict = tag.to_dict()
        assert 'Key' in tag_dict
        assert 'Value' in tag_dict
        assert tag_dict['Key'] == key
        assert tag_dict['Value'] == value
    except Exception as e:
        # Should not fail with both properties
        assert False, f"TagItem with both Key and Value failed: {e}"
    
    # Try without Key
    try:
        tag = TagItem(Value=value)
        tag.to_dict()
        assert False, "TagItem without Key should fail validation"
    except ValueError as e:
        assert 'required in type' in str(e)
    
    # Try without Value
    try:
        tag = TagItem(Key=key)
        tag.to_dict()
        assert False, "TagItem without Value should fail validation"
    except ValueError as e:
        assert 'required in type' in str(e)


# Test 7: Type validation for boolean properties
@given(st.one_of(
    st.booleans(),
    st.integers(min_value=0, max_value=1),
    st.sampled_from(['true', 'false', 'True', 'False']),
    st.text(),
    st.floats(),
    st.none()
))
def test_boolean_property_type_validation(value):
    """Boolean properties should accept valid boolean representations"""
    valid_true = [True, 1, 'true', 'True']
    valid_false = [False, 0, 'false', 'False']
    
    try:
        detector = Detector('TestDetector', Enable=value)
        # If it succeeded, value should be valid
        assert value in valid_true + valid_false, \
            f"Invalid boolean value {value!r} was accepted for Enable property"
        # Check it was converted correctly
        if value in valid_true:
            assert detector.Enable is True
        else:
            assert detector.Enable is False
    except (TypeError, ValueError) as e:
        # If it failed, value should be invalid
        assert value not in valid_true + valid_false, \
            f"Valid boolean value {value!r} was rejected for Enable property"


# Test 8: Condition integer properties
@given(st.one_of(
    st.integers(),
    st.floats(),
    st.text(),
    st.none(),
    st.lists(st.integers())
))
def test_condition_integer_properties(value):
    """Condition integer properties should validate integers"""
    integer_props = ['GreaterThan', 'GreaterThanOrEqual', 'Gt', 'Gte', 
                     'LessThan', 'LessThanOrEqual', 'Lt', 'Lte']
    
    for prop in integer_props:
        try:
            condition = Condition(**{prop: value})
            # If it succeeded, value should be convertible to int
            int(value)
        except (TypeError, ValueError):
            # Expected for non-integer values
            pass


if __name__ == '__main__':
    # Run a quick check
    test_title_validation_property()
    test_boolean_validator_property()
    test_integer_validator_property()
    test_required_field_validation()
    print("Quick checks passed!")