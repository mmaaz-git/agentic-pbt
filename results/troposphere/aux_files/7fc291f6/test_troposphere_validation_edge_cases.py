import sys
import json
from hypothesis import given, strategies as st, assume, settings, example
from hypothesis.strategies import composite
import pytest

sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import iotanalytics, AWSProperty, AWSObject, Tags
from troposphere.validators import integer, double, boolean


@composite
def edge_case_integers(draw):
    """Generate edge case integer values"""
    return draw(st.one_of(
        st.just(0),
        st.just(-1),
        st.just(2**31 - 1),  # Max 32-bit signed int
        st.just(2**31),      # Just over max 32-bit signed int
        st.just(2**63 - 1),  # Max 64-bit signed int
        st.just(-2**31),     # Min 32-bit signed int
        st.just(-2**63),     # Min 64-bit signed int
        st.floats(allow_nan=False, allow_infinity=False).map(lambda x: int(x)),
        st.text(alphabet='0123456789', min_size=1, max_size=20)  # Numeric strings
    ))


@composite
def edge_case_doubles(draw):
    """Generate edge case double values"""
    return draw(st.one_of(
        st.just(0.0),
        st.just(-0.0),
        st.just(1e-308),      # Near minimum positive double
        st.just(1.7976931348623157e+308),  # Near max double
        st.just(-1.7976931348623157e+308), # Near min double
        st.floats(allow_nan=True, allow_infinity=True),
        st.text(alphabet='0123456789.', min_size=1, max_size=20).filter(lambda x: x.count('.') <= 1)
    ))


@composite
def edge_case_booleans(draw):
    """Generate edge case boolean values"""
    return draw(st.one_of(
        st.just(True),
        st.just(False),
        st.just(1),
        st.just(0),
        st.just("true"),
        st.just("false"),
        st.just("True"),
        st.just("False"),
        st.just("1"),
        st.just("0")
    ))


@composite
def invalid_booleans(draw):
    """Generate invalid boolean values that should fail validation"""
    return draw(st.one_of(
        st.just("yes"),
        st.just("no"),
        st.just(2),
        st.just(-1),
        st.just("TRUE"),
        st.just("FALSE"),
        st.just(None),
        st.just([]),
        st.just({}),
        st.text(min_size=2)  # Random text
    ))


@given(value=edge_case_integers())
def test_integer_validator_edge_cases(value):
    """Test integer validator with edge cases"""
    
    retention = iotanalytics.RetentionPeriod()
    
    try:
        # Integer validator should handle various integer representations
        retention.NumberOfDays = value
        
        # If it succeeded, the value should be preserved
        assert retention.NumberOfDays == value
        
        # Should be able to serialize
        serialized = retention.to_dict(validation=False)
        assert "NumberOfDays" in serialized
        
        # The serialized value should be the same as what we set
        assert serialized["NumberOfDays"] == value
    except (ValueError, TypeError) as e:
        # Some values might legitimately fail validation
        # Check if it's a value that should fail
        if isinstance(value, str) and not value.isdigit() and not (value.startswith('-') and value[1:].isdigit()):
            pass  # Expected to fail for non-numeric strings
        else:
            # If it's a valid integer representation, it shouldn't have failed
            try:
                int(value)
                # If int() works, the validator should have accepted it
                pytest.fail(f"Integer validator rejected valid integer: {value}")
            except (ValueError, TypeError):
                pass  # Expected to fail


@given(value=edge_case_doubles())
def test_double_validator_edge_cases(value):
    """Test double validator with edge cases including NaN and Infinity"""
    
    var = iotanalytics.Variable()
    var.VariableName = "TestVar"
    
    try:
        # Double validator should handle various double representations
        var.DoubleValue = value
        
        # If it succeeded, the value should be preserved
        assert var.DoubleValue == value or (
            # NaN is special - it's not equal to itself
            isinstance(value, float) and 
            value != value and 
            var.DoubleValue != var.DoubleValue
        )
        
        # Should be able to serialize
        serialized = var.to_dict(validation=False)
        assert "DoubleValue" in serialized
    except (ValueError, TypeError) as e:
        # Some values might legitimately fail validation
        # Check if it's a value that should fail
        if isinstance(value, str):
            try:
                float(value)
                # If float() works, the validator should have accepted it
                pytest.fail(f"Double validator rejected valid double: {value}")
            except (ValueError, TypeError):
                pass  # Expected to fail for non-numeric strings
        else:
            # Numeric values should generally work
            pass


@given(value=edge_case_booleans())
def test_boolean_validator_edge_cases(value):
    """Test boolean validator with various representations"""
    
    retention = iotanalytics.RetentionPeriod()
    
    # Boolean validator should handle various boolean representations
    retention.Unlimited = value
    
    # Check that the value was properly converted
    assert retention.Unlimited in [True, False]
    
    # Verify the conversion logic
    if value in [True, 1, "1", "true", "True"]:
        assert retention.Unlimited == True
    elif value in [False, 0, "0", "false", "False"]:
        assert retention.Unlimited == False


@given(value=invalid_booleans())
def test_boolean_validator_invalid_values(value):
    """Test that boolean validator rejects invalid values"""
    
    retention = iotanalytics.RetentionPeriod()
    
    with pytest.raises(ValueError):
        retention.Unlimited = value


@given(
    required_field=st.text(min_size=1, max_size=100),
    skip_required=st.booleans()
)
def test_required_property_validation(required_field, skip_required):
    """Test that required properties are properly validated"""
    
    # CustomerManagedS3 has required Bucket and RoleArn fields
    obj = iotanalytics.CustomerManagedS3()
    
    if not skip_required:
        obj.Bucket = required_field
        obj.RoleArn = f"arn:aws:iam::123456789012:role/{required_field}"
        
        # With required fields set, to_dict with validation should work
        try:
            serialized = obj.to_dict(validation=True)
            assert "Bucket" in serialized
            assert "RoleArn" in serialized
        except ValueError:
            pytest.fail("Validation failed even with required fields set")
    else:
        # Without required fields, validation should fail
        with pytest.raises(ValueError, match="required in type"):
            obj.to_dict(validation=True)


@given(
    columns=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=50),
            st.text(min_size=1, max_size=50)
        ),
        min_size=0,
        max_size=10
    )
)
def test_nested_list_property_validation(columns):
    """Test nested list properties with complex structures"""
    
    schema_def = iotanalytics.SchemaDefinition()
    
    column_objs = []
    for name, type_str in columns:
        col = iotanalytics.Column()
        col.Name = name
        col.Type = type_str
        column_objs.append(col)
    
    schema_def.Columns = column_objs
    
    # Serialize
    serialized = schema_def.to_dict(validation=False)
    
    if columns:
        assert "Columns" in serialized
        assert len(serialized["Columns"]) == len(columns)
        
        # Verify each column
        for i, (name, type_str) in enumerate(columns):
            assert serialized["Columns"][i]["Name"] == name
            assert serialized["Columns"][i]["Type"] == type_str
    else:
        # Empty list should either be absent or empty
        assert "Columns" not in serialized or serialized["Columns"] == []


@given(
    activity_type=st.sampled_from([
        "Channel", "Datastore", "AddAttributes", "DeviceRegistryEnrich",
        "DeviceShadowEnrich", "Filter", "Lambda", "Math", 
        "RemoveAttributes", "SelectAttributes"
    ])
)
def test_activity_mutually_exclusive_properties(activity_type):
    """Test that Activity only allows one type of activity at a time"""
    
    activity = iotanalytics.Activity()
    
    # Set one type of activity
    if activity_type == "Channel":
        channel_activity = iotanalytics.ActivityChannel()
        channel_activity.ChannelName = "TestChannel"
        channel_activity.Name = "TestActivity"
        activity.Channel = channel_activity
    elif activity_type == "Datastore":
        datastore_activity = iotanalytics.ActivityDatastore()
        datastore_activity.DatastoreName = "TestDatastore"
        datastore_activity.Name = "TestActivity"
        activity.Datastore = datastore_activity
    elif activity_type == "AddAttributes":
        add_attrs = iotanalytics.AddAttributes()
        add_attrs.Attributes = {"key": "value"}
        add_attrs.Name = "TestActivity"
        activity.AddAttributes = add_attrs
    elif activity_type == "Filter":
        filter_activity = iotanalytics.Filter()
        filter_activity.Filter = "true"
        filter_activity.Name = "TestActivity"
        activity.Filter = filter_activity
    elif activity_type == "Lambda":
        lambda_activity = iotanalytics.Lambda()
        lambda_activity.BatchSize = 10
        lambda_activity.LambdaName = "TestLambda"
        lambda_activity.Name = "TestActivity"
        activity.Lambda = lambda_activity
    elif activity_type == "Math":
        math_activity = iotanalytics.Math()
        math_activity.Attribute = "temperature"
        math_activity.Math = "temperature * 1.8 + 32"
        math_activity.Name = "TestActivity"
        activity.Math = math_activity
    elif activity_type == "RemoveAttributes":
        remove_attrs = iotanalytics.RemoveAttributes()
        remove_attrs.Attributes = ["attr1", "attr2"]
        remove_attrs.Name = "TestActivity"
        activity.RemoveAttributes = remove_attrs
    elif activity_type == "SelectAttributes":
        select_attrs = iotanalytics.SelectAttributes()
        select_attrs.Attributes = ["attr1", "attr2"]
        select_attrs.Name = "TestActivity"
        activity.SelectAttributes = select_attrs
    elif activity_type == "DeviceRegistryEnrich":
        enrich = iotanalytics.DeviceRegistryEnrich()
        enrich.Attribute = "metadata"
        enrich.Name = "TestActivity"
        enrich.RoleArn = "arn:aws:iam::123456789012:role/TestRole"
        enrich.ThingName = "TestThing"
        activity.DeviceRegistryEnrich = enrich
    elif activity_type == "DeviceShadowEnrich":
        enrich = iotanalytics.DeviceShadowEnrich()
        enrich.Attribute = "shadow"
        enrich.Name = "TestActivity"
        enrich.RoleArn = "arn:aws:iam::123456789012:role/TestRole"
        enrich.ThingName = "TestThing"
        activity.DeviceShadowEnrich = enrich
    
    # Serialize and check only one activity type is present
    serialized = activity.to_dict(validation=False)
    
    # Count how many activity types are in the serialized dict
    activity_types = [
        "Channel", "Datastore", "AddAttributes", "DeviceRegistryEnrich",
        "DeviceShadowEnrich", "Filter", "Lambda", "Math",
        "RemoveAttributes", "SelectAttributes"
    ]
    
    present_types = [t for t in activity_types if t in serialized]
    assert len(present_types) == 1
    assert present_types[0] == activity_type


@given(
    timeout=edge_case_integers()
)
def test_delta_time_session_window_timeout_validation(timeout):
    """Test DeltaTimeSessionWindowConfiguration timeout validation"""
    
    config = iotanalytics.DeltaTimeSessionWindowConfiguration()
    
    try:
        config.TimeoutInMinutes = timeout
        
        # If it succeeded, value should be preserved
        assert config.TimeoutInMinutes == timeout
        
        # Should serialize
        serialized = config.to_dict(validation=False)
        assert serialized["TimeoutInMinutes"] == timeout
    except (ValueError, TypeError):
        # Check if this should have failed
        try:
            int(timeout)
            # If int() works but the validator failed, might be a bug
            # unless it's out of reasonable range
            if isinstance(timeout, (int, str)) and -2**31 <= int(timeout) <= 2**31:
                pytest.fail(f"Integer validator rejected valid timeout: {timeout}")
        except (ValueError, TypeError, OverflowError):
            pass  # Expected to fail


@given(
    dict_attrs=st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.text(min_size=1, max_size=100),
        min_size=0,
        max_size=10
    )
)
def test_add_attributes_dict_property(dict_attrs):
    """Test AddAttributes with dictionary property"""
    
    add_attrs = iotanalytics.AddAttributes()
    add_attrs.Name = "TestAddAttributes"
    add_attrs.Attributes = dict_attrs
    
    # Dictionary should be preserved
    assert add_attrs.Attributes == dict_attrs
    
    # Serialize and verify
    serialized = add_attrs.to_dict(validation=False)
    assert serialized["Name"] == "TestAddAttributes"
    assert serialized["Attributes"] == dict_attrs


@given(
    schedule_expr=st.text(min_size=1, max_size=200)
)
def test_schedule_expression(schedule_expr):
    """Test Schedule with various expression strings"""
    
    schedule = iotanalytics.Schedule()
    schedule.ScheduleExpression = schedule_expr
    
    # Expression should be preserved as-is
    assert schedule.ScheduleExpression == schedule_expr
    
    # Serialize
    serialized = schedule.to_dict(validation=False)
    assert serialized["ScheduleExpression"] == schedule_expr


if __name__ == "__main__":
    # Run all tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])