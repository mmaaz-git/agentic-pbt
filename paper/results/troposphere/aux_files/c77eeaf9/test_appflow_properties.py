#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import pytest
from hypothesis import given, strategies as st, assume, settings
from troposphere import appflow, validators
from troposphere import AWSProperty, AWSObject
import inspect


# Test 1: Boolean validator property
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]),
    st.text(),
    st.integers(),
    st.floats(),
    st.none(),
    st.lists(st.integers())
))
def test_boolean_validator_property(value):
    """Test that boolean validator accepts documented values and rejects others"""
    true_values = [True, 1, "1", "true", "True"]
    false_values = [False, 0, "0", "false", "False"]
    
    if value in true_values:
        result = validators.boolean(value)
        assert result is True, f"boolean({value!r}) should return True"
    elif value in false_values:
        result = validators.boolean(value)
        assert result is False, f"boolean({value!r}) should return False"
    else:
        with pytest.raises(ValueError):
            validators.boolean(value)


# Test 2: Integer validator property
@given(st.one_of(
    st.integers(),
    st.text(),
    st.floats(),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_integer_validator_property(value):
    """Test that integer validator accepts valid integers and rejects invalid ones"""
    try:
        result = validators.integer(value)
        # If it succeeds, the value should be convertible to int
        int_value = int(value)
        assert int(result) == int_value
    except (ValueError, TypeError):
        # If int() fails, validators.integer should also fail
        with pytest.raises(ValueError):
            validators.integer(value)


# Test 3: Double validator property
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text(),
    st.none(),
    st.lists(st.floats()),
    st.dictionaries(st.text(), st.floats())
))
def test_double_validator_property(value):
    """Test that double validator accepts valid floats and rejects invalid ones"""
    try:
        result = validators.double(value)
        # If it succeeds, the value should be convertible to float
        float_value = float(value)
        assert float(result) == float_value
    except (ValueError, TypeError):
        # If float() fails, validators.double should also fail
        with pytest.raises(ValueError):
            validators.double(value)


# Test 4: Required field validation property
@given(
    st.booleans(),
    st.text(min_size=1, max_size=10).filter(lambda x: x.isalnum()),
    st.one_of(st.text(), st.integers(), st.booleans())
)
def test_required_field_validation(required, field_name, field_value):
    """Test that required fields are properly validated"""
    
    # Create a custom AWSProperty class with one field
    class TestProperty(AWSProperty):
        props = {
            field_name: (str, required)
        }
    
    # If field is required, validation should fail without it
    if required:
        prop = TestProperty()
        with pytest.raises(ValueError, match=f"Resource {field_name} required"):
            prop.to_dict(validation=True)
    
    # With the field set, validation should succeed
    prop = TestProperty()
    prop.__setattr__(field_name, str(field_value))
    result = prop.to_dict(validation=True)
    assert field_name in result


# Test 5: Type validation property for appflow classes
@given(
    st.sampled_from([
        appflow.AmplitudeConnectorProfileCredentials,
        appflow.BasicAuthCredentials,
        appflow.ApiKeyCredentials,
        appflow.OAuth2Credentials,
    ]),
    st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.one_of(st.text(), st.integers(), st.booleans(), st.none())
    )
)
def test_type_validation_property(cls, properties):
    """Test that type validation works correctly for appflow classes"""
    
    # Get the actual props definition from the class
    actual_props = cls.props
    
    for prop_name, prop_value in properties.items():
        if prop_name in actual_props:
            expected_type, required = actual_props[prop_name]
            
            obj = cls()
            
            # Test setting the property
            if expected_type == str:
                if isinstance(prop_value, str):
                    obj.__setattr__(prop_name, prop_value)
                    assert getattr(obj, prop_name) == prop_value
                else:
                    with pytest.raises(TypeError):
                        obj.__setattr__(prop_name, prop_value)
            elif expected_type == validators.boolean:
                if prop_value in [True, 1, "1", "true", "True", False, 0, "0", "false", "False"]:
                    obj.__setattr__(prop_name, prop_value)
                    assert getattr(obj, prop_name) in [True, False]
                else:
                    with pytest.raises((TypeError, ValueError)):
                        obj.__setattr__(prop_name, prop_value)


# Test 6: Properties not in props should raise AttributeError
@given(
    st.sampled_from([
        appflow.Connector,
        appflow.ConnectorProfile,
        appflow.Flow,
    ]),
    st.text(min_size=1, max_size=20).filter(lambda x: x.isalnum() and not x.startswith('_')),
    st.one_of(st.text(), st.integers(), st.booleans())
)
def test_invalid_property_rejection(cls, prop_name, prop_value):
    """Test that setting properties not defined in props raises AttributeError"""
    
    # Skip if the property is actually defined or is a special attribute
    if prop_name in cls.props or prop_name in ['title', 'template', 'do_validation']:
        return
    
    # For AWSObject subclasses, we need a title
    if issubclass(cls, AWSObject):
        obj = cls(title="TestObject")
    else:
        obj = cls()
    
    # Setting an undefined property should raise AttributeError
    with pytest.raises(AttributeError, match=f"does not support attribute {prop_name}"):
        obj.__setattr__(prop_name, prop_value)


# Test 7: Round-trip property for from_dict/to_dict
@given(
    st.dictionaries(
        st.sampled_from(["ApiKey", "SecretKey"]),
        st.text(min_size=1, max_size=20)
    ).filter(lambda d: "ApiKey" in d and "SecretKey" in d)
)
def test_round_trip_property(properties):
    """Test that from_dict and to_dict are inverses"""
    
    # Use AmplitudeConnectorProfileCredentials as it has simple required string fields
    cls = appflow.AmplitudeConnectorProfileCredentials
    
    # Create object from dict
    obj = cls._from_dict(**properties)
    
    # Convert back to dict
    result = obj.to_dict(validation=True)
    
    # The result should contain all the properties we started with
    for key, value in properties.items():
        assert key in result
        assert result[key] == value


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])